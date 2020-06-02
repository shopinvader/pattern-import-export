# Copyright 2020 Akretion France (http://www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import ast

from odoo import api, fields, models


class IrExportsSelectTab(models.Model):
    _name = "ir.exports.select.tab"
    _description = "Exports Select Tab"

    name = fields.Char(string="Name", required=True)
    domain = fields.Char(string="Domain")
    model_id = fields.Many2one("ir.model", string="Model", required=True, readonly=True)
    field_id = fields.Many2one("ir.model.fields", string="Field", required=True)

    @api.multi
    def _generate_additional_sheet(self, book, bold):
        for select_tab in self:
            field = select_tab.field_id.name
            model = select_tab.model_id.model
            domain = select_tab.domain
            sheet_name = select_tab.name + " (" + field + ")"
            sheet = book.add_worksheet(sheet_name)
            sheet.write(0, 0, field, bold)
            row = 1
            for record in self.env[model].read_group(
                ast.literal_eval(domain), [field], [field], orderby=field
            ):
                sheet.write(row, 0, record[field])
                row += 1
        return sheet, row
