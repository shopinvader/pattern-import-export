# Copyright 2020 Akretion France (http://www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import io

import unicodecsv as csv

from odoo import api, fields, models


class IrExportsSelectTab(models.Model):
    _name = "ir.exports.select.tab"
    _description = "Exports Select Tab"
    _inherit = "ir.exports"

    pattern_file = fields.Binary(string="Pattern file", readonly=True)
    pattern_last_generation_date = fields.Datetime(
        string="Pattern last generation date", readonly=True
    )
    name = fields.Char(string="Name")
    domain = fields.Char(string="Domain")
    fields = fields.One2many(
        "ir.exports.line", "select_tab_id", string="Export Select Tab ID", copy=True
    )

    @api.multi
    def generate_pattern(self):
        # Allows you to generate an excel or csv file to be used as
        # a template for the import.
        pattern_file = io.BytesIO()
        writer = csv.writer(pattern_file, delimiter=";")
        for export_line in self.fields:
            writer.writerow(export_line.name)
        self.pattern_file = base64.encodestring(pattern_file.getvalue())
        self.pattern_last_generation_date = fields.Datetime.now()
        return True
