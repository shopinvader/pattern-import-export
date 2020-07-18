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
            "ID",
            "Name",
            "Street",
            "Country|Country Code",
            "Related Company|Country|Country Code",
        ]
        self.assertEquals(expected_header, headers)

    def test_get_header2(self):
        """
        Ensure the header is correctly generated in case of M2M with 1 occurrence
        @return:
        """
        headers = self.ir_exports_m2m._get_header()
        expected_header = ["ID", "Name", "Companies|1|Company Name"]
        self.assertEquals(expected_header, headers)

    def test_get_header3(self):
        """
        Ensure the header is correctly generated in case of M2M more than 1 occurrence
        @return:
        """
        export_fields_m2m = self.ir_exports_m2m.export_fields.filtered(
            lambda l: l.name == "company_ids/name"
        )
        export_fields_m2m.write({"number_occurence": 5})
        headers = self.ir_exports_m2m._get_header()
        expected_header = [
            "ID",
            "Name",
            "Companies|1|Company Name",
            "Companies|2|Company Name",
            "Companies|3|Company Name",
            "Companies|4|Company Name",
            "Companies|5|Company Name",
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
            "ID",
            "Name",
            "Users|1|ID",
            "Users|1|Name",
            "Users|1|Companies|1|Company Name",
            "Users|2|ID",
            "Users|2|Name",
            "Users|2|Companies|1|Company Name",
            "Users|3|ID",
            "Users|3|Name",
            "Users|3|Companies|1|Company Name",
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
            lambda l: l.name == "company_ids/name"
        )
        export_fields_m2m.write({"number_occurence": 5})
        headers = self.ir_exports_o2m._get_header()
        expected_header = [
            "ID",
            "Name",
            "Users|1|ID",
            "Users|1|Name",
            "Users|1|Companies|1|Company Name",
            "Users|1|Companies|2|Company Name",
            "Users|1|Companies|3|Company Name",
            "Users|1|Companies|4|Company Name",
            "Users|1|Companies|5|Company Name",
            "Users|2|ID",
            "Users|2|Name",
            "Users|2|Companies|1|Company Name",
            "Users|2|Companies|2|Company Name",
            "Users|2|Companies|3|Company Name",
            "Users|2|Companies|4|Company Name",
            "Users|2|Companies|5|Company Name",
            "Users|3|ID",
            "Users|3|Name",
            "Users|3|Companies|1|Company Name",
            "Users|3|Companies|2|Company Name",
            "Users|3|Companies|3|Company Name",
            "Users|3|Companies|4|Company Name",
            "Users|3|Companies|5|Company Name",
        ]
        self.assertEquals(expected_header, headers)

    def test_get_data_to_export1(self):
        """
        Ensure the _get_data_to_export return expected data
        @return:
        """
        expected_results = [
            {
                "ID": "base.res_partner_1",
                "Name": "Wood Corner",
                "Street": "1164 Cambridge Drive",
                "Country|Country Code": "US",
                "Contacts|1|Country|Country Code": "US",
            },
            {
                "ID": "base.res_partner_2",
                "Name": "Deco Addict",
                "Street": "325 Elsie Drive",
                "Country|Country Code": "US",
                "Contacts|1|Country|Country Code": "US",
            },
            {
                "ID": "base.res_partner_3",
                "Name": "Gemini Furniture",
                "Street": "1128 Lunetta Street",
                "Country|Country Code": "US",
                "Contacts|1|Country|Country Code": "US",
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
                "ID": "base.user_root",
                "Name": "OdooBot",
                "Companies|1|Company Name": "Awesome company",
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
                    "ID": "base.user_root",
                    "Name": "OdooBot",
                    "Companies|1|Company Name": "Awesome company",
                    "Companies|2|Company Name": "Bad company",
                    "Companies|3|Company Name": "YourCompany",
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
                    "ID": self.partner_1.get_xml_id().get(self.partner_1.id),
                    "Name": "Wood Corner",
                    "Users|1|ID": self.user1.get_xml_id().get(self.user1.id),
                    "Users|1|Name": "Wood Corner",
                    "Users|1|Companies|1|Company Name": "Awesome company",
                }
            ),
            OrderedDict(
                {
                    "ID": self.partner_2.get_xml_id().get(self.partner_2.id),
                    "Name": "Deco Addict",
                    "Users|1|ID": self.user3.get_xml_id().get(self.user3.id),
                    "Users|1|Name": "Deco Addict",
                    "Users|1|Companies|1|Company Name": "YourCompany",
                }
            ),
            OrderedDict({"ID": "base.res_partner_3", "Name": "Gemini Furniture"}),
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
                    "ID": "base.res_partner_1",
                    "Name": "Wood Corner",
                    "Users|1|ID": self.user1.get_xml_id().get(self.user1.id),
                    "Users|1|Name": "Wood Corner",
                    "Users|1|Companies|1|Company Name": "Awesome company",
                    "Users|1|Companies|2|Company Name": "Bad company",
                    "Users|1|Companies|3|Company Name": "YourCompany",
                }
            ),
            OrderedDict(
                {
                    "ID": "base.res_partner_2",
                    "Name": "Deco Addict",
                    "Users|1|ID": self.user3.get_xml_id().get(self.user3.id),
                    "Users|1|Name": "Deco Addict",
                    "Users|1|Companies|1|Company Name": "YourCompany",
                }
            ),
            OrderedDict({"ID": "base.res_partner_3", "Name": "Gemini Furniture"}),
        ]
        results = self.ir_exports_o2m._get_data_to_export(self.partners)
        for result, expected_result in zip(results, expected_results):
            self.assertDictEqual(expected_result, result)

    def test_get_data_to_export_is_key1(self):
        """
        Ensure the _get_data_to_export return expected data with correct header
        when one export line is considered as key (on simple fields)
        @return:
        """
        expected_results = [
            {
                "ID": "base.res_partner_1",
                "Name/key": "Wood Corner",
                "Street": "1164 Cambridge Drive",
                "Country|Country Code": "US",
                "Contacts|1|Country|Country Code": "US",
            },
            {
                "ID": "base.res_partner_2",
                "Name/key": "Deco Addict",
                "Street": "325 Elsie Drive",
                "Country|Country Code": "US",
                "Contacts|1|Country|Country Code": "US",
            },
            {
                "ID": "base.res_partner_3",
                "Name/key": "Gemini Furniture",
                "Street": "1128 Lunetta Street",
                "Country|Country Code": "US",
                "Contacts|1|Country|Country Code": "US",
            },
        ]
        self.ir_exports.export_fields.filtered(lambda l: l.name == "name").write(
            {"is_key": True}
        )
        results = self.ir_exports._get_data_to_export(self.partners)
        for result, expected_result in zip(results, expected_results):
            self.assertDictEqual(expected_result, result)

    def test_get_data_to_export_is_key2(self):
        """
        Ensure the _get_data_to_export return expected data with correct header
        when one export line is considered as key (on relational fields)
        @return:
        """
        expected_results = [
            {
                "ID": "base.res_partner_1",
                "Name": "Wood Corner",
                "Street": "1164 Cambridge Drive",
                "Country/key|Country Code": "US",
                "Contacts|1|Country|Country Code": "US",
            },
            {
                "ID": "base.res_partner_2",
                "Name": "Deco Addict",
                "Street": "325 Elsie Drive",
                "Country/key|Country Code": "US",
                "Contacts|1|Country|Country Code": "US",
            },
            {
                "ID": "base.res_partner_3",
                "Name": "Gemini Furniture",
                "Street": "1128 Lunetta Street",
                "Country/key|Country Code": "US",
                "Contacts|1|Country|Country Code": "US",
            },
        ]
        self.ir_exports.export_fields.filtered(lambda l: l.name == "country_id").write(
            {"is_key": True}
        )
        results = self.ir_exports._get_data_to_export(self.partners)
        for result, expected_result in zip(results, expected_results):
            self.assertDictEqual(expected_result, result)
