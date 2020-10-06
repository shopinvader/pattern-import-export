# Copyright 2020 Akretion France (http://www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
# pylint: disable=missing-manifest-dependency

import base64
from io import BytesIO
from os import path

import openpyxl

# pylint: disable=odoo-addons-relative-import
from odoo.addons.pattern_import_export.tests.common import ExportPatternCommon

CELL_VALUE_EMPTY = None

# helper to dump the result of the import into an excel file
DUMP_OUTPUT = False


PATH = path.dirname(__file__) + "/fixtures/"


class ExportPatternExcelCommon(ExportPatternCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(
            context=dict(
                cls.env.context, test_queue_job_no_delay=True  # no jobs thanks
            )
        )
        cls.ir_export_partner = cls.env["ir.exports"].create(
            {
                "name": "Partner",
                "resource": "res.partner",
                "is_pattern": True,
                "export_format": "xlsx",
            }
        )
        cls.ir_export_users = cls.env["ir.exports"].create(
            {
                "name": "User",
                "resource": "res.users",
                "is_pattern": True,
                "export_format": "xlsx",
            }
        )
        cls.user_admin = cls.env.ref("base.user_admin")
        cls.user_demo = cls.env.ref("base.user_demo")
        for el in cls.ir_exports, cls.ir_exports_m2m, cls.ir_exports_o2m:
            el.export_format = "xlsx"

    def _helper_get_resulting_wb(self, export, records):
        export._export_with_record(records)
        attachment = self._get_attachment(export)
        self.assertEqual(attachment.name, export.name + ".xlsx")
        decoded_data = base64.b64decode(attachment.datas)
        decoded_obj = BytesIO(decoded_data)
        return openpyxl.load_workbook(decoded_obj)

    def _helper_check_cell_values(self, sheet, expected_values):
        """ To allow for csv-like syntax in tests, just give a list
        of lists, with 1 list <=> 1 row """
        for itr_row, row in enumerate(expected_values, start=2):
            for itr_col, expected_cell_value in enumerate(row, start=1):
                cell_value = sheet.cell(row=itr_row, column=itr_col).value
                self.assertEqual(cell_value, expected_cell_value)

    def _helper_check_headers(self, sheet, expected_headers):
        for itr_col, expected_cell_value in enumerate(expected_headers, start=1):
            cell_value = sheet.cell(row=1, column=itr_col).value
            self.assertEqual(cell_value, expected_cell_value)

    @classmethod
    def _load_excel_file(cls, filename, export_id):
        data = base64.b64encode(open(PATH + filename, "rb").read())
        wizard = cls.env["import.pattern.wizard"].create(
            {
                "ir_exports_id": export_id.id,
                "import_file": data,
                "filename": "example.xlsx",
            }
        )
        wizard.action_launch_import()

        if DUMP_OUTPUT:
            attachment = cls.env["patterned.import.export"].search(
                [], limit=1, order="id desc"
            )
            output_name = filename.replace(".xlsx", ".result.xlsx")
            with open(output_name, "wb") as output:
                output.write(base64.b64decode(attachment.datas))
