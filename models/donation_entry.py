import hashlib

from odoo import api, fields, models
from odoo.exceptions import ValidationError, UserError


class ImpactPointRule(models.Model):
    _name = 'impact.point.rule'
    _description = 'Configurable point earning rule (Fast POC)'

    name = fields.Char(default='Default earning rule (POC)', required=True)
    points_per_thb = fields.Float(default=0.1, help="Impact points earned per donated THB (floored).", required=True)
    active = fields.Boolean(default=True)

    @api.model
    def get_active(self):
        rule = self.search([('active', '=', True)], limit=1)
        return rule or self.create({})

    def compute_points(self, amount_thb):
        self.ensure_one()
        return int(amount_thb * self.points_per_thb // 1)


class DonationEntry(models.Model):
    _name = 'donation.entry'
    _description = 'Donation money ledger entry (append-only, simulated payment — Fast POC)'
    _order = 'id desc'

    donor_id = fields.Many2one('res.partner', required=True, index=True, ondelete='restrict')
    campaign_id = fields.Many2one('donation.campaign', required=True, index=True, ondelete='restrict')
    amount = fields.Monetary(required=True)
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id, required=True)
    channel = fields.Selection([
        ('promptpay_qr', 'PromptPay QR (official path)'),
        ('mock_confirm', 'Mock confirmation (DEV/SIMULATED)'),
    ], required=True, default='promptpay_qr')
    state = fields.Selection([('draft', 'Draft'), ('confirmed', 'Confirmed (simulated payment)')], default='draft')
    receipt_ref = fields.Char(readonly=True, help="Donation receipt / evidence reference issued on confirmation.")
    point_entry_id = fields.Many2one('impact.point.entry', readonly=True, help="Impact points issued for this donation.")

    _amount_positive = models.Constraint(
        'CHECK (amount > 0)',
        'Donation amounts must be positive.',
    )

    def get_promptpay_qr_payload(self):
        """Official l10n_th PromptPay EMV payload for this donation (THB, fail-closed)."""
        self.ensure_one()
        bank = self.env['res.partner.bank'].search([
            ('partner_id', '=', self.env.company.partner_id.id),
            ('proxy_type', 'in', ['mobile', 'merchant_tax_id', 'ewallet_id']),
        ], limit=1)
        if not bank:
            raise UserError(self.env._("No company PromptPay proxy account — run the donation demo setup first."))
        payload = bank.build_qr_code_value(
            self.amount, self.campaign_id.name, '', self.currency_id, False,
            qr_method='emv_qr', silent_errors=False)
        if not payload:
            raise UserError(self.env._("PromptPay QR generation returned no payload."))
        return payload

    def action_confirm(self):
        """Simulated payment confirmation (DEV/SIMULATED — no real payment) then point issuance."""
        for donation in self.filtered(lambda d: d.state == 'draft'):
            digest = hashlib.sha256(f"donation|{donation.id}|{donation.amount:.2f}".encode()).hexdigest()[:8].upper()
            receipt = f"RCP-{digest}"
            wallet = self.env['impact.point.wallet'].ensure_for(donation.donor_id)
            points = self.env['impact.point.rule'].get_active().compute_points(donation.amount)
            donation.write({
                'state': 'confirmed',
                'receipt_ref': receipt,
            })
            if points > 0:
                entry = self.env['impact.point.entry'].create({
                    'wallet_id': wallet.id, 'kind': 'award', 'points': points,
                    'ref': receipt, 'source_donation_id': donation.id,
                })
                donation.point_entry_id = entry
        return True

    def write(self, vals):
        # Identity fields are immutable; receipt_ref/point_entry_id are readonly and
        # issued only by action_confirm.
        immutable = {'donor_id', 'campaign_id', 'amount', 'currency_id', 'channel'}
        if immutable & set(vals):
            raise ValidationError(self.env._(
                "Donation ledger is append-only (POC): %s cannot change.", ', '.join(sorted(immutable & set(vals)))))
        return super().write(vals)

    def unlink(self):
        raise ValidationError(self.env._("Donation ledger is append-only (POC): entries cannot be deleted."))
