# Copyright 2020 Akretion France (http://www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from collections import OrderedDict

from odoo.tests.common import SavepointCase

from .common import ExportPatternCommon


class TestPatternExport(ExportPatternCommon, SavepointCase):
    def test_get_header1(self):
        """
        Ensure the header is correctly generated
        @return:
        """
        headers = self.ir_exports._get_header()
        expected_header = [
            "id",
            "name",
            "street",
            "country_id|code",
            "child_ids|1|country_id|code",
        ]
        self.assertEquals(expected_header, headers)

    def test_get_header2(self):
        """
        Ensure the header is correctly generated in case of M2M with 1 occurrence
        @return:
        """
        headers = self.ir_exports_m2m._get_header()
        expected_header = ["id", "name", "company_ids|1|name"]
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
            "company_ids|1|name",
            "company_ids|2|name",
            "company_ids|3|name",
            "company_ids|4|name",
            "company_ids|5|name",
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
            "user_ids|1|company_ids|1|name",
            "user_ids|2|id",
            "user_ids|2|name",
            "user_ids|2|company_ids|1|name",
            "user_ids|3|id",
            "user_ids|3|name",
            "user_ids|3|company_ids|1|name",
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
            "user_ids|1|company_ids|1|name",
            "user_ids|1|company_ids|2|name",
            "user_ids|1|company_ids|3|name",
            "user_ids|1|company_ids|4|name",
            "user_ids|1|company_ids|5|name",
            "user_ids|2|id",
            "user_ids|2|name",
            "user_ids|2|company_ids|1|name",
            "user_ids|2|company_ids|2|name",
            "user_ids|2|company_ids|3|name",
            "user_ids|2|company_ids|4|name",
            "user_ids|2|company_ids|5|name",
            "user_ids|3|id",
            "user_ids|3|name",
            "user_ids|3|company_ids|1|name",
            "user_ids|3|company_ids|2|name",
            "user_ids|3|company_ids|3|name",
            "user_ids|3|company_ids|4|name",
            "user_ids|3|company_ids|5|name",
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
                "country_id|code": "US",
                "child_ids|1|country_id|code": "US",
            },
            {
                "id": "base.res_partner_2",
                "name": "Deco Addict",
                "street": "325 Elsie Drive",
                "country_id|code": "US",
                "child_ids|1|country_id|code": "US",
            },
            {
                "id": "base.res_partner_3",
                "name": "Gemini Furniture",
                "street": "1128 Lunetta Street",
                "country_id|code": "US",
                "child_ids|1|country_id|code": "US",
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
                "company_ids|1|name": "Awesome company",
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
            OrderedDict(
                {
                    "id": "base.user_root",
                    "name": "OdooBot",
                    "company_ids|1|name": "Awesome company",
                    "company_ids|2|name": "Bad company",
                    "company_ids|3|name": "YourCompany",
                }
            )
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
            OrderedDict(
                {
                    "id": "base.res_partner_1",
                    "name": "Wood Corner",
                    "user_ids|1|id": self.user1.get_xml_id().get(self.user1.id),
                    "user_ids|1|name": "Wood Corner",
                    "user_ids|1|company_ids|1|name": "Awesome company",
                }
            ),
            OrderedDict(
                {
                    "id": "base.res_partner_2",
                    "name": "Deco Addict",
                    "user_ids|1|id": self.user3.get_xml_id().get(self.user3.id),
                    "user_ids|1|name": "Deco Addict",
                    "user_ids|1|company_ids|1|name": "YourCompany",
                }
            ),
            OrderedDict({"id": "base.res_partner_3", "name": "Gemini Furniture"}),
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
            OrderedDict(
                {
                    "id": "base.res_partner_1",
                    "name": "Wood Corner",
                    "user_ids|1|id": self.user1.get_xml_id().get(self.user1.id),
                    "user_ids|1|name": "Wood Corner",
                    "user_ids|1|company_ids|1|name": "Awesome company",
                    "user_ids|1|company_ids|2|name": "Bad company",
                    "user_ids|1|company_ids|3|name": "YourCompany",
                }
            ),
            OrderedDict(
                {
                    "id": "base.res_partner_2",
                    "name": "Deco Addict",
                    "user_ids|1|id": self.user3.get_xml_id().get(self.user3.id),
                    "user_ids|1|name": "Deco Addict",
                    "user_ids|1|company_ids|1|name": "YourCompany",
                }
            ),
            OrderedDict({"id": "base.res_partner_3", "name": "Gemini Furniture"}),
        ]
        results = self.ir_exports_o2m._get_data_to_export(self.partners)
        for result, expected_result in zip(results, expected_results):
            self.assertDictEqual(expected_result, result)
