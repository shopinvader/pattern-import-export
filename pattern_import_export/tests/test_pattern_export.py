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
            {"name": "country_id", "export_id": cls.ir_exports.id},
        ]
        cls.ir_exports_line = cls.env["ir.exports.line"].create(cls.exports_line_vals)

    def test_generate_pattern(self):
        self.ir_exports.pattern_last_generation_date = False
        self.ir_exports.pattern_file = False
        res = self.ir_exports.generate_pattern()
        self.assertEqual(res, True)
        self.assertNotEqual(self.ir_exports.pattern_file, False)
        self.assertNotEqual(self.ir_exports.pattern_last_generation_date, False)
        decoded_data = base64.b64decode(self.ir_exports.pattern_file)
        wb = open_workbook(file_contents=decoded_data)
        self.assertEqual(wb.sheet_by_index(0).name, self.exports_vals["resource"])
        self.assertEqual(wb.sheet_by_index(1).name, self.country_model.model)
        self.assertEqual(
            wb.sheets()[0].cell_value(0, 0), self.exports_line_vals[0]["name"]
        )
        self.assertEqual(
            wb.sheets()[0].cell_value(0, 1), self.exports_line_vals[1]["name"]
        )
        self.assertEqual(
            wb.sheets()[0].cell_value(0, 2), self.exports_line_vals[2]["name"]
        )
