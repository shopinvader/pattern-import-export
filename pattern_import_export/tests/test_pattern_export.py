# Copyright 2020 Akretion France (http://www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo.tests.common import SavepointCase

from .common import PatternCommon


class PatternCaseExport:
    def _get_header(self, pattern_config, use_description=False):
        raise NotImplementedError

    def _get_data(self, pattern_config, records):
        raise NotImplementedError

    def test_get_header1(self):
        """
        Ensure the header is correctly generated
        @return:
        """
        headers = self._get_header(self.pattern_config)
        expected_header = [
            ".id",
            "name",
            "street",
            "country_id|code",
            "category_id|1|name",
        ]
        self.assertEqual(expected_header, headers)

    def test_get_header1_descriptive(self):
        headers = self._get_header(self.pattern_config, use_description=True)
        expected_header = [
            "ID",
            "Name",
            "Street",
            "Country|Country Code",
            "Tags|1|Tag Name",
        ]
        self.assertEqual(expected_header, headers)

    def test_get_header2(self):
        """
        Ensure the header is correctly generated in case of M2M with 1 occurrence
        @return:
        """
        headers = self._get_header(self.pattern_config_m2m)
        expected_header = [".id", "name", "company_ids|1|name"]
        self.assertEqual(expected_header, headers)

    def test_get_header3(self):
        """
        Ensure the header is correctly generated in case of M2M more than 1 occurrence
        @return:
        """
        export_fields_m2m = self.env.ref("pattern_import_export.demo_export_m2m_line_3")
        export_fields_m2m.write({"number_occurence": 5})
        headers = self._get_header(self.pattern_config_m2m)
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
        headers = self._get_header(self.pattern_config_o2m)
        expected_header = [
            ".id",
            "name",
            "child_ids|1|.id",
            "child_ids|1|name",
            "child_ids|1|street",
            "child_ids|1|country_id|code",
            "child_ids|1|category_id|1|name",
            "child_ids|2|.id",
            "child_ids|2|name",
            "child_ids|2|street",
            "child_ids|2|country_id|code",
            "child_ids|2|category_id|1|name",
            "child_ids|3|.id",
            "child_ids|3|name",
            "child_ids|3|street",
            "child_ids|3|country_id|code",
            "child_ids|3|category_id|1|name",
            "country_id|code",
        ]
        self.assertEqual(expected_header, headers)

    def test_get_header5(self):
        """
        Ensure the header is correctly generated in case of O2M.
        For this case, the O2M contains a sub-pattern with a M2M with more
        than 1 occurrence
        @return:
        """
        export_fields_m2m = self.env.ref("pattern_import_export.demo_export_line_5")
        export_fields_m2m.write({"number_occurence": 5})
        headers = self._get_header(self.pattern_config_o2m)
        expected_header = [
            ".id",
            "name",
            "child_ids|1|.id",
            "child_ids|1|name",
            "child_ids|1|street",
            "child_ids|1|country_id|code",
            "child_ids|1|category_id|1|name",
            "child_ids|1|category_id|2|name",
            "child_ids|1|category_id|3|name",
            "child_ids|1|category_id|4|name",
            "child_ids|1|category_id|5|name",
            "child_ids|2|.id",
            "child_ids|2|name",
            "child_ids|2|street",
            "child_ids|2|country_id|code",
            "child_ids|2|category_id|1|name",
            "child_ids|2|category_id|2|name",
            "child_ids|2|category_id|3|name",
            "child_ids|2|category_id|4|name",
            "child_ids|2|category_id|5|name",
            "child_ids|3|.id",
            "child_ids|3|name",
            "child_ids|3|street",
            "child_ids|3|country_id|code",
            "child_ids|3|category_id|1|name",
            "child_ids|3|category_id|2|name",
            "child_ids|3|category_id|3|name",
            "child_ids|3|category_id|4|name",
            "child_ids|3|category_id|5|name",
            "country_id|code",
        ]
        self.assertEqual(expected_header, headers)

    def test_get_data_to_export1(self):
        """
        Ensure the _get_data_to_export return expected data
        @return:
        """
        results = self._get_data(self.pattern_config, self.partners)
        expected_results = [
            {
                ".id": self.partner_1.id,
                "name": "Wood Corner",
                "street": "1839 Arbor Way",
                "country_id|code": "US",
                "category_id|1|name": "Desk Manufacturers",
            },
            {
                ".id": self.partner_2.id,
                "name": "Deco Addict",
                "street": "77 Santa Barbara Rd",
                "country_id|code": "US",
                "category_id|1|name": "Desk Manufacturers",
            },
            {
                ".id": self.partner_3.id,
                "name": "Gemini Furniture",
                "street": "317 Fairchild Dr",
                "country_id|code": "US",
                "category_id|1|name": "Consulting Services",
            },
        ]
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
        results = self._get_data(self.pattern_config_m2m, self.env.user)
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
        results = self._get_data(self.pattern_config_m2m, self.env.user)
        for result, expected_result in zip(results, expected_results):
            self.assertDictEqual(expected_result, result)

    def test_get_data_to_export4(self):
        """
        Ensure the _get_data_to_export return expected data with O2M with a
        M2M who contains only 1 occurrence.
        @return:
        """
        p1c = self.partner_1.child_ids
        p2c = self.partner_2.child_ids
        p3c = self.partner_3.child_ids
        expected_results = [
            {
                ".id": self.partner_1.id,
                "name": "Wood Corner",
                "child_ids|1|.id": p1c[0].id,
                "child_ids|1|name": "Ron Gibson",
                "child_ids|1|street": "1839 Arbor Way",
                "child_ids|1|country_id|code": "US",
                "child_ids|1|category_id|1|name": None,
                "child_ids|2|.id": p1c[1].id,
                "child_ids|2|name": "Tom Ruiz",
                "child_ids|2|street": "1839 Arbor Way",
                "child_ids|2|country_id|code": "US",
                "child_ids|2|category_id|1|name": None,
                "child_ids|3|.id": p1c[2].id,
                "child_ids|3|name": "Willie Burke",
                "child_ids|3|street": "1839 Arbor Way",
                "child_ids|3|country_id|code": "US",
                "child_ids|3|category_id|1|name": None,
                "country_id|code": "US",
            },
            {
                ".id": self.partner_2.id,
                "name": "Deco Addict",
                "child_ids|1|.id": p2c[0].id,
                "child_ids|1|name": "Addison Olson",
                "child_ids|1|street": "77 Santa Barbara Rd",
                "child_ids|1|country_id|code": "US",
                "child_ids|1|category_id|1|name": None,
                "child_ids|2|.id": p2c[1].id,
                "child_ids|2|name": "Douglas Fletcher",
                "child_ids|2|street": "77 Santa Barbara Rd",
                "child_ids|2|country_id|code": "US",
                "child_ids|2|category_id|1|name": None,
                "child_ids|3|.id": p2c[2].id,
                "child_ids|3|name": "Floyd Steward",
                "child_ids|3|street": "77 Santa Barbara Rd",
                "child_ids|3|country_id|code": "US",
                "child_ids|3|category_id|1|name": None,
                "country_id|code": "US",
            },
            {
                ".id": self.partner_3.id,
                "name": "Gemini Furniture",
                "child_ids|1|.id": p3c[0].id,
                "child_ids|1|name": "Edwin Hansen",
                "child_ids|1|street": "317 Fairchild Dr",
                "child_ids|1|country_id|code": "US",
                "child_ids|1|category_id|1|name": None,
                "child_ids|2|.id": p3c[1].id,
                "child_ids|2|name": "Jesse Brown",
                "child_ids|2|street": "317 Fairchild Dr",
                "child_ids|2|country_id|code": "US",
                "child_ids|2|category_id|1|name": None,
                "child_ids|3|.id": p3c[2].id,
                "child_ids|3|name": "Oscar Morgan",
                "child_ids|3|street": "317 Fairchild Dr",
                "child_ids|3|country_id|code": "US",
                "child_ids|3|category_id|1|name": None,
                "country_id|code": "US",
            },
        ]
        results = self._get_data(self.pattern_config_o2m, self.partners)
        for result, expected_result in zip(results, expected_results):
            self.assertDictEqual(expected_result, result)

    def test_get_data_to_export5(self):
        """
        Ensure the _get_data_to_export return expected data with O2M with a
        M2M who contains more than 1 occurrence.
        @return:
        """
        export_fields_m2m = self.env.ref("pattern_import_export.demo_export_line_5")
        export_fields_m2m.write({"number_occurence": 3})
        export_fields_o2m = self.env.ref("pattern_import_export.demo_export_o2m_line_3")
        export_fields_o2m.write({"number_occurence": 2})
        p1c = self.partner_1.child_ids
        p2c = self.partner_2.child_ids
        p3c = self.partner_3.child_ids
        expected_results = [
            {
                ".id": self.partner_1.id,
                "name": "Wood Corner",
                "child_ids|1|.id": p1c[0].id,
                "child_ids|1|name": "Ron Gibson",
                "child_ids|1|street": "1839 Arbor Way",
                "child_ids|1|country_id|code": "US",
                "child_ids|1|category_id|1|name": None,
                "child_ids|1|category_id|2|name": None,
                "child_ids|1|category_id|3|name": None,
                "child_ids|2|.id": p1c[1].id,
                "child_ids|2|name": "Tom Ruiz",
                "child_ids|2|street": "1839 Arbor Way",
                "child_ids|2|country_id|code": "US",
                "child_ids|2|category_id|1|name": None,
                "child_ids|2|category_id|2|name": None,
                "child_ids|2|category_id|3|name": None,
                "country_id|code": "US",
            },
            {
                ".id": self.partner_2.id,
                "name": "Deco Addict",
                "child_ids|1|.id": p2c[0].id,
                "child_ids|1|name": "Addison Olson",
                "child_ids|1|street": "77 Santa Barbara Rd",
                "child_ids|1|country_id|code": "US",
                "child_ids|1|category_id|1|name": None,
                "child_ids|1|category_id|2|name": None,
                "child_ids|1|category_id|3|name": None,
                "child_ids|2|.id": p2c[1].id,
                "child_ids|2|name": "Douglas Fletcher",
                "child_ids|2|street": "77 Santa Barbara Rd",
                "child_ids|2|country_id|code": "US",
                "child_ids|2|category_id|1|name": None,
                "child_ids|2|category_id|2|name": None,
                "child_ids|2|category_id|3|name": None,
                "country_id|code": "US",
            },
            {
                ".id": self.partner_3.id,
                "name": "Gemini Furniture",
                "child_ids|1|.id": p3c[0].id,
                "child_ids|1|name": "Edwin Hansen",
                "child_ids|1|street": "317 Fairchild Dr",
                "child_ids|1|country_id|code": "US",
                "child_ids|1|category_id|1|name": None,
                "child_ids|1|category_id|2|name": None,
                "child_ids|1|category_id|3|name": None,
                "child_ids|2|.id": p3c[1].id,
                "child_ids|2|name": "Jesse Brown",
                "child_ids|2|street": "317 Fairchild Dr",
                "child_ids|2|country_id|code": "US",
                "child_ids|2|category_id|1|name": None,
                "child_ids|2|category_id|2|name": None,
                "child_ids|2|category_id|3|name": None,
                "country_id|code": "US",
            },
        ]

        results = self._get_data(self.pattern_config_o2m, self.partners)
        for result, expected_result in zip(results, expected_results):
            self.assertDictEqual(expected_result, result)

    def test_get_data_to_export_is_key1(self):
        """
        Ensure the _get_data_to_export return expected data with correct header
        when export line are considered as key
        @return:
        """
        self.env.ref("pattern_import_export.demo_export_line_2").write({"is_key": True})
        self.env.ref("pattern_import_export.demo_export_line_4").write({"is_key": True})
        results = self._get_data(self.pattern_config, self.partners)
        for result in results:
            self.assertNotIn("name", result)
            self.assertIn("name#key", result)
            self.assertNotIn("country_id|code", result)
            self.assertIn("country_id#key|code", result)


class PatternTestExport(PatternCommon, SavepointCase, PatternCaseExport):
    def _get_header(self, pattern_config, use_description=False):
        return pattern_config._get_header(use_description=use_description)

    def _get_data(self, pattern_config, records):
        return pattern_config._get_data_to_export(records)

    def test_get_metadata(self):
        result = self.pattern_config_o2m._get_metadata()
        self.assertEqual(len(result["tabs"]), 2)
        tabs = result["tabs"]
        tab_country_name = (
            f"({self.filter_countries_1.id}) {self.filter_countries_1.name}"
        )
        self.assertEqual(list(tabs.keys()), [tab_country_name, "Tags"])
        self.assertEqual(
            tabs[tab_country_name],
            {
                "headers": ["code"],
                "data": [["BE"], ["FR"], ["US"]],
                "idx_col_validator": [6, 11, 16, 18],
            },
        )
        self.assertEqual(
            tabs["Tags"],
            {
                "headers": ["name"],
                "data": [
                    ["Consulting Services"],
                    ["Desk Manufacturers"],
                    ["Employees"],
                    ["Office Supplies"],
                    ["Prospects"],
                    ["Services"],
                    ["Vendor"],
                ],
                "idx_col_validator": [7, 12, 17],
            },
        )
