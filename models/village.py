from odoo import api, fields, models
from odoo.exceptions import ValidationError


class VillageHouse(models.Model):
    _name = 'village.house'
    _description = 'Village house / unit (Fast POC, synthetic data only)'

    code = fields.Char(required=True, help="Unit code, e.g. A-101.")
    owner_id = fields.Many2one('res.partner', required=True, ondelete='restrict')
    resident_id = fields.Many2one('res.partner', ondelete='restrict', help="Optional tenant/resident (synthetic in POC).")
    monthly_fee = fields.Monetary(currency_field='currency_id', required=True)
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id, required=True)
    active = fields.Boolean(default=True)
    charge_ids = fields.One2many('village.fee.charge', 'house_id')
    issue_ids = fields.One2many('village.issue', 'house_id')

    _code_uniq = models.Constraint(
        'UNIQUE(code)',
        'House code must be unique (POC).',
    )

    fee_outstanding_count = fields.Integer(compute='_compute_dashboard')
    fee_outstanding_amount = fields.Monetary(compute='_compute_dashboard', currency_field='currency_id')
    fee_paid_count = fields.Integer(compute='_compute_dashboard')
    open_issue_count = fields.Integer(compute='_compute_dashboard')
    work_order_count = fields.Integer(compute='_compute_dashboard')

    @api.depends('charge_ids.state', 'charge_ids.amount', 'issue_ids.state')
    def _compute_dashboard(self):
        for house in self:
            outstanding = house.charge_ids.filtered(lambda c: c.state == 'outstanding')
            house.fee_outstanding_count = len(outstanding)
            house.fee_outstanding_amount = sum(outstanding.mapped('amount'))
            house.fee_paid_count = len(house.charge_ids.filtered(lambda c: c.state == 'paid'))
            house.open_issue_count = len(house.issue_ids.filtered(
                lambda i: i.state not in ('work_order_done',)))
            house.work_order_count = len(house.issue_ids.mapped('maintenance_request_id'))

    @api.model
    def ensure_demo_setup(self):
        """Idempotent synthetic demo data (no real resident PII)."""
        env = self.env
        comp = env.company
        comp.currency_id = env.ref('base.THB')

        def partner(name):
            return env['res.partner'].search([('name', '=', name)], limit=1) or env['res.partner'].create({'name': name})

        def house(code):
            found = env['village.house'].search([('code', '=', code)], limit=1)
            return found or env['village.house'].create({
                'code': code, 'owner_id': partner(f'Synthetic Owner {code} (POC)').id,
                'monthly_fee': 800,
            })
        houses = {code: house(code) for code in ('A-101', 'A-102', 'A-103')}
        houses['A-101'].resident_id = partner('Synthetic Resident A-101 (POC)').id
        return houses


class VillageFeeCharge(models.Model):
    _name = 'village.fee.charge'
    _description = 'Common-area fee charge (outstanding/paid — simulated payment, Fast POC)'
    _order = 'period desc, id desc'

    house_id = fields.Many2one('village.house', required=True, index=True, ondelete='cascade')
    period = fields.Char(required=True, help="Billing period, e.g. 2026-01.")
    amount = fields.Monetary(currency_field='currency_id', required=True)
    currency_id = fields.Many2one(related='house_id.currency_id')
    state = fields.Selection([('outstanding', 'Outstanding'), ('paid', 'Paid')], default='outstanding')
    channel = fields.Selection([
        ('mock_confirm', 'Mock confirmation (DEV/SIMULATED — no real payment)'),
        ('account_invoice', 'Customer invoice + payment (real accounting path)'),
    ], default='mock_confirm')
    paid_receipt = fields.Char(readonly=True, copy=False, help="Evidence reference issued on (simulated) payment.")
    invoice_id = fields.Many2one('account.move', readonly=True, copy=False, index=True,
                                 help="Real customer invoice backing this charge (bounded fee->account.move spike).")

    _house_period_uniq = models.Constraint(
        'UNIQUE(house_id, period)',
        'One fee charge per house per period (POC).',
    )
    _amount_positive = models.Constraint(
        'CHECK (amount > 0)',
        'Fee amounts must be positive.',
    )

    def action_issue_invoice(self):
        """Bounded fee->account.move spike (Village G3 follow-up): issue a REAL
        posted customer invoice for this charge. No payment gateway — settlement
        stays simulated. Idempotent guard: one invoice per charge."""
        for charge in self.filtered(lambda c: c.state == 'outstanding' and not c.invoice_id):
            comp = self.env.company
            # Odoo 19+: the chart of accounts is shared — account.account has no company_id
            income = self.env['account.account'].search(
                [('account_type', '=', 'income')], limit=1)
            journal = self.env['account.journal'].search(
                [('type', '=', 'sale'), ('company_id', '=', comp.id)], limit=1)
            if not income or not journal:
                raise ValidationError(self.env._("No income account / sale journal — install a chart first."))
            invoice = self.env['account.move'].create({
                'move_type': 'out_invoice',
                'partner_id': charge.house_id.owner_id.id,
                'journal_id': journal.id,
                'invoice_date': fields.Date.context_today(charge),
                'ref': f'Common fee {charge.house_id.code} {charge.period}',
                'invoice_line_ids': [(0, 0, {
                    'name': f"ค่าส่วนกลาง {charge.house_id.code} เดือน {charge.period} (POC)",
                    'quantity': 1.0, 'price_unit': charge.amount,
                    'account_id': income.id, 'tax_ids': [(6, 0, [])],
                })],
            })
            invoice.action_post()
            charge.write({'invoice_id': invoice.id, 'channel': 'account_invoice'})

    def action_mark_paid(self):
        """Simulated settlement. When a real invoice exists, settle it through the
        standard account.payment.register flow (real accounting evidence); the
        'payment' itself is still DEV/SIMULATED — no gateway is called."""
        import hashlib
        for charge in self.filtered(lambda c: c.state == 'outstanding'):
            digest = hashlib.sha256(f"fee|{charge.house_id.code}|{charge.period}".encode()).hexdigest()[:8].upper()
            vals = {'state': 'paid', 'paid_receipt': f'FEE-{digest}'}
            if charge.invoice_id and charge.invoice_id.payment_state != 'paid':
                comp = self.env.company
                journal = self.env['account.journal'].search(
                    [('type', '=', 'bank'), ('company_id', '=', comp.id)], limit=1)
                wizard = self.env['account.payment.register'].with_context(
                    active_model='account.move', active_ids=[charge.invoice_id.id],
                ).create({'journal_id': journal.id} if journal else {})
                wizard.action_create_payments()
                charge.invalidate_recordset(['invoice_id'])
            charge.write(vals)

    def write(self, vals):
        # Identity fields are immutable; channel/state/receipt track the
        # settlement path and may transition (outstanding -> invoiced -> paid).
        immutable = {'house_id', 'period', 'amount'}
        if immutable & set(vals):
            raise ValidationError(self.env._(
                "Fee charges are append-only (POC): %s cannot change.", ', '.join(sorted(immutable & set(vals)))))
        return super().write(vals)

    def unlink(self):
        raise ValidationError(self.env._("Fee charges are append-only (POC): entries cannot be deleted."))
