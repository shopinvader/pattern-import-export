# Copyright 2020 Akretion France (http://www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
# pylint: disable=missing-manifest-dependency
import base64
from io import BytesIO

import openpyxl
import xlrd
import xlsxwriter

from odoo import _, api, fields, models


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
        for select_tab in self._get_select_tab():
            select_tab_name = select_tab.name
            field_name = select_tab.field_id.name
            ad_sheet_name = select_tab_name + " (" + field_name + ")"
            if ad_sheet_name not in ad_sheet_list:
                ad_sheet, ad_row = select_tab._generate_additional_sheet(
                    book, cell_style
                )
                ad_sheet_list[ad_sheet.name] = (ad_sheet, ad_row)
            else:
                ad_sheet = ad_sheet_list[ad_sheet.name][0]
                ad_row = ad_sheet_list[ad_sheet.name][1]
            select_tab._add_xlsx_constraint(sheet, col, ad_sheet, ad_row)
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
            for col, header in enumerate(self._get_header()):
                value = values.get(header, "")
                sheet.write(row, col, value)
        book.close()
        return pattern_file.getvalue()

    def _read_xlsx_file(self, datafile):
        workbook = xlrd.open_workbook(file_contents=BytesIO(datafile).read())
        return workbook.sheet_by_index(0)

    @api.multi
    def _read_import_data_xlsx(self, datafile):
        worksheet = self._read_xlsx_file(datafile)
        headers = []
        for col in range(worksheet.ncols):
            headers.append(worksheet.cell_value(0, col))
        for row in range(1, worksheet.nrows):
            elm = {}
            for col in range(worksheet.ncols):
                elm[headers[col]] = worksheet.cell_value(row, col)
            yield elm

    def _process_load_result_for_xls(self, attachment, res):
        infile = BytesIO(base64.b64decode(attachment.datas))
        wb = openpyxl.load_workbook(filename=infile)
        ws = wb.worksheets[0]
        if ws["A1"] != _("#Error"):
            ws.insert_cols(1)
            ws.cell(1, 1, value=_("#Error"))
        for message in res["messages"]:
            ws.cell(message["rows"]["to"] + 1, 1, value=message["message"].strip())
        output = BytesIO()
        wb.save(output)
        attachment.datas = base64.b64encode(output.getvalue())

        ids = res["ids"] or []
        info = _(
            "Number of record imported {} Number of error/warning {}"
            "\nrecord ids details: {}"
        ).format(len(ids), len(res.get("messages", [])), ids)
        return info

    def _process_load_result(self, attachment, res):
        if self.export_format == "xlsx":
            self._process_load_result_for_xls(attachment, res)
        else:
            return super()._process_load_result(attachment, res)
