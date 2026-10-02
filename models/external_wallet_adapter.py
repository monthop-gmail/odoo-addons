from odoo import fields, models
from odoo.exceptions import UserError


class CanteenExternalWalletAdapter(models.Model):
    _name = 'canteen.external.wallet.adapter'
    _description = 'External wallet adapter (MOCK, deterministic — NOT a real provider)'

    name = fields.Char(default='MOCK TrueMoney-class adapter (POC)')

    def authorize(self, amount, ref=None):
        """Deterministic mock authorization. Clearly NOT a real provider call:
        no network, no credentials, ref derived from inputs only."""
        self.ensure_one()
        if amount <= 0:
            raise UserError(self.env._("Mock adapter authorizes positive amounts only."))
        digest = __import__('hashlib').sha256(
            f"{self.id}|{amount:.2f}|{ref or ''}".encode()).hexdigest()[:8].upper()
        return {'status': 'authorized', 'provider': 'mock', 'external_ref': f"MOCK-{digest}"}
