# Copyright 2020 Akretion France (http://www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64

from xlrd import open_workbook

from odoo.tests.common import SavepointCase


class TestPatternExport(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super(TestPatternExport, cls).setUpClass()
        exports_vals = {"name": "Partner list", "resource": "res.partner"}
        cls.ir_exports = cls.env["ir.exports"].create(exports_vals)
        field = cls.env.ref("base.field_res_country__code")
        model = cls.env.ref("base.model_res_country")
        select_tab_vals = {
            "name": "Country list",
            "model_id": model.id,
            "field_id": field.id,
            "domain": "[('code', 'in', ['FR', 'BE', 'US'])]",
        }
        cls.select_tab = cls.env["ir.exports.select.tab"].create(select_tab_vals)
        exports_line_vals = [
            {"name": "id", "export_id": cls.ir_exports.id},
            {"name": "name", "export_id": cls.ir_exports.id},
            {"name": "street", "export_id": cls.ir_exports.id},
            {
                "name": "country_id",
                "export_id": cls.ir_exports.id,
                "select_tab_id": cls.select_tab.id,
            },
            {
                "name": "child_ids/country_id",
                "export_id": cls.ir_exports.id,
                "select_tab_id": cls.select_tab.id,
            },
        ]
        cls.env["ir.exports.line"].create(exports_line_vals)

    def test_generate_pattern_with_basic_fields(self):
        self.ir_exports.pattern_last_generation_date = False
        self.ir_exports.pattern_file = False
        self.ir_exports.export_fields[0].unlink()
        self.ir_exports.export_fields[2:].unlink()
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
        self.ir_exports.export_fields[0:3].unlink()
        self.ir_exports.export_fields[1].unlink()
        self.ir_exports.generate_pattern()
        decoded_data = base64.b64decode(self.ir_exports.pattern_file)
        wb = open_workbook(file_contents=decoded_data)
        self.assertEqual(len(wb.sheets()), 2)
        sheet1 = wb.sheet_by_index(0)
        self.assertEqual(sheet1.cell_value(0, 0), "country_id")
        sheet2 = wb.sheet_by_index(1)
        self.assertEqual(sheet2.name, "Country list (code)")
        self.assertEqual(sheet2.cell_value(1, 0), "BE")
        self.assertEqual(sheet2.cell_value(2, 0), "FR")
        self.assertEqual(sheet2.cell_value(3, 0), "US")

    def test_export_with_record(self):
        self.ir_exports.export_fields[4].unlink()
        partner_1 = self.env.ref("base.res_partner_1")
        partner_2 = self.env.ref("base.res_partner_2")
        partner_3 = self.env.ref("base.res_partner_3")
        records = [partner_1, partner_2, partner_3]
        self.ir_exports._export_with_record(records)
        attachment = self.env["ir.attachment"].search(
            [("res_model", "=", "ir.exports"), ("res_id", "=", self.ir_exports.id)],
            limit=1,
        )
        self.assertEqual(attachment.name, "Partner list.xlsx")
        decoded_data = base64.b64decode(attachment.datas)
        wb = open_workbook(file_contents=decoded_data)
        sheet1 = wb.sheet_by_index(0)
        self.assertEqual(sheet1.cell_value(1, 0), "base.res_partner_1")
        self.assertEqual(sheet1.cell_value(2, 0), "base.res_partner_2")
        self.assertEqual(sheet1.cell_value(3, 0), "base.res_partner_3")
        self.assertEqual(sheet1.cell_value(1, 1), "Wood Corner")
        self.assertEqual(sheet1.cell_value(2, 1), "Deco Addict")
        self.assertEqual(sheet1.cell_value(3, 1), "Gemini Furniture")
        self.assertEqual(sheet1.cell_value(1, 2), "1164 Cambridge Drive")
        self.assertEqual(sheet1.cell_value(2, 2), "325 Elsie Drive")
        self.assertEqual(sheet1.cell_value(3, 2), "1128 Lunetta Street")
        self.assertEqual(sheet1.cell_value(1, 3), "US")
        self.assertEqual(sheet1.cell_value(2, 3), "US")
        self.assertEqual(sheet1.cell_value(3, 3), "US")

    def test_export_multi_level_fields(self):
        partner_2 = self.env.ref("base.res_partner_2")
        records = [partner_2]
        self.ir_exports._export_with_record(records)
        attachment = self.env["ir.attachment"].search(
            [("res_model", "=", "ir.exports"), ("res_id", "=", self.ir_exports.id)],
            limit=1,
        )
        self.assertEqual(attachment.name, "Partner list.xlsx")
        decoded_data = base64.b64decode(attachment.datas)
        wb = open_workbook(file_contents=decoded_data)
        sheet1 = wb.sheet_by_index(0)
        self.assertEqual(sheet1.cell_value(1, 0), "base.res_partner_2")
        self.assertEqual(sheet1.cell_value(1, 1), "Deco Addict")
        self.assertEqual(sheet1.cell_value(1, 2), "325 Elsie Drive")
        self.assertEqual(sheet1.cell_value(1, 3), "US")
        self.assertEqual(sheet1.cell_value(1, 4), "US")

    def test_export_with_record_wizard(self):
        self.ir_exports.generate_pattern()
        partner_1 = self.env.ref("base.res_partner_1")
        partner_2 = self.env.ref("base.res_partner_2")
        partner_3 = self.env.ref("base.res_partner_3")
        record_ids = [partner_1.id, partner_2.id, partner_3.id]
        wiz = (
            self.env["export.pattern.wizard"]
            .with_context(active_ids=record_ids, active_model="res.partner")
            .create({"model": "res.partner", "ir_exports_id": self.ir_exports.id})
        )
        job_uuid = wiz.run()
        self.assertEqual(
            job_uuid.description,
            "Generate export 'res.partner' with export pattern 'Partner list'",
        )
        self.assertEqual(job_uuid.model_name, "res.partner")
