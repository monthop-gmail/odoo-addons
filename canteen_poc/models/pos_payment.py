from odoo import api, fields, models
from odoo.exceptions import ValidationError


class PosPaymentMethod(models.Model):
    _inherit = 'pos.payment.method'

    canteen_debit_wallet = fields.Boolean(
        "Debit canteen wallet (POC)",
        help="Payments made with this method debit the customer's canteen wallet (Fast POC).")


class PosPayment(models.Model):
    _inherit = 'pos.payment'

    canteen_wallet_txn_id = fields.Many2one('canteen.wallet.txn', readonly=True, index=True)

    @api.model_create_multi
    def create(self, vals_list):
        payments = super().create(vals_list)
        for payment in payments:
            method = payment.payment_method_id
            if method.canteen_debit_wallet and payment.pos_order_id.partner_id:
                wallet = self.env['canteen.wallet'].search([
                    ('partner_id', '=', payment.pos_order_id.partner_id.id)], limit=1)
                if not wallet:
                    raise ValidationError(self.env._(
                        "Partner %(partner)s has no canteen wallet — payment refused (fail-closed).",
                        partner=payment.pos_order_id.partner_id.display_name))
                payment.canteen_wallet_txn_id = wallet.action_debit(
                    payment.amount, 'pos_wallet',
                    ref=payment.pos_order_id.pos_reference or payment.pos_order_id.name,
                    pos_payment=payment)
        return payments
