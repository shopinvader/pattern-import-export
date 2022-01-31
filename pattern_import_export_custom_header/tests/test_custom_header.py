# Copyright (C) 2022 Akretion (<http://www.akretion.com>).
# @author Kévin Roche <kevin.roche@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import SavepointCase

from odoo.addons.pattern_import_export.tests.common import PatternCommon


class TestCustomHeader(PatternCommon, SavepointCase):
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

        self.pattern_config.use_custom_header = True
        self.pattern_config.generate_custom_header_field()
        self.assertEqual(
            len(expected_header), len(self.pattern_config.custom_header_field_name_ids)
        )

        new_custom_names = [
            "custom_1",
            "custom_2",
            "custom_3",
            "custom_4",
            "custom_5",
        ]
        for count, _enum in enumerate(new_custom_names):
            self.pattern_config.custom_header_field_name_ids[
                count
            ].custom_name = new_custom_names[count]
        headers = self.pattern_config._get_header()
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

        self.pattern_config_m2m.use_custom_header = True
        self.pattern_config_m2m.generate_custom_header_field()
        self.assertEqual(
            len(expected_header),
            len(self.pattern_config_m2m.custom_header_field_name_ids),
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
        self.pattern_config_m2m.custom_header_field_name_ids[
            2
        ].custom_name = expected_new_header[2]
        self.pattern_config_m2m.custom_header_field_name_ids[
            4
        ].custom_name = expected_new_header[4]
        self.pattern_config_m2m.custom_header_field_name_ids[
            6
        ].custom_name = expected_new_header[6]
        headers = self.pattern_config_m2m._get_header()
        self.assertEqual(headers, expected_new_header)

    def test_3_o2m_custom_headers(self):
        self.pattern_config_o2m.use_custom_header = True
        self.pattern_config_o2m.generate_custom_header_field()
        headers = self.pattern_config_o2m._get_header()
        self.assertEqual(
            len(headers), len(self.pattern_config_o2m.custom_header_field_name_ids)
        )

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
        self.pattern_config.use_custom_header = True
        self.pattern_config.generate_custom_header_field()
        self.pattern_config.custom_header_field_name_ids.create(
            {"custom_name": "addition 1", "pattern_id": self.pattern_config.id}
        )
        self.pattern_config.custom_header_field_name_ids.create(
            {"custom_name": "addition 2", "pattern_id": self.pattern_config.id}
        )

        headers = self.pattern_config._get_header()
        self.assertEqual(expected_header, headers)

    def test_5_add_new_initial_headers(self):
        expected_header = [
            ".id",
            "name",
            "street",
            "country_id|code",
            "category_id|1|name",
        ]

        headers = self.pattern_config._get_header()
        self.pattern_config.use_custom_header = True
        self.pattern_config.generate_custom_header_field()
        self.pattern_config.custom_header_field_name_ids.create(
            {"custom_name": "addition 1", "pattern_id": self.pattern_config.id}
        )
        self.pattern_config.custom_header_field_name_ids[1].custom_name = "custom_1"

        self.pattern_config.generate_custom_header_field()
        headers = self.pattern_config._get_header()
        # Empty column with only custom header name will be remove
        self.assertEqual(len(expected_header), len(headers))
        # Filled custom_name are saved
        self.assertEqual(
            self.pattern_config.custom_header_field_name_ids[1].custom_name, "custom_1"
        )
