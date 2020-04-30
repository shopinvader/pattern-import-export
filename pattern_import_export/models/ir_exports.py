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

    def generate_additional_sheet(self):
        # sheet = book.add_worksheet()
        # sheet.write(row, col, export_line.name, bold)
        return True

    @api.multi
    def generate_pattern(self):
        # Allows you to generate an excel file to be used as
        # a template for the import.
        pattern_file = BytesIO()
        book = xlsxwriter.Workbook(pattern_file)
        sheet1 = book.add_worksheet(self.resource)
        bold = book.add_format({"bold": True})
        row1 = 0
        col1 = 0
        for export_line in self.export_fields:
            sheet1.write(row1, col1, export_line.name, bold)
            if export_line.is_many2x:
                self.generate_additional_sheet()
            col1 += 1
        book.close()
        self.pattern_file = base64.b64encode(pattern_file.getvalue())
        self.pattern_last_generation_date = fields.Datetime.now()
        return True


class IrExportsLine(models.Model):
    _inherit = "ir.exports.line"

    select_tab_id = fields.Many2one("ir.exports.select.tab", string="Select tab")
    split_nbr = fields.Integer(string="Split nbr")
    is_many2x = fields.Boolean(
        string="Is Many2x field", compute="_compute_is_many2x", store=True
    )
    related_model_id = fields.Many2one(
        "ir.model",
        string="Related model",
        compute="_compute_related_model_id",
        store=True,
    )

    def get_last_field(self, model, path):
        field, path = path.split("/", 1)
        model = model._fields[field]._related_comodel_name
        if path:
            return super(IrExportsLine, self).get_last_field(model, path)
        else:
            return field

    @api.multi
    @api.depends("name")
    def _compute_is_many2x(self):
        for export_line in self:
            field = export_line.get_last_field(
                export_line.export_id.resource, export_line.name
            )
            if field.type in ["many2one", "many2many"]:
                export_line.is_many2x = True

    @api.multi
    @api.depends("name")
    def _compute_related_model_id(self):
        for export_line in self:
            model = (
                self.env[export_line.export_id.resource]
                ._fields[export_line.name]
                ._related_comodel_name
            )
            if model:
                export_line.related_model_id = model.id
