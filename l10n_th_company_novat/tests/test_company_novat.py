# Copyright 2021 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestCompanyNoVat(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner_1 = cls.env["res.partner"].create({"name": "Test Vendor NoVAT"})
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

    def _create_invoice(self, partner_id, invoice_type, price_unit, tax=False):
        invoice_dict = {
            "partner_id": partner_id,
            "move_type": invoice_type,
            "invoice_line_ids": [
                (
                    0, 0,
                    {
                        "quantity": 1.0,
                        "name": "Test line",
                        "price_unit": price_unit or 0.0,
                    },
                )
            ],
        }
        if tax:
            invoice_dict["invoice_line_ids"][0][2]["tax_ids"] = [(4, tax.id)]
        return self.env["account.move"].create(invoice_dict)

    def test_01_company_novat_block_tax(self):
        """If company novat=True, document can't select taxes"""
        self.env.company.novat = True
        tax = self.env["account.tax"].search(
            [("company_id", "=", self.env.company.id)], limit=1
        )
        if not tax:
            return
        # Create invoice with Tax should raise
        with self.assertRaises(UserError):
            self._create_invoice(
                self.partner_1.id, "in_invoice", 100.0, tax=tax
            )
        # Create invoice without tax, then write tax should also raise
        invoice = self._create_invoice(
            self.partner_1.id, "in_invoice", 100.0
        )
        with self.assertRaises(UserError):
            invoice.invoice_line_ids.write({"tax_ids": [(4, tax.id)]})

    def test_02_company_novat_vendor_novat(self):
        """Company No-VAT, and Vendor No-VAT -> WHT based on full amount"""
        self.env.company.novat = True
        self.partner_1.novat = True
        invoice = self._create_invoice(
            self.partner_1.id, "in_invoice", 107.0
        )
        invoice.invoice_line_ids.write({"wht_tax_id": self.wht_1.id})
        # Partner No-VAT, no wtvat adjustment
        wtvat = invoice.invoice_line_ids[:1].wtvat
        self.assertEqual(wtvat, 0)

    def test_03_company_novat_vendor_vat(self):
        """Company No-VAT, but vendor VAT -> wtvat should be set"""
        self.env.company.novat = True
        self.partner_1.novat = False
        # Ensure purchase tax exists
        purchase_tax = self.env["account.tax"].search(
            [
                ("type_tax_use", "=", "purchase"),
                ("company_id", "=", self.env.company.id),
            ],
            limit=1,
        )
        if purchase_tax:
            self.env.company.account_purchase_tax_id = purchase_tax
            self.env.company.account_purchase_tax_id.amount = 7
        invoice = self._create_invoice(
            self.partner_1.id, "in_invoice", 107.0
        )
        invoice.invoice_line_ids.write({"wht_tax_id": self.wht_1.id})
        # Partner VAT, wtvat should be the purchase tax %
        wtvat = invoice.invoice_line_ids[:1].wtvat
        if purchase_tax:
            self.assertEqual(wtvat, 7)
