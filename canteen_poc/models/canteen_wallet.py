from odoo import api, fields, models
from odoo.exceptions import ValidationError, UserError

CHANNELS = [
    ('cash', 'Cash (top-up point only)'),
    ('promptpay_qr', 'PromptPay QR'),
    ('external_wallet_mock', 'External wallet (MOCK adapter)'),
    ('pos_wallet', 'Shop POS (prepaid wallet)'),
]


class CanteenWallet(models.Model):
    _name = 'canteen.wallet'
    _description = 'Canteen prepaid wallet (Fast POC)'

    name = fields.Char(required=True)
    partner_id = fields.Many2one('res.partner', required=True, index=True, ondelete='restrict')
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id, required=True)
    active = fields.Boolean(default=True)
    txn_ids = fields.One2many('canteen.wallet.txn', 'wallet_id')
    balance = fields.Monetary(compute='_compute_balance', currency_field='currency_id')

    _partner_uniq = models.Constraint(
        'UNIQUE(partner_id)',
        'One wallet per partner (POC).',
    )

    @api.depends('txn_ids.amount', 'txn_ids.kind')
    def _compute_balance(self):
        for wallet in self:
            wallet.balance = sum(wallet.txn_ids.mapped('signed_amount'))

    @api.model
    def _promptpay_bank(self):
        """The company PromptPay proxy account (official l10n_th EMV QR path)."""
        bank = self.env['res.partner.bank'].search([
            ('partner_id', '=', self.env.company.partner_id.id),
            ('proxy_type', 'in', ['mobile', 'merchant_tax_id', 'ewallet_id']),
        ], limit=1)
        return bank

    @api.model
    def ensure_shop_setup(self):
        """Idempotent demo/POC configuration: official-first PromptPay QR + no-cash shop POS.

        Returns dict with bank/journal/qr_pm/wallet_pm/pos_config records.
        All config steps are the ones verified live on 20.0-20260926 (dis-882f5ddd#2).
        """
        env = self.env
        comp = env.company
        th = env['res.country'].search([('code', '=', 'TH')], limit=1)
        if th:
            comp.partner_id.country_id = th
            comp.partner_id.city = comp.partner_id.city or 'Bangkok'
        comp.currency_id = env.ref('base.THB')
        bank = self._promptpay_bank()
        if not bank:
            bank = env['res.partner.bank'].create({
                'partner_id': comp.partner_id.id,
                'account_number': '0812345678',
                'proxy_type': 'mobile',
                'proxy_value': '0812345678',
            })
        journal = env['account.journal'].search([('company_id', '=', comp.id), ('type', '=', 'bank')], limit=1)
        if not journal:
            journal = env['account.journal'].create({'name': 'Canteen Bank (POC)', 'type': 'bank', 'code': 'CNBP', 'company_id': comp.id})
        if not journal.bank_account_id:
            journal.bank_account_id = bank
        journal.currency_id = env.ref('base.THB')

        qr_pm = env['pos.payment.method'].search([('name', '=', 'PromptPay QR (canteen POC)')], limit=1)
        if not qr_pm:
            qr_pm = env['pos.payment.method'].create({
                'name': 'PromptPay QR (canteen POC)',
                'type': 'bank',
                'payment_method_type': 'bank_qr_code',
                'qr_code_method': 'emv_qr',
                'journal_id': journal.id,
                'company_id': comp.id,
            })
        wallet_pm = env['pos.payment.method'].search([('name', '=', 'Prepaid Wallet (canteen POC)')], limit=1)
        if not wallet_pm:
            wallet_vals = {
                'name': 'Prepaid Wallet (canteen POC)',
                'type': 'pay_later',
                'canteen_debit_wallet': True,
                'company_id': comp.id,
            }
            try:
                wallet_pm = env['pos.payment.method'].create(wallet_vals)
            except Exception:  # payment_method_type required on some builds
                wallet_vals['payment_method_type'] = 'pay_later'
                wallet_pm = env['pos.payment.method'].create(wallet_vals)
        shop = env['pos.config'].search([('name', '=', 'Canteen Shop (POC)')], limit=1)
        if not shop:
            shop = env['pos.config'].create({'name': 'Canteen Shop (POC)', 'company_id': comp.id})
        shop.payment_method_ids = [(6, 0, [qr_pm.id, wallet_pm.id])]
        return {'bank': bank, 'journal': journal, 'qr_pm': qr_pm, 'wallet_pm': wallet_pm, 'pos_config': shop}

    def get_promptpay_qr_payload(self, amount, ref=None):
        """Official PromptPay EMV payload for a top-up amount (THB, fail-closed)."""
        self.ensure_one()
        bank = self._promptpay_bank()
        if not bank:
            raise UserError(self.env._("No company PromptPay proxy account configured — run canteen shop setup first."))
        payload = bank.build_qr_code_value(
            amount, ref or self.name, '', self.env.ref('base.THB'), False,
            qr_method='emv_qr', silent_errors=False)
        if not payload:
            raise UserError(self.env._("PromptPay QR generation returned no payload."))
        return payload

    def action_topup(self, amount, channel, ref=None, external_ref=None):
        self.ensure_one()
        if channel == 'pos_wallet':
            raise ValidationError(self.env._("Top-ups cannot use the shop POS channel."))
        return self.env['canteen.wallet.txn'].create({
            'wallet_id': self.id, 'kind': 'topup', 'channel': channel,
            'amount': amount, 'ref': ref, 'external_ref': external_ref,
        })

    def action_debit(self, amount, channel, ref=None, external_ref=None, pos_payment=None):
        self.ensure_one()
        if amount > self.balance:
            raise ValidationError(self.env._(
                "Wallet %(wallet)s: balance %(balance).2f < debit %(amount).2f — refused (fail-closed).",
                wallet=self.name, balance=self.balance, amount=amount))
        return self.env['canteen.wallet.txn'].create({
            'wallet_id': self.id, 'kind': 'debit', 'channel': channel,
            'amount': amount, 'ref': ref, 'external_ref': external_ref,
            'pos_payment_id': pos_payment.id if pos_payment else None,
        })


class CanteenWalletTxn(models.Model):
    _name = 'canteen.wallet.txn'
    _description = 'Canteen wallet ledger entry (append-only, Fast POC)'
    _order = 'id desc'

    wallet_id = fields.Many2one('canteen.wallet', required=True, index=True, ondelete='cascade')
    kind = fields.Selection([('topup', 'Top-up'), ('debit', 'Debit')], required=True)
    channel = fields.Selection(CHANNELS, required=True)
    amount = fields.Monetary(required=True)
    currency_id = fields.Many2one(related='wallet_id.currency_id')
    ref = fields.Char()
    external_ref = fields.Char()
    pos_payment_id = fields.Many2one('pos.payment', index=True, ondelete='set null')
    signed_amount = fields.Float(compute='_compute_signed_amount')

    @api.constrains('amount')
    def _check_amount(self):
        for txn in self:
            if txn.amount <= 0:
                raise ValidationError(self.env._("Ledger amounts must be positive; kind carries the sign."))

    @api.depends('kind', 'amount')
    def _compute_signed_amount(self):
        for txn in self:
            txn.signed_amount = txn.amount if txn.kind == 'topup' else -txn.amount

    def write(self, vals):
        immutable = {'kind', 'channel', 'amount', 'wallet_id'}
        if immutable & set(vals):
            raise ValidationError(self.env._("Wallet ledger is append-only (POC): %s cannot change.", ', '.join(sorted(immutable & set(vals)))))
        return super().write(vals)

    def unlink(self):
        raise ValidationError(self.env._("Wallet ledger is append-only (POC): entries cannot be deleted."))
