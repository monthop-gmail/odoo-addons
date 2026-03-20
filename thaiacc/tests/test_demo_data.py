# Copyright 2025 Accsumana
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.html)

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestThaiaccDemoData(TransactionCase):
    """Test that thaiacc demo data is loaded correctly."""

    def test_demo_vendor_novat(self):
        """NOVAT vendor should exist with novat=True."""
        vendor = self.env.ref("thaiacc.demo_vendor_novat")
        self.assertEqual(vendor.vat, "0993560456789")
        self.assertTrue(vendor.supplier_rank > 0)
        self.assertTrue(vendor.novat)

    def test_demo_expense_products(self):
        """Expense products should exist with can_be_expensed and WHT."""
        repair = self.env.ref("thaiacc.demo_product_repair")
        self.assertEqual(repair.type, "service")
        self.assertTrue(repair.can_be_expensed)
        self.assertEqual(
            repair.supplier_company_wht_tax_id,
            self.env.ref("ocaacc.demo_wht_3_service"),
        )
        self.assertEqual(
            repair.supplier_wht_tax_id,
            self.env.ref("ocaacc.demo_wht_3_service_pnd3"),
        )

        delivery = self.env.ref("thaiacc.demo_product_delivery")
        self.assertTrue(delivery.can_be_expensed)
        self.assertEqual(
            delivery.supplier_company_wht_tax_id,
            self.env.ref("ocaacc.demo_wht_1_transport"),
        )

    def test_ocaacc_demo_inherited(self):
        """thaiacc should also have access to ocaacc demo data."""
        # WHT rates from ocaacc should be accessible
        wht_3 = self.env.ref("ocaacc.demo_wht_3_service")
        self.assertTrue(wht_3)
        self.assertEqual(wht_3.amount, 3)

        # WHT account from ocaacc
        account = self.env.ref("ocaacc.demo_wht_account")
        self.assertTrue(account.wht_account)
