# Copyright 2020 Akretion France (http://www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from collections import OrderedDict
from uuid import uuid4

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
            OrderedDict(
                {
                    "id": "base.user_root",
                    "name": "OdooBot",
                    "company_ids|1": "Awesome company",
                    "company_ids|2": "Bad company",
                    "company_ids|3": "YourCompany",
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
                    "user_ids|1|company_ids|1": "Awesome company",
                }
            ),
            OrderedDict(
                {
                    "id": "base.res_partner_2",
                    "name": "Deco Addict",
                    "user_ids|1|id": self.user3.get_xml_id().get(self.user3.id),
                    "user_ids|1|name": "Deco Addict",
                    "user_ids|1|company_ids|1": "YourCompany",
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
                    "user_ids|1|company_ids|1": "Awesome company",
                    "user_ids|1|company_ids|2": "Bad company",
                    "user_ids|1|company_ids|3": "YourCompany",
                }
            ),
            OrderedDict(
                {
                    "id": "base.res_partner_2",
                    "name": "Deco Addict",
                    "user_ids|1|id": self.user3.get_xml_id().get(self.user3.id),
                    "user_ids|1|name": "Deco Addict",
                    "user_ids|1|company_ids|1": "YourCompany",
                }
            ),
            OrderedDict({"id": "base.res_partner_3", "name": "Gemini Furniture"}),
        ]
        results = self.ir_exports_o2m._get_data_to_export(self.partners)
        for result, expected_result in zip(results, expected_results):
            self.assertDictEqual(expected_result, result)

    def test_get_target_fields_import(self):
        """
        Test the function _get_target_fields_import.
        This function should return every fields name targeted
        by columns names (without duplicated)
        @return:
        """
        columns = [
            "id",
            "name",
            "company_ids|1",
            "company_ids|2",
            "company_ids|3",
            "user_ids|1|id",
            "user_ids|1|name",
            "user_ids|1|login",
            "user_ids|2|id",
            "user_ids|2|name",
            "user_ids|2|login",
        ]
        expected_result = [
            "id",
            "name",
            "company_ids/id",
            "user_ids/id",
            "user_ids/name",
            "user_ids/login",
        ]
        for expected_field_name, result in zip(
            expected_result, self.ir_exports._get_target_fields_import(columns)
        ):
            self.assertEquals(expected_field_name, result)

    def test_build_data_to_import1(self):
        """
        Test the function _build_data_to_import.
        Ensure each data from M2M and O2M are grouped.
        For this test, we simulate a normal case where main data are
        correctly organized
        @return:
        """
        unique_id = str(uuid4())
        unique_name = str(uuid4())
        company1 = str(uuid4())
        company2 = str(uuid4())
        company3 = str(uuid4())
        user1_id = str(uuid4())
        user1_name = str(uuid4())
        user1_login = str(uuid4())
        user2_id = str(uuid4())
        user2_name = str(uuid4())
        user2_login = str(uuid4())
        main_data = {
            "id": unique_id,
            "name": unique_name,
            "company_ids|1": company1,
            "company_ids|2": company2,
            "company_ids|3": company3,
            "user_ids|1|id": user1_id,
            "user_ids|1|name": user1_name,
            "user_ids|1|login": user1_login,
            "user_ids|2|id": user2_id,
            "user_ids|2|name": user2_name,
            "user_ids|2|login": user2_login,
        }
        expected_results = [
            {
                "id": unique_id,
                "name": unique_name,
                "company_ids/id": ",".join([company1, company2, company3]),
            },
            {
                "user_ids/id": user1_id,
                "user_ids/name": user1_name,
                "user_ids/login": user1_login,
            },
            {
                "user_ids/id": user2_id,
                "user_ids/name": user2_name,
                "user_ids/login": user2_login,
            },
        ]
        for result in self.ir_exports_o2m._build_data_to_import(main_data):
            self.assertIn(result, expected_results)
            expected_results = [e for e in expected_results if e != result]
        # Ensure each item was found
        self.assertFalse(expected_results)

    def test_build_data_to_import2(self):
        """
        Test the function _build_data_to_import.
        Ensure each data from M2M and O2M are grouped.
        For this test, we simulate a normal case where main data are
        correctly organized
        @return:
        """
        unique_id = str(uuid4())
        unique_name = str(uuid4())
        company1 = self.company1.name
        company2 = self.company2.name
        company3 = self.company3.name
        user1_id = str(uuid4())
        user1_name = str(uuid4())
        user1_login = str(uuid4())
        user2_id = str(uuid4())
        user2_name = str(uuid4())
        user2_login = str(uuid4())
        main_data = {
            "id": unique_id,
            "name": unique_name,
            "company_ids|1|name": company1,
            "company_ids|2|name": company2,
            "company_ids|3|name": company3,
            "user_ids|1|id": user1_id,
            "user_ids|1|name": user1_name,
            "user_ids|1|login": user1_login,
            "user_ids|2|id": user2_id,
            "user_ids|2|name": user2_name,
            "user_ids|2|login": user2_login,
        }
        expected_results = [
            {
                "id": unique_id,
                "name": unique_name,
                "company_ids": ",".join([company1, company2, company3]),
            },
            {
                "company_ids": ",".join([company1, company2, company3]),
            },
            {
                "company_ids": ",".join([company1, company2, company3]),
            },
            {
                "user_ids/id": user1_id,
                "user_ids/name": user1_name,
                "user_ids/login": user1_login,
            },
            {
                "user_ids/id": user2_id,
                "user_ids/name": user2_name,
                "user_ids/login": user2_login,
            },
        ]
        for result in self.ir_exports_o2m._build_data_to_import(main_data):
            self.assertIn(result, expected_results)
            expected_results = [e for e in expected_results if e != result]
        # Ensure each item was found
        self.assertFalse(expected_results)

    def test_build_data_to_import3(self):
        """
        Test the function _build_data_to_import.
        Ensure each data from M2M and O2M are grouped.
        For this test, we simulate a normal case where main data are
        not correctly organized.
        @return:
        """
        unique_id = str(uuid4())
        unique_name = str(uuid4())
        company1 = str(uuid4())
        company2 = str(uuid4())
        company3 = str(uuid4())
        user1_id = str(uuid4())
        user1_name = str(uuid4())
        user1_login = str(uuid4())
        user2_id = str(uuid4())
        user2_name = str(uuid4())
        user2_login = str(uuid4())
        main_data = {
            "company_ids|3": company3,
            "user_ids|1|login": user1_login,
            "user_ids|2|id": user2_id,
            "id": unique_id,
            "name": unique_name,
            "user_ids|2|login": user2_login,
            "company_ids|1": company1,
            "company_ids|2": company2,
            "user_ids|1|id": user1_id,
            "user_ids|1|name": user1_name,
            "user_ids|2|name": user2_name,
        }
        expected_results = [
            {
                "id": unique_id,
                "name": unique_name,
                "company_ids/id": ",".join([company3, company1, company2]),
            },
            {
                "user_ids/id": user1_id,
                "user_ids/name": user1_name,
                "user_ids/login": user1_login,
            },
            {
                "user_ids/id": user2_id,
                "user_ids/name": user2_name,
                "user_ids/login": user2_login,
            },
        ]
        # The order is not important
        for result in self.ir_exports_o2m._build_data_to_import(main_data):
            self.assertIn(result, expected_results)
            expected_results = [e for e in expected_results if e != result]
        # Ensure each item was found
        self.assertFalse(expected_results)

    def test_generate_import_with_pattern_job1(self):
        """
        For this test, simulate the case of an update of existing record
        @return:
        """
        unique_name = str(uuid4())
        main_data = [
            {"id": self.user3.get_xml_id().get(self.user3.id), "name": unique_name}
        ]
        target_model = self.ir_exports_m2m.model_id.model
        existing_records = self.env[target_model].search([])
        with self._mock_read_import_data(main_data):
            self.ir_exports_m2m._generate_import_with_pattern_job(self.empty_attachment)
        new_records = self.env[target_model].search(
            [("id", "not in", existing_records.ids)]
        )
        self.assertFalse(new_records)
        self.assertEquals(unique_name, self.user3.name)

    def test_generate_import_with_pattern_job2(self):
        """
        For this test, simulate the case of the creation of a new record
        @return:
        """
        unique_name = str(uuid4())
        unique_login = str(uuid4())
        main_data = [{"name": unique_name, "login": unique_login}]
        target_model = self.ir_exports_m2m.model_id.model
        existing_records = self.env[target_model].search([])
        with self._mock_read_import_data(main_data):
            self.ir_exports_m2m._generate_import_with_pattern_job(self.empty_attachment)
        new_records = self.env[target_model].search(
            [("id", "not in", existing_records.ids)]
        )
        self.assertEquals(len(new_records), 1)
        self.assertEquals(unique_name, new_records.name)
        self.assertEquals(unique_login, new_records.login)

    def test_generate_import_with_pattern_job3(self):
        """
        For this test, simulate the case of a complex update on existing record
        @return:
        """
        unique_name = str(uuid4())
        user1_name = str(uuid4())
        user1_login = str(uuid4())
        user2_name = str(uuid4())
        user2_login = str(uuid4())
        company_xml_ids = ",".join(
            [
                self.company1.get_xml_id().get(self.company1.id),
                self.company2.get_xml_id().get(self.company2.id),
                self.company3.get_xml_id().get(self.company3.id),
            ]
        )
        main_data = [
            {
                "id": self.user3.get_xml_id().get(self.user3.id),
                "name": unique_name,
                "company_ids/id": company_xml_ids,
            },
            {
                "user_ids/id": self.user1.get_xml_id().get(self.user1.id),
                "user_ids/name": user1_name,
                "user_ids/login": user1_login,
            },
            {
                "user_ids/id": self.user2.get_xml_id().get(self.user2.id),
                "user_ids/name": user2_name,
                "user_ids/login": user2_login,
            },
        ]
        target_model = self.ir_exports_m2m.model_id.model
        existing_records = self.env[target_model].search([])
        with self._mock_read_import_data(main_data):
            self.ir_exports_m2m._generate_import_with_pattern_job(self.empty_attachment)
        new_records = self.env[target_model].search(
            [("id", "not in", existing_records.ids)]
        )
        self.assertFalse(new_records)
        # Special case: as the name comes from the related res.partner and
        # we link these 3 users together, the name will be the one
        # set in last position
        self.assertEquals(user2_name, self.user3.name)
        self.assertIn(self.company1, self.user3.company_ids)
        self.assertIn(self.company2, self.user3.company_ids)
        self.assertIn(self.company3, self.user3.company_ids)
        self.assertIn(self.user1, self.user3.user_ids)
        self.assertIn(self.user2, self.user2.user_ids)

    def test_generate_import_with_pattern_job4(self):
        """
        For this test, simulate the case of a complex update on existing record
        and mix M2M in O2M
        @return:
        """
        unique_name = str(uuid4())
        user1_name = str(uuid4())
        user1_login = str(uuid4())
        user2_name = str(uuid4())
        user2_login = str(uuid4())
        groups_xml_ids3 = ",".join(
            [
                self.group_manager.get_xml_id().get(self.group_manager.id),
                self.group_no_one.get_xml_id().get(self.group_no_one.id),
                self.group_job.get_xml_id().get(self.group_job.id),
            ]
        )
        group_xml_ids2 = ",".join(
            [
                self.group_manager.get_xml_id().get(self.group_manager.id),
                self.group_no_one.get_xml_id().get(self.group_no_one.id),
            ]
        )
        main_data = [
            {
                "id": self.user3.get_xml_id().get(self.user3.id),
                "name": unique_name,
                "groups_id/id": groups_xml_ids3,
                "country_id/id": self.country_be.get_xml_id().get(self.country_be.id),
            },
            {
                "user_ids/id": self.user1.get_xml_id().get(self.user1.id),
                "user_ids/name": user1_name,
                "user_ids/login": user1_login,
                "user_ids/groups_id/id": group_xml_ids2,
                "user_ids/country_id/id": self.country_be.get_xml_id().get(
                    self.country_be.id
                ),
            },
            {
                "user_ids/id": self.user2.get_xml_id().get(self.user2.id),
                "user_ids/name": user2_name,
                "user_ids/login": user2_login,
                "user_ids/groups_id/id": self.group_manager.get_xml_id().get(
                    self.group_manager.id
                ),
                "user_ids/country_id/id": self.country_us.get_xml_id().get(
                    self.country_us.id
                ),
            },
        ]

        target_model = self.ir_exports_m2m.model_id.model
        existing_records = self.env[target_model].search([])
        with self._mock_read_import_data(main_data):
            self.ir_exports_m2m._generate_import_with_pattern_job(self.empty_attachment)
        new_records = self.env[target_model].search(
            [("id", "not in", existing_records.ids)]
        )
        self.assertFalse(new_records)
        # Special case: as the name comes from the related res.partner and
        # we link these 3 users together, the name will be the one
        # set in last position (and same for the country)
        self.assertEquals(user2_name, self.user3.name)
        self.assertEquals(self.country_us, self.user3.country_id)
        self.assertIn(self.group_manager, self.user3.groups_id)
        self.assertIn(self.group_no_one, self.user3.groups_id)
        self.assertIn(self.group_job, self.user3.groups_id)
        self.assertEquals(user1_login, self.user1.login)
        self.assertEquals(self.country_us, self.user1.country_id)
        self.assertIn(self.group_manager, self.user1.groups_id)
        self.assertIn(self.group_no_one, self.user1.groups_id)
        self.assertEquals(user2_login, self.user2.login)
        self.assertEquals(self.country_us, self.user2.country_id)
        self.assertIn(self.group_manager, self.user2.groups_id)

    def test_generate_import_with_pattern_job5(self):
        """
        For this test, simulate the case of a complex update on existing record
        and mix M2M in O2M
        @return:
        """
        unique_name = str(uuid4())
        user1_name = str(uuid4())
        user1_login = str(uuid4())
        user2_name = str(uuid4())
        user2_login = str(uuid4())
        groups_xml_ids3 = ",".join(
            [
                self.group_manager.get_xml_id().get(self.group_manager.id),
                self.group_no_one.get_xml_id().get(self.group_no_one.id),
                self.group_job.get_xml_id().get(self.group_job.id),
            ]
        )
        group_xml_ids2 = ",".join(
            [
                self.group_manager.get_xml_id().get(self.group_manager.id),
                self.group_no_one.get_xml_id().get(self.group_no_one.id),
            ]
        )
        main_data = [
            {
                "id": self.user3.get_xml_id().get(self.user3.id),
                "name": unique_name,
                "groups_id/id": groups_xml_ids3,
                "country_id/id": self.country_be.get_xml_id().get(self.country_be.id),
            },
            {
                "user_ids/id": self.user1.get_xml_id().get(self.user1.id),
                "user_ids/name": user1_name,
                "user_ids/login": user1_login,
                "user_ids/groups_id/id": group_xml_ids2,
                "user_ids/country_id/id": self.country_be.get_xml_id().get(self.country_be.id),
            },
            {
                "user_ids/id": self.user2.get_xml_id().get(self.user2.id),
                "user_ids/name": user2_name,
                "user_ids/login": user2_login,
                "user_ids/groups_id/id": self.group_manager.get_xml_id().get(
                    self.group_manager.id
                ),
                "user_ids/country_id/id": self.country_be.get_xml_id().get(self.country_be.id),
            },
        ]

        target_model = self.ir_exports_m2m.model_id.model
        existing_records = self.env[target_model].search([])
        with self._mock_read_import_data(main_data):
            self.ir_exports_m2m._generate_import_with_pattern_job(self.empty_attachment)
        new_records = self.env[target_model].search(
            [("id", "not in", existing_records.ids)]
        )
        self.assertFalse(new_records)
        # Special case: as the name comes from the related res.partner and
        # we link these 3 users together, the name will be the one
        # set in last position (and same for the country)
        self.assertEquals(user2_name, self.user3.name)
        self.assertEquals(self.country_be, self.user3.country_id)
        self.assertIn(self.group_manager, self.user3.groups_id)
        self.assertIn(self.group_no_one, self.user3.groups_id)
        self.assertIn(self.group_job, self.user3.groups_id)
        self.assertEquals(user1_login, self.user1.login)
        self.assertEquals(self.country_be, self.user1.country_id)
        self.assertIn(self.group_manager, self.user1.groups_id)
        self.assertIn(self.group_no_one, self.user1.groups_id)
        self.assertEquals(user2_login, self.user2.login)
        self.assertEquals(self.country_be, self.user2.country_id)
        self.assertIn(self.group_manager, self.user2.groups_id)
