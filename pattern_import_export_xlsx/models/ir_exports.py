# Copyright 2020 Akretion France (http://www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from io import BytesIO

import xlsxwriter

from odoo import api, fields, models


class IrExports(models.Model):
    _inherit = "ir.exports"

    export_format = fields.Selection(selection_add=[("xlsx", "Excel")])

    @api.multi
    def _create_xlsx_file(self):
        self.ensure_one()
        pattern_file = BytesIO()
        book = xlsxwriter.Workbook(pattern_file)
        sheet = book.add_worksheet(self.name)
        cell_style = book.add_format({"bold": True})
        ad_sheet_list = {}
        for col, header in enumerate(self._get_header()):
            sheet.write(0, col, header, cell_style)
        # Manage others tab of Excel file!
        for export_line in self.export_fields:
            if export_line.is_many2x and export_line.select_tab_id:
                select_tab_name = export_line.select_tab_id.name
                field_name = export_line.select_tab_id.field_id.name
                ad_sheet_name = select_tab_name + " (" + field_name + ")"
                if ad_sheet_name not in ad_sheet_list:
                    select_tab_id = export_line.select_tab_id
                    ad_sheet, ad_row = select_tab_id._generate_additional_sheet(
                        book, cell_style
                    )
                    ad_sheet_list[ad_sheet.name] = (ad_sheet, ad_row)
                else:
                    ad_sheet = ad_sheet_list[ad_sheet.name][0]
                    ad_row = ad_sheet_list[ad_sheet.name][1]
                export_line._add_xlsx_constraint(sheet, col, ad_sheet, ad_row)
        return book, sheet, pattern_file

    @api.multi
    def _export_with_record_xlsx(self, records):
        """
        Export given recordset
        @param records: recordset
        @return: string
        """
        self.ensure_one()
        book, sheet, pattern_file = self._create_xlsx_file()
        for row, values in enumerate(self._get_data_to_export(records), start=1):
            for col, value in enumerate(values.values()):
                sheet.write(row, col, value)
        book.close()
        return pattern_file.getvalue()
