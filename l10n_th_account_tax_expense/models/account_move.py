# Copyright 2020 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import _, models
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = "account.move"

    def _post(self, soft=True):
        self._assign_expense_tax_invoice()
        return super()._post(soft)

    def _assign_expense_tax_invoice(self):
        """Use tax_number and tax_date from Expense Line as Tax Invoice"""
        for move in self:
            for tax_invoice in move.tax_invoice_ids.filtered(
                lambda l: l.tax_line_id.type_tax_use == "purchase"
            ):
                expense = tax_invoice.move_line_id.expense_id
                if not expense:
                    continue
                if not (expense.tax_number and expense.tax_date):
                    raise UserError(
                        _("Please fill in tax invoice and tax date")
                    )
                vals = {
                    "tax_invoice_number": expense.tax_number,
                    "tax_invoice_date": expense.tax_date,
                }
                if expense.bill_partner_id:
                    vals["partner_id"] = expense.bill_partner_id.id
                tax_invoice.write(vals)


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def _get_tax_base_amount(self, sign, vals_list):
        """Case expense multi line, tax base amount should compute each line"""
        tax_base_amount = super()._get_tax_base_amount(sign, vals_list)
        taxes_list = list(
            filter(lambda x: x.get("tax_repartition_line_id"), vals_list)
        )
        for vals in taxes_list:
            if vals["move_id"] == self.move_id.id:
                line_ids = self.move_id.tax_cash_basis_origin_move_id.line_ids
                move_line_tax_amount = line_ids.filtered(
                    lambda line: line.tax_base_amount
                    and line.amount_currency == self.amount_currency
                )
                if move_line_tax_amount:
                    tax_base_amount = move_line_tax_amount[0].tax_base_amount
        return tax_base_amount

    def _get_partner_wht_lines(self, wht_tax_lines, partner_id):
        if wht_tax_lines.filtered("expense_id"):
            partner_wht_lines = wht_tax_lines.filtered(
                lambda line: line.expense_id.bill_partner_id.id == partner_id
                or (
                    not line.expense_id.bill_partner_id
                    and line.partner_id.id == partner_id
                )
            )
            return partner_wht_lines
        return super()._get_partner_wht_lines(wht_tax_lines, partner_id)

    def _get_partner_wht(self, wht_tax_lines):
        if wht_tax_lines.filtered("expense_id"):
            partner_expense = wht_tax_lines.mapped(
                "expense_id.bill_partner_id"
            ).ids
            return partner_expense
        return super()._get_partner_wht(wht_tax_lines)
