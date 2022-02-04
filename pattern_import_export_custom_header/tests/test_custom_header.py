# Copyright (C) 2022 Akretion (<http://www.akretion.com>).
# @author Kévin Roche <kevin.roche@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import SavepointCase

from odoo.addons.pattern_import_export.tests.common import PatternCommon


class TestCustomHeader(PatternCommon, SavepointCase):
    def _get_data(self, pattern_config, records):
        return pattern_config._get_data_to_export(records)

    def test_1_all_custom_headers(self):
        expected_header = [
            ".id",
            "name",
            "street",
            "country_id|code",
            "category_id|1|name",
        ]

        headers = self.pattern_config._get_header()
        self.assertEqual(expected_header, headers)

        self.pattern_config.header_format = "custom"
        self.pattern_config.generate_custom_header_field()
        self.assertEqual(
            len(expected_header), len(self.pattern_config.custom_header_ids)
        )

        new_custom_names = [
            "custom_1",
            "custom_2",
            "custom_3",
            "custom_4",
            "custom_5",
        ]
        for count, _enum in enumerate(new_custom_names):
            self.pattern_config.custom_header_ids[count].custom_name = new_custom_names[
                count
            ]
        headers = list(self.pattern_config._get_output_headers()[0].keys())
        self.assertEqual(headers, new_custom_names)

    def test_2_m2m_and_few_custom_headers(self):
        export_fields_m2m = self.env.ref("pattern_import_export.demo_export_m2m_line_3")
        export_fields_m2m.write({"number_occurence": 5})
        expected_header = [
            ".id",
            "name",
            "company_ids|1|name",
            "company_ids|2|name",
            "company_ids|3|name",
            "company_ids|4|name",
            "company_ids|5|name",
        ]
        headers = self.pattern_config_m2m._get_header()
        self.assertEqual(expected_header, headers)

        self.pattern_config_m2m.header_format = "custom"
        self.pattern_config_m2m.generate_custom_header_field()
        self.assertEqual(
            len(expected_header),
            len(self.pattern_config_m2m.custom_header_ids),
        )

        expected_new_header = [
            ".id",
            "name",
            "first_company_name",
            "company_ids|2|name",
            "middle_comany_name",
            "company_ids|4|name",
            "last_company_name",
        ]
        self.pattern_config_m2m.custom_header_ids[2].custom_name = expected_new_header[
            2
        ]
        self.pattern_config_m2m.custom_header_ids[4].custom_name = expected_new_header[
            4
        ]
        self.pattern_config_m2m.custom_header_ids[6].custom_name = expected_new_header[
            6
        ]
        headers = list(self.pattern_config_m2m._get_output_headers()[0].keys())
        self.assertEqual(headers, expected_new_header)

    def test_3_o2m_custom_headers(self):
        self.pattern_config_o2m.header_format = "custom"
        self.pattern_config_o2m.generate_custom_header_field()
        headers = list(self.pattern_config_o2m._get_output_headers()[0].keys())
        self.assertEqual(len(headers), len(self.pattern_config_o2m.custom_header_ids))

    def test_4_add_empty_columns(self):
        expected_header = [
            ".id",
            "name",
            "street",
            "country_id|code",
            "category_id|1|name",
            "addition 1",
            "addition 2",
        ]
        self.pattern_config.header_format = "custom"
        self.pattern_config.generate_custom_header_field()
        self.pattern_config.custom_header_ids.create(
            {"custom_name": "addition 1", "pattern_id": self.pattern_config.id}
        )
        self.pattern_config.custom_header_ids.create(
            {"custom_name": "addition 2", "pattern_id": self.pattern_config.id}
        )

        headers = list(self.pattern_config._get_output_headers()[0].keys())
        self.assertEqual(expected_header, headers)

    def test_5_add_new_initial_headers(self):
        headers = self.pattern_config._get_header()
        self.pattern_config.header_format = "custom"
        self.pattern_config.generate_custom_header_field()
        self.pattern_config.custom_header_ids.create(
            {"custom_name": "addition 1", "pattern_id": self.pattern_config.id}
        )
        self.pattern_config.custom_header_ids[1].custom_name = "custom_1"

        self.pattern_config.generate_custom_header_field()
        headers = list(self.pattern_config._get_output_headers()[0].keys())
        # Empty column with only custom header name is kept
        self.assertEqual(6, len(headers))
        # Filled custom_name are saved
        self.assertEqual(
            self.pattern_config.custom_header_ids[1].custom_name, "custom_1"
        )

    def test_6_data_export_with_custom_header(self):
        new_custom_names = [
            "custom_1",
            "custom_2",
            "custom_3",
            "custom_4",
            "custom_5",
        ]
        self.pattern_config.header_format = "custom"
        self.pattern_config.generate_custom_header_field()
        for count, _enum in enumerate(new_custom_names):
            self.pattern_config.custom_header_ids[count].custom_name = new_custom_names[
                count
            ]

        self.pattern_config.custom_header_ids.create(
            {"custom_name": "addition 1", "pattern_id": self.pattern_config.id}
        )
        new_custom_names.append("addition 1")
        headers = list(self.pattern_config._get_output_headers()[0].keys())
        self.assertEqual(new_custom_names, headers)

        results = self._get_data(self.pattern_config, self.partners)
        expected_results = [
            {
                "custom_1": self.partner_1.id,
                "custom_2": "Wood Corner",
                "custom_3": "1839 Arbor Way",
                "custom_4": "US",
                "custom_5": "Desk Manufacturers",
                "addition 1": None,
            },
            {
                "custom_1": self.partner_2.id,
                "custom_2": "Deco Addict",
                "custom_3": "77 Santa Barbara Rd",
                "custom_4": "US",
                "custom_5": "Desk Manufacturers",
                "addition 1": None,
            },
            {
                "custom_1": self.partner_3.id,
                "custom_2": "Gemini Furniture",
                "custom_3": "317 Fairchild Dr",
                "custom_4": "US",
                "custom_5": "Consulting Services",
                "addition 1": None,
            },
        ]
        for result, expected_result in zip(results, expected_results):
            self.assertDictEqual(expected_result, result)

    def test_7_data_export_custom_header_in_different_order(self):
        new_custom_names = [
            "custom_0",
            "custom_1",
            "custom_2",
            "custom_3",
            "custom_4",
        ]
        self.pattern_config.header_format = "custom"
        self.pattern_config.generate_custom_header_field()
        for count, _enum in enumerate(new_custom_names):
            self.pattern_config.custom_header_ids[count].custom_name = new_custom_names[
                count
            ]

        header = self.pattern_config.custom_header_ids
        header[0].write({"sequence": 0})
        header[1].write({"sequence": 4})
        header[2].write({"sequence": 3})
        header[3].write({"sequence": 2})
        header[4].write({"sequence": 1})

        results = self._get_data(self.pattern_config, self.partners)
        expected_results = [
            {
                "custom_0": self.partner_1.id,
                "custom_4": "Desk Manufacturers",
                "custom_3": "US",
                "custom_2": "1839 Arbor Way",
                "custom_1": "Wood Corner",
            },
            {
                "custom_0": self.partner_2.id,
                "custom_4": "Desk Manufacturers",
                "custom_3": "US",
                "custom_2": "77 Santa Barbara Rd",
                "custom_1": "Deco Addict",
            },
            {
                "custom_0": self.partner_3.id,
                "custom_4": "Consulting Services",
                "custom_3": "US",
                "custom_2": "317 Fairchild Dr",
                "custom_1": "Gemini Furniture",
            },
        ]
        for result, expected_result in zip(results, expected_results):
            self.assertDictEqual(expected_result, result)
