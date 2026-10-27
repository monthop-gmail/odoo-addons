"""Opaque incident metadata; no transport, provider integration or external FK."""
import re
from odoo import api, fields, models
from odoo.exceptions import AccessError, MissingError, UserError
from odoo.fields import Domain
from odoo.tools.safe_eval import safe_eval
from .authority import approver, audit


def restriction_domain(env, model_name, operation):
    """AND of the group-less ir.access rows (restrictions) for the current user.

    19.0 used ir.rule._compute_domain: the rule scope without the ACL grant.
    On 20.0 rules and ACLs are both ir.access; restrictions are the rows with
    no group, so this keeps "rule scope, no native permission".
    """
    from odoo.addons.base.models.ir_access import IN_SELECTION
    access_model = env['ir.access']
    context = None
    domains = []
    for access in access_model._get_all_access().get(model_name, ()):
        if access.group_id or access.operation not in IN_SELECTION[operation]:
            continue
        domain = access.domain
        if not isinstance(domain, Domain):
            context = context or access_model._eval_context()
            domain = Domain(safe_eval(domain, context))
        domains.append(domain)
    return Domain.AND(domains)

REFERENCE=re.compile(r'[A-Za-z0-9][A-Za-z0-9._:-]{0,127}',re.ASCII)


def incident_write(records,values,parent):
    if 'sph_incident_ref' not in values:
        return parent(records).write(values)
    action='incident.reference'
    approver(records,action)
    try:
        if records._name=='purchase.order':
            # SPH approvers intentionally lack a native Purchase read ACL. Match
            # their bounded approval capability, retaining actual-user rule scope.
            domain=restriction_domain(records.env,records._name,'read')
            allowed=records.sudo().search(domain&Domain([('id','in',records.ids),
                ('company_id','in',records.env.companies.ids)]))
            if len(allowed)!=len(records):raise AccessError('Unavailable')
        else:
            records.check_access('read')
            if len(records.exists())!=len(records):raise MissingError('Unavailable')
    except (AccessError,MissingError):
        audit(records.browse(),action,'deny')
        raise AccessError('Unavailable') from None
    value=values['sph_incident_ref']
    if set(values)!={'sph_incident_ref'}:
        audit(records,action,'deny');raise AccessError('Unavailable')
    if value not in (False,None,'') and (not isinstance(value,str) or not REFERENCE.fullmatch(value)):
        audit(records,action,'deny');raise UserError('Unavailable')
    # Elevate only this validated metadata field, never a bundled business write.
    result=parent(records.sudo()).write({'sph_incident_ref':value or False})
    audit(records,action,'allow')
    return result


def incident_create(records,values_list,parent):
    if any(values.get('sph_incident_ref') for values in values_list):
        if records._name=='purchase.order':records._sph_po_scope(action='incident.reference')
        audit(records,'incident.reference','deny');raise AccessError('Unavailable')
    return parent(records).create(values_list)


class IncidentSale(models.Model):
    _inherit='sale.order'
    sph_incident_ref=fields.Char(string='Incident reference',size=128,copy=False)

    def write(self,values):
        return incident_write(self,values,lambda record:super(IncidentSale,record))

    @api.model_create_multi
    def create(self,values_list):
        return incident_create(self,values_list,lambda record:super(IncidentSale,record))


class IncidentPurchase(models.Model):
    _inherit='purchase.order'
    sph_incident_ref=fields.Char(string='Incident reference',size=128,copy=False)

    def write(self,values):
        return incident_write(self,values,lambda record:super(IncidentPurchase,record))

    @api.model_create_multi
    def create(self,values_list):
        return incident_create(self,values_list,lambda record:super(IncidentPurchase,record))
