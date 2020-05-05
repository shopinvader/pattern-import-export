# Copyright 2020 Akretion France (http://www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64

from xlrd import open_workbook

from odoo.tests.common import SavepointCase


class TestPatternExport(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super(TestPatternExport, cls).setUpClass()
        cls.exports_vals = {"name": "Partner Export Test", "resource": "res.partner"}
        cls.ir_exports = cls.env["ir.exports"].create(cls.exports_vals)
        cls.exports_line_vals = [
            {"name": "name", "export_id": cls.ir_exports.id},
            {"name": "street", "export_id": cls.ir_exports.id},
        ]
        cls.ir_exports_line = cls.env["ir.exports.line"].create(cls.exports_line_vals)

    def test_generate_pattern_with_basic_fields(self):
        self.ir_exports.pattern_last_generation_date = False
        self.ir_exports.pattern_file = False
        res = self.ir_exports.generate_pattern()
        self.assertEqual(res, True)
        self.assertNotEqual(self.ir_exports.pattern_file, False)
        self.assertNotEqual(self.ir_exports.pattern_last_generation_date, False)
        decoded_data = base64.b64decode(self.ir_exports.pattern_file)
        wb = open_workbook(file_contents=decoded_data)
        sheet1 = wb.sheet_by_index(0)
        self.assertEqual(sheet1.name, "res.partner")
        self.assertEqual(sheet1.cell_value(0, 0), "name")
        self.assertEqual(sheet1.cell_value(0, 1), "street")

    def test_generate_pattern_with_many2one_fields(self):
        self.env["ir.exports.line"].create(
            [{"name": "country_id", "export_id": self.ir_exports.id}]
        )
        self.ir_exports.generate_pattern()
        decoded_data = base64.b64decode(self.ir_exports.pattern_file)
        wb = open_workbook(file_contents=decoded_data)
        self.assertEqual(len(wb.sheets()), 2)
        sheet1 = wb.sheet_by_index(0)
        self.assertEqual(sheet1.cell_value(0, 2), "country_id")
        sheet2 = wb.sheet_by_index(1)
        self.assertEqual(sheet2.name, "res.country")
        self.assertEqual(sheet2.cell_value(0, 0), "country_id")
        countries = self.env["res.country"].search([])
        countries_names = countries.name_get()
        self.assertEqual(sheet2.col(0), countries_names)
