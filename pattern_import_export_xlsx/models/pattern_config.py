# Copyright 2020 Akretion France (http://www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
# pylint: disable=missing-manifest-dependency
import base64
from io import BytesIO

import openpyxl
from openpyxl.utils import get_column_letter, quote_sheetname
from openpyxl.worksheet.datavalidation import DataValidation

from odoo import _, api, fields, models
from odoo.exceptions import UserError

STOP_AFTER_NBR_EMPTY = 10


class PatternConfig(models.Model):
    _inherit = "pattern.config"

    export_format = fields.Selection(selection_add=[("xlsx", "Excel")])
    tab_to_import = fields.Selection(
        [("first", "First"), ("match_name", "Match Name")], default="first"
    )

    @api.multi
    def _create_xlsx_file(self, records):
        self.ensure_one()
        book = openpyxl.Workbook(write_only=True)
        main_sheet = self._build_main_sheet_structure(book)
        self._populate_main_sheet_rows(main_sheet, records)
        tab_data = self.export_fields._get_tab_data()
        self._create_tabs(book, tab_data)
        if len(records.ids) < 1000:
            main_sheet_length = 1000
        else:
            main_sheet_length = len(records.ids) + 2
        self._create_validators(main_sheet, main_sheet_length, tab_data)
        book.close()
        xlsx_file = BytesIO()
        book.save(xlsx_file)
        return xlsx_file

    def _build_main_sheet_structure(self, book):
        """
        Write main sheet header and other style details
        """
        main_sheet = book["Sheet"]
        main_sheet.title = self.name
        if self.use_description:
            for col, header in enumerate(
                self._get_header(use_description=True), start=1
            ):
                main_sheet.cell(row=1, column=col, value=header)
            for col, header in enumerate(self._get_header(), start=1):
                main_sheet.cell(row=2, column=col, value=header)
        else:
            for col, header in enumerate(self._get_header(), start=1):
                main_sheet.cell(row=1, column=col, value=header)
        return main_sheet

    def _populate_main_sheet_rows(self, main_sheet, records):
        """
        Get the actual data and write it row by row on the main sheet
        """
        headers = self._get_header()
        for row, values in enumerate(
            self._get_data_to_export(records), start=self.row_start_records
        ):
            for col, header in enumerate(headers, start=1):
                main_sheet.cell(row=row, column=col, value=values.get(header, ""))

    def _create_tabs(self, book, tab_data):
        """Create additional sheets for export lines with create tab option
        and write all valid choices"""
        for name, headers, data, __ in tab_data:
            new_sheet = book.create_sheet(name)
            for col_number, header in enumerate(headers, start=1):
                new_sheet.cell(row=1, column=col_number, value=header)
            for row_number, row_data in enumerate(data, start=2):
                for col_number, cell_data in enumerate(row_data, start=1):
                    new_sheet.cell(row=row_number, column=col_number, value=cell_data)

    def _create_validators(self, main_sheet, main_sheet_length, tab_data):
        """Add validators: source permitted records from tab sheets,
        apply validation to main sheet"""
        for el in tab_data:
            tab_name, _, data, col_dst = el
            col_letter_dst = get_column_letter(col_dst)
            # TODO support arbitrary columns/attributes instead of
            #  only name
            col_letter_src = get_column_letter(1)
            range_src = "${}$2:${}${}".format(
                col_letter_src, col_letter_src, str(1 + len(data))
            )
            formula_range_src = "=" + quote_sheetname(tab_name) + "!" + range_src
            validation = DataValidation(type="list", formula1=formula_range_src)
            range_dst = "${}${}:${}${}".format(
                col_letter_dst,
                str(self.row_start_records),
                col_letter_dst,
                str(max(main_sheet_length, 2)),
            )
            validation.add(range_dst)
            main_sheet.add_data_validation(validation)

    @api.multi
    def _export_with_record_xlsx(self, records):
        """
        Export given recordset
        @param records: recordset
        @return: string
        """
        self.ensure_one()
        excel_file = self._create_xlsx_file(records)
        return excel_file.getvalue()

    # Import part

    def _get_worksheet(self, workbook):
        name = None
        if self.tab_to_import == "first":
            name = workbook.sheetnames[0]
        elif self.tab_to_import == "match_name":
            for sheetname in workbook.sheetnames:
                if sheetname.lower() == self.name.lower():
                    name = sheetname
                    break
            if not name:
                raise UserError(
                    _("The file do not contain tab with the name {}").format(self.name)
                )
        else:
            raise UserError(_("Please select a tab to import on the pattern"))
        return workbook[name]

    @api.multi
    def _read_import_data_xlsx(self, datafile):
        workbook = openpyxl.load_workbook(
            BytesIO(datafile), data_only=True, read_only=True
        )
        worksheet = self._get_worksheet(workbook)
        headers = None
        count_empty = 0
        for idx, row in enumerate(worksheet.rows):
            if self.nr_of_header_rows == idx + 1:
                headers = [x.value for x in row]
            elif headers:
                vals = [x.value for x in row]
                if any(vals):
                    count_empty = 0
                    yield dict(zip(headers, vals))
                else:
                    count_empty += 1
            if count_empty > STOP_AFTER_NBR_EMPTY:
                break
        workbook.close()

    def _write_error_in_xlsx(self, attachment, vals):
        # TODO writing in an existing big excel file is long with openpyxl
        # maybe we should try some other tools
        # https://editpyxl.readthedocs.io
        infile = BytesIO(base64.b64decode(attachment.datas))
        wb = openpyxl.load_workbook(filename=infile)
        ws = self._get_worksheet(wb)

        # we clear the error col if exist
        if ws["A1"].value == _("#Error"):
            ws.delete_cols(1)
        ws.insert_cols(1)
        ws.cell(1, 1, value=_("#Error"))

        for idx, message in vals:
            ws.cell(idx, 1, value=message)

        output = BytesIO()
        wb.save(output)
        attachment.datas = base64.b64encode(output.getvalue())

    def _process_load_result_for_xls(self, attachment, res):
        global_message = []
        vals = []
        for message in res["messages"]:
            if "rows" in message:
                vals.append((message["rows"]["to"] + 1, message["message"].strip()))
            else:
                global_message.append(message)

        if vals:
            self._write_error_in_xlsx(attachment, vals)

        ids = res["ids"] or []
        info = _("Number of record imported {} Number of error/warning {}").format(
            len(ids), len(res.get("messages", []))
        )
        info_detail = _("Record ids: {}" "\nDetails: {}").format(
            ids,
            "\n".join(
                [
                    "{}: {}".format(message["type"], message["message"])
                    for message in global_message
                ]
            ),
        )
        if res.get("messages"):
            state = "fail"
        else:
            state = "success"
        return info, info_detail, state

    def _process_load_result(self, attachment, res):
        if self.export_format == "xlsx":
            return self._process_load_result_for_xls(attachment, res)
        else:
            return super()._process_load_result(attachment, res)
