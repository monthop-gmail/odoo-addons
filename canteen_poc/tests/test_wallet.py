from odoo.tests import TransactionCase
from odoo.exceptions import ValidationError, UserError


class TestCanteenWallet(TransactionCase):

    def setUp(self):
        super().setUp()
        # Obvious test-only PromptPay number (10 digits as l10n_th requires); never a real account.
        self.env['ir.config_parameter'].sudo().set_str('canteen_poc.promptpay_mobile', '0000000000')

    def _wallet(self):
        partner = self.env['res.partner'].create({'name': 'Employee POC'})
        return self.env['canteen.wallet'].create({'name': 'Employee POC wallet', 'partner_id': partner.id})

    def test_topup_debit_balance(self):
        wallet = self._wallet()
        wallet.action_topup(200, 'cash', 'cashier-001')
        self.assertEqual(wallet.balance, 200.0)
        wallet.action_debit(45.50, 'pos_wallet', 'pos-001')
        self.assertEqual(wallet.balance, 154.50)
        self.assertEqual(len(wallet.txn_ids), 2)

    def test_overspend_fail_closed(self):
        wallet = self._wallet()
        wallet.action_topup(50, 'promptpay_qr', 'topup-1')
        with self.assertRaises(ValidationError):
            wallet.action_debit(999, 'pos_wallet', 'pos-2')
        self.assertEqual(wallet.balance, 50.0)

    def test_topup_rejected_on_pos_channel(self):
        wallet = self._wallet()
        with self.assertRaises(ValidationError):
            wallet.action_topup(100, 'pos_wallet', 'x')

    def test_ledger_append_only(self):
        wallet = self._wallet()
        txn = wallet.action_topup(100, 'cash', 'cashier-1')
        with self.assertRaises(ValidationError):
            txn.amount = 1
        with self.assertRaises(ValidationError):
            txn.unlink()

    def test_nonpositive_amount_refused(self):
        wallet = self._wallet()
        with self.assertRaises(ValidationError):
            wallet.action_topup(0, 'cash', 'zero')

    def test_external_adapter_deterministic_mock(self):
        adapter = self.env['canteen.external.wallet.adapter'].create({})
        first = adapter.authorize(30, 'order-1')
        again = adapter.authorize(30, 'order-1')
        self.assertEqual(first['external_ref'], again['external_ref'])
        self.assertTrue(first['external_ref'].startswith('MOCK-'))
        self.assertEqual(first['provider'], 'mock')
        with self.assertRaises(UserError):
            adapter.authorize(-1, 'x')

    def test_promptpay_qr_payload_official_path(self):
        setup = self.env['canteen.wallet'].ensure_shop_setup()
        wallet = self._wallet()
        payload = wallet.get_promptpay_qr_payload(100, 'topup-qr-1')
        self.assertIn('A000000677010111', payload)  # PromptPay AID
        self.assertIn('5303764', payload)           # THB currency tag
        self.assertTrue(payload.startswith('000201'))
        self.assertEqual(setup['pos_config'].payment_method_ids.mapped('type').count('cash'), 0)
