# Copyright 2020 Akretion France (http://www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64

from xlrd import open_workbook

from odoo.tests.common import SavepointCase

from ..models.ir_exports import COLUMN_M2M_SEPARATOR


class TestPatternExport(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        exports_vals = {"name": "Partner list", "resource": "res.partner"}
        cls.ir_exports = cls.env["ir.exports"].create(exports_vals)
        country_code_field = cls.env.ref("base.field_res_country__code")
        country_model = cls.env.ref("base.model_res_country")
        company_model = cls.env.ref("base.model_res_company")
        company_name_field = cls.env.ref("base.field_res_company__name")
        select_tab_vals = {
            "name": "Country list",
            "model_id": country_model.id,
            "field_id": country_code_field.id,
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
        # M2M part
        select_tab_vals = {
            "name": "Company list",
            "model_id": company_model.id,
            "field_id": company_name_field.id,
        }
        cls.select_tab_company = cls.env["ir.exports.select.tab"].create(
            select_tab_vals
        )
        cls.ir_exports_m2m = cls.env["ir.exports"].create(
            {
                "name": "Users list - M2M",
                "resource": "res.users",
                "export_fields": [
                    (0, False, {"name": "id"}),
                    (0, False, {"name": "name"}),
                    (
                        0,
                        False,
                        {
                            "name": "company_ids",
                            "number_occurence": 1,
                            "select_tab_id": cls.select_tab_company.id,
                        },
                    ),
                ],
            }
        )
        cls.separator = COLUMN_M2M_SEPARATOR

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

    def _check_is_many2many(self, export_lines):
        """
        Ensure the is_many2many is correct for given export lines.
        """
        for export_line in export_lines:
            expected_result = False
            if (
                export_line.is_many2x
                and export_line.export_id.resource
                and export_line.name
            ):
                field, model = export_line._get_last_field(
                    export_line.export_id.resource, export_line.name
                )
                if self.env[model]._fields[field].type == "many2many":
                    expected_result = True
            if expected_result:
                self.assertTrue(export_line.is_many2many)
            else:
                self.assertFalse(export_line.is_many2many)

    def test_generate_pattern_is_many2many(self):
        """
        Ensure the is_many2many boolean field on the ir.exports.line
        is correctly set.
        """
        self._check_is_many2many(self.ir_exports.export_fields)
        self._check_is_many2many(self.ir_exports_m2m.export_fields)

    def test_generate_pattern_with_many2many_fields1(self):
        """
        Test the excel generation for M2M fields with 1 occurence.
        Only header part
        """
        for export_line in self.ir_exports_m2m.export_fields:
            if not export_line.is_many2many:
                export_line.unlink()
        # Ensure still at least 1 line!
        self.assertTrue(self.ir_exports_m2m.export_fields)
        self.ir_exports_m2m.generate_pattern()
        decoded_data = base64.b64decode(self.ir_exports_m2m.pattern_file)
        wb = open_workbook(file_contents=decoded_data)
        self.assertEqual(len(wb.sheets()), 2)
        sheet1 = wb.sheet_by_index(0)
        column_name = "{name}{sep}{nb}".format(
            name="company_ids", sep=self.separator, nb=1
        )
        self.assertEquals(column_name, sheet1.cell_value(0, 0))
        sheet2 = wb.sheet_by_index(1)
        companies = self.env["res.company"].search([])
        expected_sheet_name = "{name} ({field})".format(
            name=self.select_tab_company.name, field="name"
        )
        self.assertEquals(expected_sheet_name, sheet2.name)
        # Start at 1 because 0 is the header
        for ind, company in enumerate(companies, start=1):
            self.assertEquals(company.name, sheet2.cell_value(ind, 0))

    def test_generate_pattern_with_many2many_fields2(self):
        """
        Test the excel generation for M2M fields with more than 1 occurence.
        Only header part!
        """
        for export_line in self.ir_exports_m2m.export_fields:
            if not export_line.is_many2many:
                export_line.unlink()
        # Ensure still at least 1 line!
        self.assertTrue(self.ir_exports_m2m.export_fields)
        self.ir_exports_m2m.export_fields.write({"number_occurence": 5})
        self.ir_exports_m2m.generate_pattern()
        decoded_data = base64.b64decode(self.ir_exports_m2m.pattern_file)
        wb = open_workbook(file_contents=decoded_data)
        self.assertEqual(len(wb.sheets()), 2)
        sheet1 = wb.sheet_by_index(0)
        for nb in range(self.ir_exports_m2m.export_fields.number_occurence):
            column_name = "{name}{sep}{nb}".format(
                name="company_ids", sep=self.separator, nb=nb + 1
            )
            self.assertEquals(column_name, sheet1.cell_value(0, nb))
        sheet2 = wb.sheet_by_index(1)
        companies = self.env["res.company"].search([])
        expected_sheet_name = "{name} ({field})".format(
            name=self.select_tab_company.name, field="name"
        )
        self.assertEquals(expected_sheet_name, sheet2.name)
        # Start at 1 because 0 is the header
        for ind, company in enumerate(companies, start=1):
            self.assertEquals(company.name, sheet2.cell_value(ind, 0))

    def test_generate_pattern_with_many2many_fields3(self):
        """
        Test the excel generation for M2M fields with more than 1 occurence.
        Test only the content part
        """
        self.env["res.company"].create(
            {"name": "Awesome company", "user_ids": [(4, self.env.user.id)]}
        )
        self.env["res.company"].create(
            {"name": "Bad company", "user_ids": [(4, self.env.user.id)]}
        )
        # Ensure still at least 1 line!
        nb_occurence = 4
        export_fields_m2m = self.ir_exports_m2m.export_fields.filtered(
            lambda l: l.is_many2many
        )
        self.assertTrue(export_fields_m2m)
        export_fields_m2m.write({"number_occurence": nb_occurence})
        users = self.env["res.users"].search([])
        self.ir_exports_m2m._export_with_record(users)
        attachment = self.env["ir.attachment"].search(
            [("res_model", "=", "ir.exports"), ("res_id", "=", self.ir_exports_m2m.id)],
            limit=1,
        )
        expected_attachment_name = "{name}{ext}".format(
            name=self.ir_exports_m2m.name, ext=".xlsx"
        )
        self.assertEquals(expected_attachment_name, attachment.name)
        decoded_data = base64.b64decode(attachment.datas)
        wb = open_workbook(file_contents=decoded_data)
        sheet1 = wb.sheet_by_index(0)
        for ind, user in enumerate(users, start=1):
            xml_id = user.get_xml_id().get(user.id, "")
            self.assertEquals(xml_id, sheet1.cell_value(ind, 0))
            self.assertEquals(user.name or "", sheet1.cell_value(ind, 1))
            for ind_company, company in enumerate(user.company_ids, start=2):
                self.assertEquals(
                    company.name or "", sheet1.cell_value(ind, ind_company)
                )
            ind_already_checked = max(1, ind_company + 1)
            ind_to_check = nb_occurence + ind_company
            # Ensure others are empty
            for ind_company in range(ind_already_checked, ind_to_check):
                self.assertEquals("", sheet1.cell_value(ind, ind_company))

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
