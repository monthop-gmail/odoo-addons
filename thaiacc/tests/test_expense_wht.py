# Copyright 2025 Accsumana
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.html)

from odoo.tests import tagged

from odoo.addons.hr_expense.tests.common import TestExpenseCommon


@tagged("post_install", "-at_install")
class TestExpenseWht(TestExpenseCommon):
    """Test creating an Expense with WHT using thaiacc demo data."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.vendor = cls.env["res.partner"].create(
            {"name": "Test Vendor Expense WHT"}
        )
        # Create WHT in the test company (TestExpenseCommon uses its own company)
        cls.wht_account = cls.env["account.account"].create(
            {
                "code": "X215300",
                "name": "WHT Account Test",
                "account_type": "liability_current",
                "wht_account": True,
                "reconcile": True,
            }
        )
        cls.wht_3 = cls.env["account.withholding.tax"].create(
            {
                "name": "WHT 3% Test",
                "account_id": cls.wht_account.id,
                "amount": 3,
                "company_id": cls.company_data["company"].id,
            }
        )
        cls.product_repair = cls.env.ref("thaiacc.demo_product_repair")

    def test_create_expense_with_wht(self):
        """Create an expense with WHT and verify it posts correctly."""
        expenses = self.create_expenses(
            {
                "name": "ค่าซ่อมเครื่องปรับอากาศ",
                "employee_id": self.expense_employee.id,
                "product_id": self.product_repair.product_variant_id.id,
                "quantity": 1,
                "payment_mode": "own_account",
                "company_id": self.company_data["company"].id,
                "total_amount_currency": 8000.00,
                "wht_tax_id": self.wht_3.id,
                "bill_partner_id": self.vendor.id,
                "tax_ids": False,
            }
        )
        self.assertTrue(expenses.wht_tax_id)
        self.assertEqual(expenses.wht_tax_id.amount, 3)

        # Submit and approve
        expenses.action_submit()
        expenses.action_approve()
        self.post_expenses_with_wizard(expenses)
        self.assertEqual(expenses.state, "posted")

        # Verify WHT on journal entry
        move = expenses.account_move_id
        self.assertTrue(move.invoice_line_ids.wht_tax_id)

    def test_expense_product_can_be_expensed(self):
        """Demo expense products should have can_be_expensed flag."""
        self.assertTrue(self.product_repair.can_be_expensed)
