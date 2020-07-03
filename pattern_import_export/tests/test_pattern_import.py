# Copyright 2020 Akretion France (http://www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from uuid import uuid4

from odoo.tests.common import SavepointCase

from .common import ExportPatternCommon


class TestPatternExport(ExportPatternCommon, SavepointCase):
    def test_generate_import_with_pattern_job1(self):
        """
        For this test, simulate the case of an update of existing record
        with 'simple' fields and ensure no new records are created
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
        For this test, simulate the case of a complex update (O2M) on existing record
        and ensure no new records are created
        @return:
        """
        unique_name = str(uuid4())
        partner2_name = str(uuid4())
        partner3_name = str(uuid4())
        main_data = [
            {
                "id": self.partner_1.get_xml_id().get(self.partner_1.id),
                "name": unique_name,
                "child_ids|1|id": self.partner_2.get_xml_id().get(self.partner_2.id),
                "child_ids|1|name": partner2_name,
                "child_ids|2|id": self.partner_3.get_xml_id().get(self.partner_3.id),
                "child_ids|2|name": partner3_name,
            }
        ]
        target_model = self.ir_exports.model_id.model
        existing_records = self.env[target_model].search([])
        with self._mock_read_import_data(main_data):
            self.ir_exports._generate_import_with_pattern_job(self.empty_attachment)
        new_records = self.env[target_model].search(
            [("id", "not in", existing_records.ids)]
        )
        self.assertFalse(new_records)
        # Special case: as the name comes from the related res.partner and
        # we link these 3 users together, the name will be the one
        # set in last position
        self.assertEquals(unique_name, self.partner_1.name)
        self.assertEquals(partner2_name, self.partner_2.name)
        self.assertEquals(partner3_name, self.partner_3.name)
        self.assertIn(self.partner_2, self.partner_1.child_ids)
        self.assertIn(self.partner_3, self.partner_1.child_ids)

    def test_generate_import_with_pattern_job4(self):
        """
        For this test, simulate the case of a complex update on existing record
        and mix M2M in O2M
        @return:
        """
        unique_name = str(uuid4())
        user1_name = str(uuid4())
        user2_name = str(uuid4())
        main_data = [
            {
                "id": self.partner_1.get_xml_id().get(self.partner_1.id),
                "name": unique_name,
                "category_id|1|id": self.partner_cat1.get_xml_id().get(
                    self.partner_cat1.id
                ),
                "category_id|2|id": self.partner_cat2.get_xml_id().get(
                    self.partner_cat2.id
                ),
                "country_id|id": self.country_be.get_xml_id().get(self.country_be.id),
                "child_ids|1|id": self.partner_2.get_xml_id().get(self.partner_2.id),
                "child_ids|1|name": user1_name,
                "child_ids|1|industry_id|id": self.industry1.get_xml_id().get(
                    self.industry1.id
                ),
                "child_ids|1|country_id|id": self.country_be.get_xml_id().get(
                    self.country_be.id
                ),
                "child_ids|1|category_id|1|id": self.partner_cat1.get_xml_id().get(
                    self.partner_cat1.id
                ),
                "child_ids|1|category_id|2|id": self.partner_cat2.get_xml_id().get(
                    self.partner_cat2.id
                ),
                "child_ids|2|id": self.partner_3.get_xml_id().get(self.partner_3.id),
                "child_ids|2|name": user2_name,
                "child_ids|2|industry_id|id": self.industry2.get_xml_id().get(
                    self.industry2.id
                ),
                "child_ids|2|country_id|id": self.country_us.get_xml_id().get(
                    self.country_us.id
                ),
                "child_ids|2|category_id|1|id": self.partner_cat2.get_xml_id().get(
                    self.partner_cat2.id
                ),
            }
        ]
        target_model = self.ir_exports.model_id.model
        existing_records = self.env[target_model].search([])
        with self._mock_read_import_data(main_data):
            self.ir_exports._generate_import_with_pattern_job(self.empty_attachment)
        new_records = self.env[target_model].search(
            [("id", "not in", existing_records.ids)]
        )
        self.assertFalse(new_records)
        self.assertEquals(unique_name, self.partner_1.name)
        self.assertIn(self.partner_cat1, self.partner_1.category_id)
        self.assertIn(self.partner_cat2, self.partner_1.category_id)
        self.assertEquals(self.country_be, self.partner_1.country_id)
        self.assertIn(self.partner_2, self.partner_1.child_ids)
        self.assertIn(self.partner_3, self.partner_1.child_ids)
        self.assertEquals(user1_name, self.partner_2.name)
        self.assertEquals(self.industry1, self.partner_2.industry_id)
        self.assertEquals(self.country_be, self.partner_2.country_id)
        self.assertIn(self.partner_cat1, self.partner_2.category_id)
        self.assertIn(self.partner_cat2, self.partner_2.category_id)
        self.assertEquals(user2_name, self.partner_3.name)
        self.assertEquals(self.industry2, self.partner_3.industry_id)
        # Because if the country is edited on the parent,
        # so the country is updated automatically on children.
        self.assertEquals(self.country_be, self.partner_3.country_id)
        self.assertEquals(self.partner_cat2, self.partner_3.category_id)

    def test_import_replace_keys1(self):
        """
        Test the _import_replace_keys function.
        For this test, we only have basic fields and without seperator
        @return:
        """
        values = {
            # Cast into str to ensure it's correctly converted into int
            "id/key": str(self.partner_3.id)
        }
        expected_results = {"id": self.partner_3.id}
        self.ir_exports._import_replace_keys(values, self.ir_exports.model_id.model)
        self.assertDictEqual(expected_results, values)

    def test_import_replace_keys2(self):
        """
        Test the _import_replace_keys function.
        For this test, we only have basic fields and without seperator
        @return:
        """
        barcode = str(uuid4())
        self.partner_3.write({"barcode": barcode})
        values = {
            # Cast into str to ensure it's correctly converted into int
            "barcode/key": barcode
        }
        expected_results = {"id": self.partner_3.id}
        self.ir_exports._import_replace_keys(values, self.ir_exports.model_id.model)
        self.assertDictEqual(expected_results, values)

    def test_import_replace_keys3(self):
        """
        Test the _import_replace_keys function.
        For this test the key shouldn't be replaced because there is the
        separator.
        @return:
        """
        values = {"parent_id|id/key": self.partner_3.id}
        expected_results = {"parent_id|id/key": self.partner_3.id}
        self.ir_exports._import_replace_keys(values, self.ir_exports.model_id.model)
        self.assertDictEqual(expected_results, values)
