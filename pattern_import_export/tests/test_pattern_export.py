# Copyright 2020 Akretion France (http://www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64

from xlrd import open_workbook

from odoo.tests.common import SavepointCase


class TestPatternExport(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super(TestPatternExport, cls).setUpClass()
        cls.exports_vals = {"name": "Partner list", "resource": "res.partner"}
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
        self.assertEqual(sheet1.name, "Partner list")
        self.assertEqual(sheet1.cell_value(0, 0), "name")
        self.assertEqual(sheet1.cell_value(0, 1), "street")

    def test_generate_pattern_with_many2one_fields(self):
        field = self.env.ref("base.field_res_country__code")
        model = self.env.ref("base.model_res_country")
        select_tab_vals = {
            "name": "Country list",
            "model_id": model.id,
            "field_id": field.id,
            "domain": "[('code', 'in', ['FR', 'BE', 'US'])]",
        }
        select_tab = self.env["ir.exports.select.tab"].create(select_tab_vals)
        self.env["ir.exports.line"].create(
            [
                {
                    "name": "country_id",
                    "export_id": self.ir_exports.id,
                    "select_tab_id": select_tab.id,
                }
            ]
        )
        self.ir_exports.generate_pattern()
        decoded_data = base64.b64decode(self.ir_exports.pattern_file)
        wb = open_workbook(file_contents=decoded_data)
        self.assertEqual(len(wb.sheets()), 2)
        sheet1 = wb.sheet_by_index(0)
        self.assertEqual(sheet1.cell_value(0, 2), "country_id")
        sheet2 = wb.sheet_by_index(1)
        self.assertEqual(sheet2.name, "Country list")
        self.assertEqual(sheet2.cell_value(1, 0), "BE")
        self.assertEqual(sheet2.cell_value(2, 0), "FR")
        self.assertEqual(sheet2.cell_value(3, 0), "US")

    def test_export_with_record(self):
        exports_vals = {"name": "My Partner list", "resource": "res.partner"}
        ir_exports = self.env["ir.exports"].create(exports_vals)
        field = self.env.ref("base.field_res_country__name")
        model = self.env.ref("base.model_res_country")
        select_tab_vals = {
            "name": "Country list",
            "model_id": model.id,
            "field_id": field.id,
        }
        select_tab = self.env["ir.exports.select.tab"].create(select_tab_vals)
        exports_line_vals = [
            {"name": "id", "export_id": ir_exports.id},
            {"name": "name", "export_id": ir_exports.id},
            {"name": "street", "export_id": ir_exports.id},
            {
                "name": "country_id",
                "export_id": ir_exports.id,
                "select_tab_id": select_tab.id,
            },
        ]
        self.env["ir.exports.line"].create(exports_line_vals)
        partner_1 = self.env.ref("base.res_partner_1")
        partner_2 = self.env.ref("base.res_partner_2")
        partner_3 = self.env.ref("base.res_partner_3")
        records = [partner_1, partner_2, partner_3]
        export_file = ir_exports._export_with_record(records)
        decoded_data = base64.b64decode(export_file)
        wb = open_workbook(file_contents=decoded_data)
        sheet1 = wb.sheet_by_index(0)
        self.assertEqual(sheet1.cell_value(1, 0), 9)
        self.assertEqual(sheet1.cell_value(2, 0), 10)
        self.assertEqual(sheet1.cell_value(3, 0), 11)
        self.assertEqual(sheet1.cell_value(1, 1), "Wood Corner")
        self.assertEqual(sheet1.cell_value(2, 1), "Deco Addict")
        self.assertEqual(sheet1.cell_value(3, 1), "Gemini Furniture")
        self.assertEqual(sheet1.cell_value(1, 2), "1164 Cambridge Drive")
        self.assertEqual(sheet1.cell_value(2, 2), "325 Elsie Drive")
        self.assertEqual(sheet1.cell_value(3, 2), "1128 Lunetta Street")
        self.assertEqual(sheet1.cell_value(1, 3), "United States")
        self.assertEqual(sheet1.cell_value(2, 3), "United States")
        self.assertEqual(sheet1.cell_value(3, 3), "United States")
