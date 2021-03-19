# Copyright 2020 Akretion France (http://www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo.tests.common import SavepointCase

from .common import PatternCommon


class TestPatternExport(PatternCommon, SavepointCase):
    def test_get_header1(self):
        """
        Ensure the header is correctly generated
        @return:
        """
        headers = self.pattern_config._get_header()
        expected_header = [
            ".id",
            "name",
            "street",
            "country_id|code",
            "parent_id|country_id|code",
        ]
        self.assertEqual(expected_header, headers)

    def test_get_header1_descriptive(self):
        headers = self.pattern_config._get_header(use_description=True)
        expected_header = [
            "ID",
            "Name",
            "Street",
            "Country|Country Code",
            "Related Company|Country|Country Code",
        ]
        self.assertEqual(expected_header, headers)

    def test_get_header2(self):
        """
        Ensure the header is correctly generated in case of M2M with 1 occurrence
        @return:
        """
        headers = self.pattern_config_m2m._get_header()
        expected_header = [".id", "name", "company_ids|1|name"]
        self.assertEqual(expected_header, headers)

    def test_get_header3(self):
        """
        Ensure the header is correctly generated in case of M2M more than 1 occurrence
        @return:
        """
        export_fields_m2m = self.env.ref("pattern_import_export.demo_export_m2m_line_3")
        export_fields_m2m.write({"number_occurence": 5})
        headers = self.pattern_config_m2m._get_header()
        expected_header = [
            ".id",
            "name",
            "company_ids|1|name",
            "company_ids|2|name",
            "company_ids|3|name",
            "company_ids|4|name",
            "company_ids|5|name",
        ]
        self.assertEqual(expected_header, headers)

    def test_get_header4(self):
        """
        Ensure the header is correctly generated in case of O2M.
        This O2M contains a sub-pattern whith a M2M with 1 occurrence.
        @return:
        """
        headers = self.pattern_config_o2m._get_header()
        expected_header = [
            ".id",
            "name",
            "user_ids|1|.id",
            "user_ids|1|name",
            "user_ids|1|company_ids|1|name",
            "user_ids|2|.id",
            "user_ids|2|name",
            "user_ids|2|company_ids|1|name",
            "user_ids|3|.id",
            "user_ids|3|name",
            "user_ids|3|company_ids|1|name",
        ]
        self.assertEqual(expected_header, headers)

    def test_get_header5(self):
        """
        Ensure the header is correctly generated in case of O2M.
        For this case, the O2M contains a sub-pattern with a M2M with more
        than 1 occurrence
        @return:
        """
        export_fields_m2m = self.env.ref("pattern_import_export.demo_export_m2m_line_3")
        export_fields_m2m.write({"number_occurence": 5})
        headers = self.pattern_config_o2m._get_header()
        expected_header = [
            ".id",
            "name",
            "user_ids|1|.id",
            "user_ids|1|name",
            "user_ids|1|company_ids|1|name",
            "user_ids|1|company_ids|2|name",
            "user_ids|1|company_ids|3|name",
            "user_ids|1|company_ids|4|name",
            "user_ids|1|company_ids|5|name",
            "user_ids|2|.id",
            "user_ids|2|name",
            "user_ids|2|company_ids|1|name",
            "user_ids|2|company_ids|2|name",
            "user_ids|2|company_ids|3|name",
            "user_ids|2|company_ids|4|name",
            "user_ids|2|company_ids|5|name",
            "user_ids|3|.id",
            "user_ids|3|name",
            "user_ids|3|company_ids|1|name",
            "user_ids|3|company_ids|2|name",
            "user_ids|3|company_ids|3|name",
            "user_ids|3|company_ids|4|name",
            "user_ids|3|company_ids|5|name",
        ]
        self.assertEqual(expected_header, headers)

    def test_get_data_to_export1(self):
        """
        Ensure the _get_data_to_export return expected data
        @return:
        """
        expected_results = [
            {
                ".id": self.partner_1.id,
                "name": "Wood Corner",
                "street": "1839 Arbor Way",
                "country_id|code": "US",
                "parent_id|country_id|code": None,
            },
            {
                ".id": self.partner_2.id,
                "name": "Deco Addict",
                "street": "77 Santa Barbara Rd",
                "country_id|code": "US",
                "parent_id|country_id|code": None,
            },
            {
                ".id": self.partner_3.id,
                "name": "Gemini Furniture",
                "street": "317 Fairchild Dr",
                "country_id|code": "US",
                "parent_id|country_id|code": None,
            },
        ]
        results = self.pattern_config._get_data_to_export(self.partners)
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
                ".id": self.env.user.id,
                "name": "OdooBot",
                "company_ids|1|name": "Awesome company",
            }
        ]
        results = self.pattern_config_m2m._get_data_to_export(self.env.user)
        for result, expected_result in zip(results, expected_results):
            self.assertDictEqual(expected_result, result)

    def test_get_data_to_export3(self):
        """
        Ensure the _get_data_to_export return expected data with M2M with more
        than 1 occurrence.
        @return:
        """
        export_fields_m2m = self.env.ref("pattern_import_export.demo_export_m2m_line_3")
        export_fields_m2m.write({"number_occurence": 5})
        expected_results = [
            {
                ".id": self.env.user.id,
                "name": "OdooBot",
                "company_ids|1|name": "Awesome company",
                "company_ids|2|name": "Bad company",
                "company_ids|3|name": "Ignored company",
                "company_ids|4|name": "YourCompany",
                "company_ids|5|name": None,
            }
        ]
        results = self.pattern_config_m2m._get_data_to_export(self.env.user)
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
                ".id": self.partner_1.id,
                "name": "Wood Corner",
                "user_ids|1|.id": self.user2.id,
                "user_ids|1|name": "Wood Corner",
                "user_ids|1|company_ids|1|name": "Awesome company",
                "user_ids|2|.id": self.user1.id,
                "user_ids|2|name": "Wood Corner",
                "user_ids|2|company_ids|1|name": "Awesome company",
                "user_ids|3|.id": None,
                "user_ids|3|name": None,
                "user_ids|3|company_ids|1|name": None,
            },
            {
                ".id": self.partner_2.id,
                "name": "Deco Addict",
                "user_ids|1|.id": self.user3.id,
                "user_ids|1|name": "Deco Addict",
                "user_ids|1|company_ids|1|name": "YourCompany",
                "user_ids|2|.id": None,
                "user_ids|2|name": None,
                "user_ids|2|company_ids|1|name": None,
                "user_ids|3|.id": None,
                "user_ids|3|name": None,
                "user_ids|3|company_ids|1|name": None,
            },
            {
                ".id": self.partner_3.id,
                "name": "Gemini Furniture",
                "user_ids|1|.id": None,
                "user_ids|1|name": None,
                "user_ids|1|company_ids|1|name": None,
                "user_ids|2|.id": None,
                "user_ids|2|name": None,
                "user_ids|2|company_ids|1|name": None,
                "user_ids|3|.id": None,
                "user_ids|3|name": None,
                "user_ids|3|company_ids|1|name": None,
            },
        ]
        results = self.pattern_config_o2m._get_data_to_export(self.partners)
        for result, expected_result in zip(results, expected_results):
            self.assertDictEqual(expected_result, result)

    def test_get_data_to_export5(self):
        """
        Ensure the _get_data_to_export return expected data with O2M with a
        M2M who contains more than 1 occurrence.
        @return:
        """
        export_fields_m2m = self.env.ref("pattern_import_export.demo_export_m2m_line_3")
        export_fields_m2m.write({"number_occurence": 3})
        export_fields_o2m = self.env.ref("pattern_import_export.demo_export_o2m_line_3")
        export_fields_o2m.write({"number_occurence": 2})
        expected_results = [
            {
                ".id": self.partner_1.id,
                "name": "Wood Corner",
                "user_ids|1|.id": self.user2.id,
                "user_ids|1|name": "Wood Corner",
                "user_ids|1|company_ids|1|name": "Awesome company",
                "user_ids|1|company_ids|2|name": "YourCompany",
                "user_ids|1|company_ids|3|name": None,
                "user_ids|2|.id": self.user1.id,
                "user_ids|2|name": "Wood Corner",
                "user_ids|2|company_ids|1|name": "Awesome company",
                "user_ids|2|company_ids|2|name": "Bad company",
                "user_ids|2|company_ids|3|name": "YourCompany",
            },
            {
                ".id": self.partner_2.id,
                "name": "Deco Addict",
                "user_ids|1|.id": self.user3.id,
                "user_ids|1|name": "Deco Addict",
                "user_ids|1|company_ids|1|name": "YourCompany",
                "user_ids|1|company_ids|2|name": None,
                "user_ids|1|company_ids|3|name": None,
                "user_ids|2|.id": None,
                "user_ids|2|name": None,
                "user_ids|2|company_ids|1|name": None,
                "user_ids|2|company_ids|2|name": None,
                "user_ids|2|company_ids|3|name": None,
            },
            {
                ".id": self.partner_3.id,
                "name": "Gemini Furniture",
                "user_ids|1|.id": None,
                "user_ids|1|name": None,
                "user_ids|1|company_ids|1|name": None,
                "user_ids|1|company_ids|2|name": None,
                "user_ids|1|company_ids|3|name": None,
                "user_ids|2|.id": None,
                "user_ids|2|name": None,
                "user_ids|2|company_ids|1|name": None,
                "user_ids|2|company_ids|2|name": None,
                "user_ids|2|company_ids|3|name": None,
            },
        ]
        results = self.pattern_config_o2m._get_data_to_export(self.partners)
        for result, expected_result in zip(results, expected_results):
            self.assertDictEqual(expected_result, result)

    def test_get_data_to_export_is_key1(self):
        """
        Ensure the _get_data_to_export return expected data with correct header
        when export line are considered as key
        @return:
        """
        expected_results = [
            {
                ".id": self.partner_1.id,
                "name#key": "Wood Corner",
                "street": "1839 Arbor Way",
                "country_id#key|code": "US",
                "parent_id|country_id|code": None,
            },
            {
                ".id": self.partner_2.id,
                "name#key": "Deco Addict",
                "street": "77 Santa Barbara Rd",
                "country_id#key|code": "US",
                "parent_id|country_id|code": None,
            },
            {
                ".id": self.partner_3.id,
                "name#key": "Gemini Furniture",
                "street": "317 Fairchild Dr",
                "country_id#key|code": "US",
                "parent_id|country_id|code": None,
            },
        ]
        self.env.ref("pattern_import_export.demo_export_line_2").write({"is_key": True})
        self.env.ref("pattern_import_export.demo_export_line_4").write({"is_key": True})
        results = self.pattern_config._get_data_to_export(self.partners)
        for result, expected_result in zip(results, expected_results):
            self.assertDictEqual(expected_result, result)
