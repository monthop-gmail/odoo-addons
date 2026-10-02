from odoo import fields, models


class DonationCampaign(models.Model):
    _name = 'donation.campaign'
    _description = 'Nationwide recipient / campaign registry (Fast POC)'

    name = fields.Char(required=True)
    recipient_name = fields.Char(required=True, help="Hospital / charity / organisation receiving support (concept POC).")
    category = fields.Selection([
        ('hospital', 'Hospital'),
        ('charity', 'Charity'),
        ('foundation', 'Foundation'),
        ('org', 'Organisation'),
    ], required=True, default='charity')
    province_id = fields.Many2one('res.country.state', domain="[('country_id.code', '=', 'TH')]")
    active = fields.Boolean(default=True)
    donation_ids = fields.One2many('donation.entry', 'campaign_id')
    point_support_ids = fields.One2many('impact.point.entry', 'recipient_campaign_id')
