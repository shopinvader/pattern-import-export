# Copyright 2020 Akretion France (http://www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
# pylint: disable=missing-manifest-dependency

import base64
import csv
import io
from os import path
# pylint: disable=odoo-addons-relative-import
from odoo.addons.pattern_import_export.tests.common import ExportPatternCommon
from odoo.tests.common import SavepointCase

DEBUG_SAVE_EXPORTS = True

PATH = path.dirname(__file__)
CELL_VALUE_EMPTY = None


class TestPatternExportCsv(ExportPatternCommon, SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ir_exports = cls.env.ref("pattern_import_export_csv.demo_export_csv")
        cls.ir_exports_m2m = cls.env.ref("pattern_import_export_csv.demo_export_m2m_csv")
        cls.ir_exports_o2m = cls.env.ref("pattern_import_export_csv.demo_export_o2m_csv")

    def _helper_get_resulting_csv(self, export, records):
        export._export_with_record(records)
        attachment = self._get_attachment(export)
        self.assertEqual(attachment.name, export.name + ".csv")
        decoded_data = base64.b64decode(attachment.datas).decode("utf-8")
        if DEBUG_SAVE_EXPORTS:
            full_path = PATH + export.name + ".csv"
            with open(full_path, "wt") as out:
                out.write(decoded_data)
            # with open(full_path, "wt") as out:
            #     writer = csv.writer(out)
            #     writer.writerow(decoded_data)
        res = csv.reader(decoded_data, delimiter=",")
        for el in res:
            print(el)
        return


    def _helper_check_rows(self, reader, values):
        # skip header
        reader.__next__()
        for row in reader:
            self.assertEqual(row, values)

    def test_export_headers(self):
        reader = self._helper_get_resulting_csv(self.ir_exports, self.partners)
        expected_headers = [
            "id",
            "name",
            "street",
            "country_id|code",
            "parent_id|country_id|code",
        ]
        headers = reader.__next__()
        self.assertEqual(headers, expected_headers)

    def test_export_headers_descriptive(self):
        self.ir_exports.use_description = True
        reader = self._helper_get_resulting_csv(self.ir_exports, self.partners)
        expected_headers = [
            "ID",
            "Name",
            "Street",
            "Country|Country Code",
            "Related Company|Country|Country Code",
        ]
        headers = reader.__next__()
        self.assertEqual(headers, expected_headers)

    def test_export_vals(self):
        reader = self._helper_get_resulting_csv(self.ir_exports, self.partners)
        id1 = self.env.ref("base.res_partner_1").id
        id2 = self.env.ref("base.res_partner_2").id
        id3 = self.env.ref("base.res_partner_3").id
        expected_values = [
            [id1, "Wood Corner", "1164 Cambridge Drive", "US"],
            [id2, "Deco Addict", "325 Elsie Drive", "US"],
            [id3, "Gemini Furniture", "1128 Lunetta Street", "US"],
        ]
        self._helper_check_rows(reader, expected_values)

    def test_export_m2m_headers(self):
        reader = self._helper_get_resulting_csv(self.ir_exports_m2m, self.partners)
        expected_headers = ["id", "name", "company_ids|1|name"]
        headers = reader.__next__()
        self.assertEqual(headers, expected_headers)

    def test_export_m2m_values(self):
        reader = self._helper_get_resulting_csv(self.ir_exports_m2m, self.partners)
        expected_values = [
            [self.user1.id, "Wood Corner", "Awesome company"],
            [self.user2.id, "Wood Corner", "Awesome company"],
            [self.user3.id, "Deco Addict", "YourCompany"],
        ]
        self._helper_check_rows(reader, expected_values)

    def test_export_o2m_headers(self):
        reader = self._helper_get_resulting_csv(self.ir_exports_o2m, self.partners)
        expected_headers = [
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
        headers = reader.__next__()
        self.assertEqual(headers, expected_headers)

    def test_export_o2m_values(self):
        reader = self._helper_get_resulting_csv(self.ir_exports_o2m, self.partners)
        id1 = self.env.ref("base.res_partner_1").id
        id2 = self.env.ref("base.res_partner_2").id
        expected_values = [
            [
                id1,
                "Wood Corner",
                self.user2.id,
                self.user2.name,
                self.user2.company_ids[0].name,
                self.user1.id,
                self.user1.name,
                self.user1.company_ids[0].name,
                CELL_VALUE_EMPTY,
                CELL_VALUE_EMPTY,
                CELL_VALUE_EMPTY,
            ],
            [
                id2,
                "Deco Addict",
                self.user3.id,
                self.user3.name,
                self.user3.company_ids[0].name,
                CELL_VALUE_EMPTY,
                CELL_VALUE_EMPTY,
                CELL_VALUE_EMPTY,
                CELL_VALUE_EMPTY,
                CELL_VALUE_EMPTY,
            ],
        ]
        self._helper_check_rows(reader, expected_values)
