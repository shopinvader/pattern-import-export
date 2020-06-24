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
        expected_header = self._get_header_from_export(self.ir_exports)
        self.assertEquals(expected_header, headers)

    def test_get_header2(self):
        """
        Ensure the header is correctly generated
        @return:
        """
        headers = self.ir_exports_m2m._get_header()
        expected_header = self._get_header_from_export(self.ir_exports_m2m)
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
        for result, expected_result in zip(
            self.ir_exports._get_data_to_export(self.partners), expected_results
        ):
            self.assertDictEqual(expected_result, result)

    def test_get_data_to_export2(self):
        """
        Ensure the _get_data_to_export return expected data
        @return:
        """
        expected_results = [
            {
                "id": "base.user_root",
                "name": "OdooBot",
                "company_ids|1": "Awesome company",
            }
        ]
        for result, expected_result in zip(
            self.ir_exports_m2m._get_data_to_export(self.env.user), expected_results
        ):
            self.assertDictEqual(expected_result, result)

    def test_get_data_to_export3(self):
        """
        Ensure the _get_data_to_export return expected data
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
        for result, expected_result in zip(
            self.ir_exports_m2m._get_data_to_export(self.env.user), expected_results
        ):
            self.assertDictEqual(expected_result, result)
