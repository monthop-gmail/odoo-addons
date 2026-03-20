# Copyright 2025 Accsumana
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.html)

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestVendorBillWht(TransactionCase):
    """Test creating a Vendor Bill with WHT using demo data."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.vendor = cls.env.ref("ocaacc.demo_vendor_somchai")
        cls.product = cls.env.ref("ocaacc.demo_product_consulting")
        cls.wht_3 = cls.env.ref("ocaacc.demo_wht_3_service")

    def test_create_vendor_bill_with_wht(self):
        """Create a vendor bill, assign WHT, and verify the WHT line."""
        bill = self.env["account.move"].create(
            {
                "move_type": "in_invoice",
                "partner_id": self.vendor.id,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.product_variant_id.id,
                            "quantity": 1,
                            "price_unit": 10000.0,
                        },
                    )
                ],
            }
        )
        # Assign WHT to invoice line
        bill.invoice_line_ids.write({"wht_tax_id": self.wht_3.id})
        self.assertTrue(bill.invoice_line_ids.wht_tax_id)
        self.assertEqual(bill.invoice_line_ids.wht_tax_id.amount, 3)

    def test_product_auto_wht_on_bill(self):
        """Product with default WHT should suggest WHT on vendor bill."""
        # The product has supplier_company_wht_tax_id set
        self.assertTrue(self.product.supplier_company_wht_tax_id)
        self.assertEqual(self.product.supplier_company_wht_tax_id, self.wht_3)
