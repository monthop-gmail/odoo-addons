# Copyright 2021 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from odoo import api, fields, models


class AccountMoveLine(models.Model):
    _name = "account.move.line"
    _inherit = ["account.move.line", "base.company.novat"]
    _tax_field_name = "tax_ids"

    wtvat = fields.Float(
        string="Vat%",
        compute="_compute_wtvat",
        store=True,
        readonly=False,
        copy=True,
        help="Only with No-VAT registered company, set default tax "
        "to calculate base amount used for withholding amount",
    )

    @api.depends("move_id.partner_id")
    def _compute_wtvat(self):
        if not self.env.company.novat:
            self.update({"wtvat": False})
            return
        for rec in self:
            partner = rec.move_id.partner_id
            percent = False
            if partner and not partner.novat:  # VAT partner
                move_type = rec.move_id.move_type
                if move_type in ("out_invoice", "out_refund"):
                    percent = self.env.company.account_sale_tax_id.amount
                if move_type in ("in_invoice", "in_refund"):
                    percent = self.env.company.account_purchase_tax_id.amount
            rec.wtvat = percent

    def _get_wht_amount(self, currency, wht_date):
        """Use wtvat percent to calculate the base amount for WHT"""
        amount_base, amount_wht = super()._get_wht_amount(currency, wht_date)
        # Adjust base amount when company is novat but partner is VAT
        wht_lines = self.filtered("wht_tax_id")
        if wht_lines and any(line.wtvat for line in wht_lines):
            wtvat = wht_lines[0].wtvat
            if wtvat:
                adjusted_base = amount_base * 100 / (100 + wtvat)
                wht_tax = wht_lines.mapped("wht_tax_id")
                if not wht_tax[0].is_pit:
                    amount_wht = adjusted_base * (wht_tax[0].amount / 100)
                return (adjusted_base, amount_wht)
        return (amount_base, amount_wht)
