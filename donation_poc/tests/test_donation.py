from odoo.tests import TransactionCase
from odoo.exceptions import ValidationError, UserError


class TestDonationPoc(TransactionCase):

    def setUp(self):
        super().setUp()
        # Obvious test-only PromptPay number (10 digits as l10n_th requires); never a real account.
        self.env['ir.config_parameter'].sudo().set_param('donation_poc.promptpay_mobile', '0000000000')

    def _setup(self):
        setup = self.env['impact.point.wallet'].ensure_demo_setup()
        donor = self.env['res.partner'].create({'name': 'Donor POC'})
        wallet = self.env['impact.point.wallet'].ensure_for(donor)
        return setup, donor, wallet

    def _donation(self, donor, campaign, amount):
        return self.env['donation.entry'].create({
            'donor_id': donor.id, 'campaign_id': campaign.id,
            'amount': amount, 'channel': 'mock_confirm',
        })

    def test_donation_receipt_and_point_issuance(self):
        setup, donor, wallet = self._setup()
        donation = self._donation(donor, setup['campaign_kk'], 500)
        donation.action_confirm()
        self.assertEqual(donation.state, 'confirmed')
        self.assertTrue(donation.receipt_ref.startswith('RCP-'))
        self.assertEqual(donation.point_entry_id.points, 50)  # 500 THB x 0.1
        self.assertEqual(wallet.balance, 50)

    def test_earning_rule_floored(self):
        rule = self.env['impact.point.rule'].create({'points_per_thb': 0.1})
        self.assertEqual(rule.compute_points(555), 55)
        self.assertEqual(rule.compute_points(9), 0)

    def test_ledgers_are_separate(self):
        """Structural invariant: money ledger and point ledger are distinct models;
        points carry no monetary field, donations carry no point amount."""
        self.assertNotIn('amount', self.env['impact.point.entry']._fields)
        self.assertNotIn('currency_id', self.env['impact.point.entry']._fields)
        self.assertNotIn('points', self.env['donation.entry']._fields)
        setup, donor, wallet = self._setup()
        donation = self._donation(donor, setup['campaign_bkk'], 100)
        donation.action_confirm()
        self.assertEqual(self.env['donation.entry'].search_count([]), 1)
        donation.point_entry_id.sudo().write({})  # no-op write allowed, immutable fields refused below
        with self.assertRaises(ValidationError):
            donation.point_entry_id.points = 999

    def test_points_are_not_money(self):
        """Converting/exporting points must never create money-ledger entries."""
        setup, donor, wallet = self._setup()
        donation = self._donation(donor, setup['campaign_kk'], 300)
        donation.action_confirm()
        before = self.env['donation.entry'].search_count([])
        wallet.action_request_conversion(15, 'TruePoint-class partner (concept only)', idempotency_key='K1')
        self.assertEqual(self.env['donation.entry'].search_count([]), before)
        self.assertEqual(wallet.balance, 15)

    def test_conversion_idempotency_key(self):
        setup, donor, wallet = self._setup()
        self._donation(donor, setup['campaign_kk'], 300).action_confirm()
        first = wallet.action_request_conversion(20, 'TruePoint-class partner (concept only)', idempotency_key='KEY-1')
        again = wallet.action_request_conversion(20, 'TruePoint-class partner (concept only)', idempotency_key='KEY-1')
        self.assertEqual(first.id, again.id)
        self.assertEqual(first.state, 'success')
        self.assertEqual(wallet.env['impact.point.entry'].search_count([('wallet_id', '=', wallet.id), ('kind', '=', 'redeem_out')]), 1)
        self.assertEqual(wallet.balance, 10)

    def test_conversion_failed_path_leaves_points(self):
        setup, donor, wallet = self._setup()
        self._donation(donor, setup['campaign_kk'], 300).action_confirm()
        conversion = wallet.action_request_conversion(
            25, 'TruePoint-class partner (concept only)',
            idempotency_key='KEY-F', force_outcome='failed')
        self.assertEqual(conversion.state, 'failed')
        self.assertFalse(conversion.entry_id)
        self.assertEqual(wallet.balance, 30)  # points untouched on failure

    def test_point_donation_to_recipient(self):
        setup, donor, wallet = self._setup()
        self._donation(donor, setup['campaign_kk'], 500).action_confirm()
        entry = wallet.action_donate_points(20, setup['campaign_bkk'])
        self.assertEqual(entry.kind, 'donate_out')
        self.assertEqual(entry.recipient_campaign_id.id, setup['campaign_bkk'].id)
        self.assertEqual(wallet.balance, 30)
        self.assertEqual(self.env['donation.entry'].search_count([]), 1)

    def test_over_balance_fail_closed(self):
        setup, donor, wallet = self._setup()
        self._donation(donor, setup['campaign_kk'], 100).action_confirm()
        with self.assertRaises(ValidationError):
            wallet.action_donate_points(999, setup['campaign_bkk'])
        with self.assertRaises(ValidationError):
            wallet.action_request_conversion(999, 'TruePoint-class partner (concept only)', idempotency_key='KEY-X')
        self.assertEqual(wallet.balance, 10)

    def test_ledger_append_only(self):
        setup, donor, wallet = self._setup()
        donation = self._donation(donor, setup['campaign_kk'], 100)
        with self.assertRaises(ValidationError):
            donation.amount = 1
        donation.action_confirm()
        entry = donation.point_entry_id
        with self.assertRaises(ValidationError):
            entry.points = 1
        with self.assertRaises(ValidationError):
            entry.unlink()
        with self.assertRaises(ValidationError):
            donation.unlink()

    def test_promptpay_qr_payload_official_path(self):
        setup, donor, wallet = self._setup()
        donation = self._donation(donor, setup['campaign_kk'], 500)
        payload = donation.get_promptpay_qr_payload()
        self.assertTrue(payload.startswith('000201'))
        self.assertIn('A000000677010111', payload)
        self.assertIn('5303764', payload)
        self.assertTrue(payload[-8:-4] == '6304')

    def test_mock_adapter_deterministic_and_labelled(self):
        adapter = self.env['impact.point.adapter'].create({})
        first = adapter.simulate(25, 'KEY-1')
        again = adapter.simulate(25, 'KEY-1')
        self.assertEqual(first, again)
        self.assertEqual(first['provider'] if 'provider' in first else 'mock', 'mock')
        self.assertTrue(first['external_ref'].startswith('MOCK-'))
        failed = adapter.simulate(25, 'KEY-2', force_outcome='failed')
        self.assertEqual(failed['outcome'], 'failed')
        self.assertFalse(failed['external_ref'])
