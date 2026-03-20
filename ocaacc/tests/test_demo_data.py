# Copyright 2025 Accsumana
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.html)

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestOcaaccDemoData(TransactionCase):
    """Test that ocaacc demo data is loaded correctly."""

    def test_demo_vendors_exist(self):
        """Thai vendor partners should exist with correct tax IDs."""
        vendor1 = self.env.ref("ocaacc.demo_vendor_somchai")
        self.assertEqual(vendor1.vat, "0105560123456")
        self.assertTrue(vendor1.supplier_rank > 0)
        self.assertTrue(vendor1.is_company)

        vendor2 = self.env.ref("ocaacc.demo_vendor_rungrueang")
        self.assertEqual(vendor2.vat, "0103560789012")
        self.assertTrue(vendor2.is_company)

        vendor3 = self.env.ref("ocaacc.demo_vendor_wichai")
        self.assertEqual(vendor3.vat, "1234567890123")
        self.assertFalse(vendor3.is_company)

    def test_demo_customer_exists(self):
        """Thai customer partner should exist."""
        customer = self.env.ref("ocaacc.demo_customer_thai")
        self.assertEqual(customer.vat, "0107550345678")
        self.assertTrue(customer.customer_rank > 0)

    def test_demo_wht_account(self):
        """WHT account should exist and be marked as wht_account."""
        account = self.env.ref("ocaacc.demo_wht_account")
        self.assertEqual(account.code, "215300")
        self.assertTrue(account.wht_account)
        self.assertTrue(account.reconcile)
        self.assertEqual(account.account_type, "liability_current")

    def test_demo_wht_rates(self):
        """All WHT rates should exist with correct percentages."""
        wht_1 = self.env.ref("ocaacc.demo_wht_1_transport")
        self.assertEqual(wht_1.amount, 1)
        self.assertEqual(wht_1.income_tax_form, "pnd53")

        wht_2 = self.env.ref("ocaacc.demo_wht_2_advertising")
        self.assertEqual(wht_2.amount, 2)

        wht_3 = self.env.ref("ocaacc.demo_wht_3_service")
        self.assertEqual(wht_3.amount, 3)
        self.assertEqual(wht_3.income_tax_form, "pnd53")

        wht_3_pnd3 = self.env.ref("ocaacc.demo_wht_3_service_pnd3")
        self.assertEqual(wht_3_pnd3.amount, 3)
        self.assertEqual(wht_3_pnd3.income_tax_form, "pnd3")

        wht_5 = self.env.ref("ocaacc.demo_wht_5_rent")
        self.assertEqual(wht_5.amount, 5)

        pit = self.env.ref("ocaacc.demo_wht_pit")
        self.assertTrue(pit.is_pit)
        self.assertEqual(pit.income_tax_form, "pnd1")

    def test_demo_products_wht_defaults(self):
        """Products should have correct default WHT tax assigned."""
        consulting = self.env.ref("ocaacc.demo_product_consulting")
        self.assertEqual(consulting.type, "service")
        self.assertEqual(
            consulting.supplier_company_wht_tax_id,
            self.env.ref("ocaacc.demo_wht_3_service"),
        )
        self.assertEqual(
            consulting.supplier_wht_tax_id,
            self.env.ref("ocaacc.demo_wht_3_service_pnd3"),
        )

        rent = self.env.ref("ocaacc.demo_product_rent")
        self.assertEqual(
            rent.supplier_company_wht_tax_id,
            self.env.ref("ocaacc.demo_wht_5_rent"),
        )

        transport = self.env.ref("ocaacc.demo_product_transport")
        self.assertEqual(
            transport.supplier_company_wht_tax_id,
            self.env.ref("ocaacc.demo_wht_1_transport"),
        )
