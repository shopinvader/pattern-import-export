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
        # Allows you to generate an excel file to be used as
        # a template for the import.
        pattern_file = BytesIO()
        book = xlsxwriter.Workbook(pattern_file)
        sheet = book.add_worksheet(self.resource)
        bold = book.add_format({"bold": True})
        row = 0
        col = 0
        for export_line in self.export_fields:
            sheet.write(row, col, export_line.name, bold)
            if export_line.is_many2x:
                if not export_line.select_tab_id:
                    select_tab_vals = {
                        "name": export_line.related_model_id.model,
                        "model_id": export_line.related_model_id.id,
                    }
                    res = self.env["ir.exports.select.tab"].create(select_tab_vals)
                    export_line.select_tab_id = res.id
                add_sheet = export_line.select_tab_id._generate_additional_sheet(
                    book, bold
                )
                export_line._add_excel_constraint(add_sheet, sheet, col)
            col += 1
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

    def _get_last_field(self, model, path):
        if "/" not in path:
            path = path + "/"
        field, path = path.split("/", 1)
        if path:
            model = self.env[model]._fields[field]._related_comodel_name
            return self._get_last_field(model, path)
        else:
            return field, model

    @api.multi
    @api.depends("name")
    def _compute_is_many2x(self):
        for export_line in self:
            field, model = export_line._get_last_field(
                export_line.export_id.resource, export_line.name
            )
            if self.env[model]._fields[field].type in ["many2one", "many2many"]:
                export_line.is_many2x = True

    @api.multi
    @api.depends("name")
    def _compute_related_model_id(self):
        for export_line in self:
            field, model = export_line._get_last_field(
                export_line.export_id.resource, export_line.name
            )
            related_comodel = self.env[model]._fields[field]._related_comodel_name
            if related_comodel:
                comodel = self.env["ir.model"].search(
                    [("model", "=", related_comodel)], limit=1
                )
                export_line.related_model_id = comodel.id

    def _add_excel_constraint(self, add_sheet, sheet, col):
        sheet.data_validation(
            1, col, 1048576, col, {"validate": "list", "source": add_sheet}
        )
        return True
