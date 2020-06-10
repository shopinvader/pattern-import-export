# Copyright 2020 Akretion France (http://www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
from io import BytesIO

import xlsxwriter

from odoo import api, fields, models

COLUMN_M2M_SEPARATOR = "|"


class IrExports(models.Model):
    _inherit = "ir.exports"

    pattern_file = fields.Binary(string="Pattern file", readonly=True)
    pattern_last_generation_date = fields.Datetime(
        string="Pattern last generation date", readonly=True
    )

    @api.multi
    def _create_xlsx_file(self):
        pattern_file = BytesIO()
        book = xlsxwriter.Workbook(pattern_file)
        sheet = book.add_worksheet(self.name)
        bold = book.add_format({"bold": True})
        row = 0
        col = 0
        ad_sheet_list = {}
        for export_line in self.export_fields:
            base_column_name = column_name = export_line.name
            nb_occurence = 1
            if export_line.is_many2many:
                nb_occurence = max(1, export_line.number_occurence)
            line_added = 0
            while line_added < nb_occurence:
                if export_line.is_many2many:
                    column_name = "{column_name}{separator}{nb}".format(
                        column_name=base_column_name,
                        separator=COLUMN_M2M_SEPARATOR,
                        nb=line_added + 1,
                    )
                sheet.write(row, col, column_name, bold)
                col += 1
                line_added += 1
            if export_line.is_many2x and export_line.select_tab_id:
                select_tab_name = export_line.select_tab_id.name
                field_name = export_line.select_tab_id.field_id.name
                ad_sheet_name = select_tab_name + " (" + field_name + ")"
                if ad_sheet_name not in ad_sheet_list:
                    select_tab_id = export_line.select_tab_id
                    ad_sheet, ad_row = select_tab_id._generate_additional_sheet(
                        book, bold
                    )
                    ad_sheet_list[ad_sheet.name] = (ad_sheet, ad_row)
                else:
                    ad_sheet = ad_sheet_list[ad_sheet.name][0]
                    ad_row = ad_sheet_list[ad_sheet.name][1]
                export_line._add_xlsx_constraint(sheet, col, ad_sheet, ad_row)
        return book, sheet, pattern_file

    @api.multi
    def generate_pattern(self):
        # Allows you to generate an xlsx file to be used as
        # a pattern for the export.
        for export in self:
            book, sheet, pattern_file = export._create_xlsx_file()
            book.close()
            export.pattern_file = base64.b64encode(pattern_file.getvalue())
            export.pattern_last_generation_date = fields.Datetime.now()
        return True

    @api.multi
    def _export_with_record(self, records):
        for export in self:
            book, sheet, pattern_file = export._create_xlsx_file()
            row = 1
            for record in records:
                fields_to_export = []
                nb_field_column = {}
                for export_line in export.export_fields:
                    nb_column = 1
                    if export_line.is_many2x and export_line.select_tab_id:
                        field_name = export_line.select_tab_id.field_id.name
                        field = export_line.name + "/" + field_name
                        if export_line.is_many2many:
                            nb_column = max(1, export_line.number_occurence)
                    else:
                        field = export_line.name
                    fields_to_export.append(field)
                    nb_field_column.update({field: nb_column})
                # The data-structure returned by export_data is different
                # that the one used to export.
                # export_data(...) return a dict with a keys named 'datas'
                # and it contains a list of list.
                # Each list item is a line (for M2M) but for the export,
                # we want to display these lines as column.
                # So we have to convert
                res = record.export_data(fields_to_export, raw_data=False)
                list_dict_values = []
                for data in res.get("datas", []):
                    data_dict = {}
                    for field, value in zip(fields_to_export, data):
                        data_dict.update({field: value})
                    list_dict_values.append(data_dict)
                col = 0
                for field, nb_occurence in nb_field_column.items():
                    for current_occurence in range(0, nb_occurence):
                        value = ""
                        if len(list_dict_values) >= current_occurence + 1:
                            value = list_dict_values[current_occurence].get(field)
                        sheet.write(row, col, value)
                        col += 1
                row += 1
            book.close()
            attachment_datas = base64.b64encode(pattern_file.getvalue())
            self.env["ir.attachment"].create(
                {
                    "name": export.name + ".xlsx",
                    "type": "binary",
                    "res_id": export.id,
                    "res_model": "ir.exports",
                    "datas": attachment_datas,
                }
            )
        return True
