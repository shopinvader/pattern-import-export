# Copyright 2020 Akretion France (http://www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
# pylint: disable=missing-manifest-dependency

import base64
from os import path

# pylint: disable=odoo-addons-relative-import
from .common import ExportPatternCsvCommon

DEBUG_SAVE_EXPORTS = False

PATH = path.dirname(__file__)
CELL_VALUE_EMPTY = ""


class TestPatternExportCsv(ExportPatternCsvCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.pattern_config = cls.env.ref(
            "pattern_import_export_csv.demo_pattern_config_csv"
        )
        cls.pattern_config_m2m = cls.env.ref(
            "pattern_import_export_csv.demo_pattern_config_m2m_csv"
        )
        cls.pattern_config_o2m = cls.env.ref(
            "pattern_import_export_csv.demo_pattern_config_o2m_csv"
        )

    def _helper_get_resulting_csv(self, export, records):
        export._export_with_record(records)
        attachment = self._get_attachment(export)
        self.assertEqual(attachment.name, export.name + ".csv")
        decoded_data = base64.b64decode(attachment.datas).decode("utf-8")
        if DEBUG_SAVE_EXPORTS:
            full_path = PATH + export.name + ".csv"
            with open(full_path, "wt") as out:
                out.write(decoded_data)
        return self._split_csv_str(decoded_data, export)

    def test_export_headers(self):
        csv_file_lines = self._helper_get_resulting_csv(
            self.pattern_config, self.partners
        )
        expected_content = [
            ".id",
            "name",
            "street",
            "country_id|code",
            "parent_id|country_id|code",
        ]
        self.assertEqual(csv_file_lines[0], expected_content)

    def test_export_headers_fmt2(self):
        self.pattern_config.csv_value_delimiter = "²"
        self.pattern_config.csv_quote_character = "%"
        csv_file_lines = self._helper_get_resulting_csv(
            self.pattern_config, self.partners
        )
        expected_content = [
            ".id",
            "name",
            "street",
            "country_id|code",
            "parent_id|country_id|code",
        ]
        self.assertEqual(csv_file_lines[0], expected_content)

    def test_export_headers_descriptive(self):
        self.pattern_config.header_format = "description_and_tech"
        csv_file_lines = self._helper_get_resulting_csv(
            self.pattern_config, self.partners
        )
        expected_headers = [
            "ID",
            "Name",
            "Street",
            "Country|Country Code",
            "Related Company|Country|Country Code",
        ]
        self.assertEqual(csv_file_lines[0], expected_headers)

    def test_export_vals(self):
        csv_file_lines = self._helper_get_resulting_csv(
            self.pattern_config, self.partners
        )
        id1 = self.env.ref("base.res_partner_1").id
        id2 = self.env.ref("base.res_partner_2").id
        id3 = self.env.ref("base.res_partner_3").id
        expected_content = [
            [str(id1), "Wood Corner", "1839 Arbor Way", "US", ""],
            [str(id2), "Deco Addict", "77 Santa Barbara Rd", "US", ""],
            [str(id3), "Gemini Furniture", "317 Fairchild Dr", "US", ""],
        ]
        self.assertEqual(csv_file_lines[1:4], expected_content)

    def test_export_m2m_headers(self):
        csv_file_lines = self._helper_get_resulting_csv(
            self.pattern_config_m2m, self.users
        )
        expected_headers = [".id", "name", "company_ids|1|name"]
        self.assertEqual(csv_file_lines[0], expected_headers)

    def test_export_m2m_values(self):
        csv_file_lines = self._helper_get_resulting_csv(
            self.pattern_config_m2m, self.users
        )
        expected_values = [
            [str(self.user1.id), "Wood Corner", "Awesome company"],
            [str(self.user2.id), "Wood Corner", "Awesome company"],
            [str(self.user3.id), "Deco Addict", "YourCompany"],
        ]
        self.assertEqual(csv_file_lines[1:4], expected_values)

    def test_export_o2m_headers(self):
        csv_file_lines = self._helper_get_resulting_csv(
            self.pattern_config_o2m, self.partners
        )
        expected_headers = [
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
        self.assertEqual(csv_file_lines[0], expected_headers)

    def test_export_o2m_values(self):
        csv_file_lines = self._helper_get_resulting_csv(
            self.pattern_config_o2m, self.partners
        )
        id1 = self.env.ref("base.res_partner_1").id
        id2 = self.env.ref("base.res_partner_2").id
        expected_values = [
            [
                str(id1),
                "Wood Corner",
                str(self.user2.id),
                str(self.user2.name),
                str(self.user2.company_ids[0].name),
                str(self.user1.id),
                str(self.user1.name),
                str(self.user1.company_ids[0].name),
                CELL_VALUE_EMPTY,
                CELL_VALUE_EMPTY,
                CELL_VALUE_EMPTY,
            ],
            [
                str(id2),
                "Deco Addict",
                str(self.user3.id),
                str(self.user3.name),
                str(self.user3.company_ids[0].name),
                CELL_VALUE_EMPTY,
                CELL_VALUE_EMPTY,
                CELL_VALUE_EMPTY,
                CELL_VALUE_EMPTY,
                CELL_VALUE_EMPTY,
                CELL_VALUE_EMPTY,
            ],
        ]
        self.assertEqual(csv_file_lines[1:3], expected_values)
