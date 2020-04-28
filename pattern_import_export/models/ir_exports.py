# Copyright 2020 Akretion France (http://www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
from io import BytesIO

import xlsxwriter

from odoo import api, fields, models


class IrExports(models.Model):
    _inherit = "ir.exports"

    pattern_file = fields.Binary(string="Pattern file", readonly=True)
    pattern_last_generation_date = fields.Datetime(
        string="Pattern last generation date", readonly=True
    )

    @api.multi
    def generate_pattern(self):
        # Allows you to generate an excel or csv file to be used as
        # a template for the import.
        pattern_file = BytesIO()
        book = xlsxwriter.Workbook(pattern_file)
        sheet1 = book.add_worksheet()
        bold = book.add_format({"bold": True})
        row = 0
        col = 0
        for export_line in self.export_fields:
            sheet1.write(row, col, export_line.name, bold)
            col += 1
        book.close()
        self.pattern_file = base64.b64encode(pattern_file.getvalue())
        self.pattern_last_generation_date = fields.Datetime.now()
        return True


class IrExportsLine(models.Model):
    _inherit = "ir.exports.line"

    select_tab_id = fields.Many2one("ir.exports.select.tab", string="Select tab")
    split_nbr = fields.Integer(string="Split nbr")
