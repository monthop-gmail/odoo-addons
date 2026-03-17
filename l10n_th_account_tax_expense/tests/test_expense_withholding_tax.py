# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.tests import tagged

from odoo.addons.hr_expense.tests.common import TestExpenseCommon


@tagged("-at_install", "post_install")
class TestExpenseWithholdingTax(TestExpenseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner1 = cls.env["res.partner"].create(
            {"name": "Test Vendor WHT"}
        )
        cls.wht_account = cls.env["account.account"].create(
            {
                "code": "X152000",
                "name": "Withholding Tax Account Test",
                "account_type": "liability_current",
                "wht_account": True,
                "reconcile": True,
            }
        )
        cls.wht_1 = cls.env["account.withholding.tax"].create(
            {
                "name": "Withholding Tax 1%",
                "account_id": cls.wht_account.id,
                "amount": 1,
            }
        )

    def test_01_expense_wht(self):
        """Test Expense with Withholding Tax"""
        expenses = self.create_expenses(
            {
                "name": "Expense WHT 1,000",
                "employee_id": self.expense_employee.id,
                "product_id": self.product_a.id,
                "quantity": 1,
                "payment_mode": "own_account",
                "company_id": self.company_data["company"].id,
                "date": "2021-10-11",
                "total_amount_currency": 1000.00,
                "wht_tax_id": self.wht_1.id,
                "bill_partner_id": self.partner1.id,
                "tax_ids": False,
            }
        )
        self.assertTrue(expenses.wht_tax_id)
        expenses.action_submit()
        expenses.action_approve()
        self.post_expenses_with_wizard(expenses)
        self.assertEqual(expenses.state, "posted")
        # Check WHT on move lines
        move = expenses.account_move_id
        self.assertTrue(move.invoice_line_ids.wht_tax_id)

    def test_02_expense_no_wht(self):
        """Test Expense without Withholding Tax"""
        expenses = self.create_expenses(
            {
                "name": "Expense no WHT 1,000",
                "employee_id": self.expense_employee.id,
                "product_id": self.product_a.id,
                "quantity": 1,
                "payment_mode": "own_account",
                "company_id": self.company_data["company"].id,
                "date": "2021-10-11",
                "total_amount_currency": 1000.00,
                "tax_ids": False,
            }
        )
        self.assertFalse(expenses.wht_tax_id)
        expenses.action_submit()
        expenses.action_approve()
        self.post_expenses_with_wizard(expenses)
        self.assertEqual(expenses.state, "posted")
