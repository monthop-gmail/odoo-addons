# Copyright 2021 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from odoo import api, fields, models


class HrExpense(models.Model):
    _name = "hr.expense"
    _inherit = ["hr.expense", "base.company.novat"]
    _tax_field_name = "tax_ids"

    wtvat = fields.Float(
        string="Vat%",
        compute="_compute_wtvat",
        store=True,
        copy=True,
        readonly=False,
        help="Only with No-VAT registered company, set default tax "
        "to calculate base amount used for withholding amount",
    )

    @api.depends("employee_id")
    def _compute_wtvat(self):
        if not self.env.company.novat:
            self.update({"wtvat": False})
            return
        for rec in self:
            partner = rec.employee_id.sudo().work_contact_id
            percent = False
            if partner and not partner.novat:  # VAT partner
                percent = self.env.company.account_purchase_tax_id.amount
            rec.wtvat = percent

    def _prepare_move_lines_vals(self):
        """Pass wtvat to move line"""
        self.ensure_one()
        ml_vals = super()._prepare_move_lines_vals()
        ml_vals["wtvat"] = self.wtvat
        return ml_vals
