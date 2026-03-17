# Copyright 2020 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import Command
from odoo.exceptions import UserError
from odoo.tests import tagged

from odoo.addons.hr_expense.tests.common import TestExpenseCommon


@tagged("-at_install", "post_install")
class TestExpenseTaxInvoice(TestExpenseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner1 = cls.env["res.partner"].create({"name": "Test Vendor"})

    def test_expense_tax_invoice(self):
        """hr.expense's tax_number & tax_date is used as Tax Invoice and Date.
        If not filled, do not allow posting.
        """
        expenses = self.create_expenses(
            {
                "name": "Expense with Tax Invoice",
                "employee_id": self.expense_employee.id,
                "account_id": self.expense_account.id,
                "product_id": self.product_a.id,
                "quantity": 1,
                "payment_mode": "own_account",
                "company_id": self.company_data["company"].id,
                "date": "2021-10-11",
                "total_amount_currency": 1000.00,
                "tax_ids": [Command.set(self.tax_purchase_a.ids)],
            }
        )
        expenses.action_submit()
        expenses.action_approve()
        # Posting without tax_number/tax_date should fail
        with self.assertRaises(
            UserError, msg="Please fill in tax invoice and tax date"
        ):
            self.post_expenses_with_wizard(expenses)
        # Fill in tax invoice details
        expenses.write(
            {
                "tax_number": "TAXINV-001",
                "tax_date": "2021-10-11",
                "bill_partner_id": self.partner1.id,
            }
        )
        self.post_expenses_with_wizard(expenses)
        self.assertEqual(expenses.state, "posted")
