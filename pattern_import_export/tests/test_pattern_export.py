# Copyright 2020 Akretion France (http://www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo.tests.common import SavepointCase

from .common import ExportPatternCommon


class TestPatternExport(ExportPatternCommon, SavepointCase):
    def test_get_header1(self):
        """
        Ensure the header is correctly generated
        @return:
        """
        headers = self.ir_exports._get_header()
        expected_header = ["id", "name", "street", "country_id", "child_ids/country_id"]
        self.assertEquals(expected_header, headers)

    def test_get_header2(self):
        """
        Ensure the header is correctly generated in case of M2M with 1 occurrence
        @return:
        """
        headers = self.ir_exports_m2m._get_header()
        expected_header = ["id", "name", "company_ids|1"]
        self.assertEquals(expected_header, headers)

    def test_get_header3(self):
        """
        Ensure the header is correctly generated in case of M2M more than 1 occurrence
        @return:
        """
        export_fields_m2m = self.ir_exports_m2m.export_fields.filtered(
            lambda l: l.is_many2many
        )
        self.assertTrue(export_fields_m2m)
        export_fields_m2m.write({"number_occurence": 5})
        headers = self.ir_exports_m2m._get_header()
        expected_header = [
            "id",
            "name",
            "company_ids|1",
            "company_ids|2",
            "company_ids|3",
            "company_ids|4",
            "company_ids|5",
        ]
        self.assertEquals(expected_header, headers)

    def test_get_header4(self):
        """
        Ensure the header is correctly generated in case of O2M.
        This O2M contains a sub-pattern whith a M2M with 1 occurrence.
        @return:
        """
        headers = self.ir_exports_o2m._get_header()
        expected_header = [
            "id",
            "name",
            "user_ids|1|id",
            "user_ids|1|name",
            "user_ids|1|company_ids|1",
            "user_ids|2|id",
            "user_ids|2|name",
            "user_ids|2|company_ids|1",
            "user_ids|3|id",
            "user_ids|3|name",
            "user_ids|3|company_ids|1",
        ]
        self.assertEquals(expected_header, headers)

    def test_get_header5(self):
        """
        Ensure the header is correctly generated in case of O2M.
        For this case, the O2M contains a sub-pattern with a M2M with more
        than 1 occurrence
        @return:
        """
        export_fields_m2m = self.ir_exports_m2m.export_fields.filtered(
            lambda l: l.is_many2many
        )
        self.assertTrue(export_fields_m2m)
        export_fields_m2m.write({"number_occurence": 5})
        headers = self.ir_exports_o2m._get_header()
        expected_header = [
            "id",
            "name",
            "user_ids|1|id",
            "user_ids|1|name",
            "user_ids|1|company_ids|1",
            "user_ids|1|company_ids|2",
            "user_ids|1|company_ids|3",
            "user_ids|1|company_ids|4",
            "user_ids|1|company_ids|5",
            "user_ids|2|id",
            "user_ids|2|name",
            "user_ids|2|company_ids|1",
            "user_ids|2|company_ids|2",
            "user_ids|2|company_ids|3",
            "user_ids|2|company_ids|4",
            "user_ids|2|company_ids|5",
            "user_ids|3|id",
            "user_ids|3|name",
            "user_ids|3|company_ids|1",
            "user_ids|3|company_ids|2",
            "user_ids|3|company_ids|3",
            "user_ids|3|company_ids|4",
            "user_ids|3|company_ids|5",
        ]
        self.assertEquals(expected_header, headers)

    def test_get_data_to_export1(self):
        """
        Ensure the _get_data_to_export return expected data
        @return:
        """
        expected_results = [
            {
                "id": "base.res_partner_1",
                "name": "Wood Corner",
                "street": "1164 Cambridge Drive",
                "country_id": "US",
                "child_ids/country_id": "US",
            },
            {
                "id": "base.res_partner_2",
                "name": "Deco Addict",
                "street": "325 Elsie Drive",
                "country_id": "US",
                "child_ids/country_id": "US",
            },
            {
                "id": "base.res_partner_3",
                "name": "Gemini Furniture",
                "street": "1128 Lunetta Street",
                "country_id": "US",
                "child_ids/country_id": "US",
            },
        ]
        results = self.ir_exports._get_data_to_export(self.partners)
        for result, expected_result in zip(results, expected_results):
            self.assertDictEqual(expected_result, result)

    def test_get_data_to_export2(self):
        """
        Ensure the _get_data_to_export return expected data with M2M with only
        1 occurrence.
        @return:
        """
        expected_results = [
            {
                "id": "base.user_root",
                "name": "OdooBot",
                "company_ids|1": "Awesome company",
            }
        ]
        results = self.ir_exports_m2m._get_data_to_export(self.env.user)
        for result, expected_result in zip(results, expected_results):
            self.assertDictEqual(expected_result, result)

    def test_get_data_to_export3(self):
        """
        Ensure the _get_data_to_export return expected data with M2M with more
        than 1 occurrence.
        @return:
        """
        export_fields_m2m = self.ir_exports_m2m.export_fields.filtered(
            lambda l: l.is_many2many
        )
        self.assertTrue(export_fields_m2m)
        export_fields_m2m.write({"number_occurence": 5})
        expected_results = [
            {
                "id": "base.user_root",
                "name": "OdooBot",
                "company_ids|1": "Awesome company",
                "company_ids|2": "Bad company",
                "company_ids|3": "YourCompany",
            }
        ]
        results = self.ir_exports_m2m._get_data_to_export(self.env.user)
        for result, expected_result in zip(results, expected_results):
            self.assertDictEqual(expected_result, result)

    def test_get_data_to_export4(self):
        """
        Ensure the _get_data_to_export return expected data with O2M with a
        M2M who contains only 1 occurrence.
        @return:
        """
        expected_results = [
            {
                "id": "base.res_partner_1",
                "name": "Wood Corner",
                "user_ids|1|id": self.user1.get_xml_id().get(self.user1.id),
                "user_ids|1|name": "Wood Corner",
                "user_ids|1|company_ids|1": "Awesome company",
            },
            {
                "id": "base.res_partner_2",
                "name": "Deco Addict",
                "user_ids|1|id": self.user3.get_xml_id().get(self.user3.id),
                "user_ids|1|name": "Deco Addict",
                "user_ids|1|company_ids|1": "YourCompany",
            },
            {"id": "base.res_partner_3", "name": "Gemini Furniture"},
        ]
        results = self.ir_exports_o2m._get_data_to_export(self.partners)
        for result, expected_result in zip(results, expected_results):
            self.assertDictEqual(expected_result, result)

    def test_get_data_to_export5(self):
        """
        Ensure the _get_data_to_export return expected data with O2M with a
        M2M who contains more than 1 occurrence.
        @return:
        """
        export_fields_m2m = self.ir_exports_m2m.export_fields.filtered(
            lambda l: l.is_many2many
        )
        self.assertTrue(export_fields_m2m)
        export_fields_m2m.write({"number_occurence": 5})
        export_fields_o2m = self.ir_exports_o2m.export_fields.filtered(
            lambda l: l.is_one2many
        )
        self.assertTrue(export_fields_o2m)
        export_fields_o2m.write({"number_occurence": 3})
        expected_results = [
            {
                "id": "base.res_partner_1",
                "name": "Wood Corner",
                "user_ids|1|id": self.user1.get_xml_id().get(self.user1.id),
                "user_ids|1|name": "Wood Corner",
                "user_ids|1|company_ids|1": "Awesome company",
                "user_ids|1|company_ids|2": "Bad company",
                "user_ids|1|company_ids|3": "YourCompany",
            },
            {
                "id": "base.res_partner_2",
                "name": "Deco Addict",
                "user_ids|1|id": self.user3.get_xml_id().get(self.user3.id),
                "user_ids|1|name": "Deco Addict",
                "user_ids|1|company_ids|1": "YourCompany",
            },
            {"id": "base.res_partner_3", "name": "Gemini Furniture"},
        ]
        results = self.ir_exports_o2m._get_data_to_export(self.partners)
        for result, expected_result in zip(results, expected_results):
            self.assertDictEqual(expected_result, result)
