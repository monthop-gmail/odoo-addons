from odoo.tests import TransactionCase
from odoo.exceptions import ValidationError, UserError


class TestVillagePoc(TransactionCase):

    def _setup(self):
        houses = self.env['village.house'].ensure_demo_setup()
        return houses['A-101']

    def _issue(self, house, title='ไฟถนนหน้าบ้านดับ'):
        return self.env['village.issue'].create({
            'house_id': house.id,
            'title': title,
            # Odoo 20 note: raw create() does not convert recordsets for m2o — pass .id
            'reported_by': (house.resident_id or house.owner_id).id,
        })

    def test_fee_outstanding_paid_state(self):
        house = self._setup()
        charges = self.env['village.fee.charge'].create([{
            'house_id': house.id, 'period': f'2026-{m:02d}', 'amount': 800,
        } for m in (1, 2, 3)])
        self.assertEqual(house.fee_outstanding_count, 3)
        self.assertEqual(house.fee_outstanding_amount, 2400)
        charges[0].action_mark_paid()
        self.assertEqual(charges[0].state, 'paid')
        self.assertTrue(charges[0].paid_receipt.startswith('FEE-'))
        self.assertEqual(house.fee_outstanding_count, 2)
        with self.assertRaises(ValidationError):  # append-only
            charges[0].period = '2026-99'

    def test_fee_unique_house_period(self):
        house = self._setup()
        self.env['village.fee.charge'].create({'house_id': house.id, 'period': '2026-01', 'amount': 800})
        with self.assertRaises(Exception):
            self.env['village.fee.charge'].create({'house_id': house.id, 'period': '2026-01', 'amount': 800})

    def test_ai_classification_deterministic(self):
        house = self._setup()
        advisory = self.env['village.ai.advisory'].generate_for_issue(self._issue(house, 'ไฟถนนหน้าบ้านดับ'))
        self.assertEqual(advisory.category, 'lighting')
        self.assertEqual(advisory.priority, 'high')
        self.assertIn('ADVISORY ONLY', advisory.summary)
        advisory2 = self.env['village.ai.advisory'].generate_for_issue(self._issue(house, 'ท่อน้ำรั่วหน้าหมู่บ้าน'))
        self.assertEqual(advisory2.category, 'plumbing')
        advisory3 = self.env['village.ai.advisory'].generate_for_issue(self._issue(house, 'ขอความร่วมมือทั่วไป'))
        self.assertEqual(advisory3.category, 'other')

    def test_advisory_never_approves_itself(self):
        """Structural human-control invariant: generating advisory does not approve or
        create any consequential work order."""
        house = self._setup()
        issue = self._issue(house)
        advisory = self.env['village.ai.advisory'].generate_for_issue(issue)
        self.assertEqual(advisory.state, 'draft')
        self.assertEqual(issue.state, 'reported')
        self.assertFalse(issue.maintenance_request_id)
        with self.assertRaises(UserError):
            advisory.approve()  # mock engine cannot self-approve

    def test_human_approval_creates_work_order(self):
        house = self._setup()
        issue = self._issue(house)
        advisory = self.env['village.ai.advisory'].generate_for_issue(issue)
        advisory.action_approve()
        self.assertEqual(advisory.state, 'approved')
        self.assertEqual(advisory.approved_by.id, self.env.user.id)
        self.assertTrue(advisory.maintenance_request_id)
        self.assertEqual(issue.maintenance_request_id.id, advisory.maintenance_request_id.id)
        self.assertEqual(issue.state, 'approved')
        with self.assertRaises(UserError):  # mock engine path blocked
            advisory.approve()
        with self.assertRaises(ValidationError):  # approved advisories frozen
            advisory.summary = 'tamper'

    def test_work_order_progression_sets_close_date(self):
        house = self._setup()
        issue = self._issue(house)
        advisory = self.env['village.ai.advisory'].generate_for_issue(issue)
        advisory.action_approve()
        request = advisory.maintenance_request_id
        stages = self.env['maintenance.stage'].search([], order='sequence')
        request.write({'stage_id': stages[-1].id, 'state': 'done'})
        self.assertEqual(request.state, 'done')
        self.assertTrue(request.close_date)
        self.assertEqual(issue.state, 'approved')

    def test_rejected_advisory_creates_no_work_order(self):
        house = self._setup()
        issue = self._issue(house)
        advisory = self.env['village.ai.advisory'].generate_for_issue(issue)
        advisory.action_reject()
        self.assertEqual(advisory.state, 'rejected')
        self.assertFalse(advisory.maintenance_request_id)
        self.assertEqual(self.env['maintenance.request'].search_count([]), 0)

    def test_dashboard_fields(self):
        house = self._setup()
        self.env['village.fee.charge'].create({'house_id': house.id, 'period': '2026-02', 'amount': 800})
        issue = self._issue(house)
        advisory = self.env['village.ai.advisory'].generate_for_issue(issue)
        advisory.action_approve()
        self.assertEqual(house.open_issue_count, 1)  # not work_order_done yet
        self.assertEqual(house.work_order_count, 1)
        self.assertEqual(house.fee_outstanding_amount, 800)
