# Copyright 2020 Akretion France (http://www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from uuid import uuid4

from odoo.tests.common import SavepointCase
from odoo.tools import mute_logger

from .common import ExportPatternCommon


class TestPatternImport(ExportPatternCommon, SavepointCase):
    def test_update_with_external_id(self):
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
            self.ir_exports_m2m._generate_import_with_pattern_job(
                self.empty_patterned_import_export
            )
        new_records = self.env[target_model].search(
            [("id", "not in", existing_records.ids)]
        )
        self.assertFalse(new_records)
        self.assertEquals(unique_name, self.user3.name)

    # TODO FIXME
    def disable_test_update_with_external_id_bad_data_1(self):
        """
        For this test, simulate the case of an update of existing record
        with 'simple' fields and ensure no new records are created
        @return:
        """
        unique_name = str(uuid4())
        main_data = [{"id": 2, "name": unique_name}]
        with self._mock_read_import_data(main_data):
            self.ir_exports_m2m._generate_import_with_pattern_job(
                self.empty_patterned_import_export
            )

    # TODO FIXME
    def disable_test_update_with_external_id_bad_data_2(self):
        """
        For this test, simulate the case of an update of existing record
        with 'simple' fields and ensure no new records are created
        @return:
        """
        unique_name = str(uuid4())
        main_data = [{".id": "bad data", "name": unique_name}]
        with self._mock_read_import_data(main_data):
            self.ir_exports_m2m._generate_import_with_pattern_job(
                self.empty_patterned_import_export
            )

    def test_create_new_record(self):
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
            self.ir_exports_m2m._generate_import_with_pattern_job(
                self.empty_patterned_import_export
            )
        new_records = self.env[target_model].search(
            [("id", "not in", existing_records.ids)]
        )
        self.assertEquals(len(new_records), 1)
        self.assertEquals(unique_name, new_records.name)
        self.assertEquals(unique_login, new_records.login)

    def test_update_o2m_with_external_id(self):
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
            self.ir_exports._generate_import_with_pattern_job(
                self.empty_patterned_import_export
            )
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

    def test_update_o2m_m2m_with_external_id(self):
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
            self.ir_exports._generate_import_with_pattern_job(
                self.empty_patterned_import_export
            )
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

    def test_update_with_key(self):
        unique_name = str(uuid4())
        main_data = [{"login#key": self.user3.login, "name": unique_name}]
        with self._mock_read_import_data(main_data):
            self.ir_exports_m2m._generate_import_with_pattern_job(
                self.empty_patterned_import_export
            )
        self.assertEquals(unique_name, self.user3.name)

    def test_update_o2m_with_key(self):
        unique_name = str(uuid4())
        contact_1_name = str(uuid4())
        contact_2_name = str(uuid4())
        self.partner_1.ref = "o2m_main"
        contact_1 = self.env.ref("base.res_partner_address_1")
        contact_2 = self.env.ref("base.res_partner_address_2")
        contact_1.ref = "o2m_child_1"
        contact_2.ref = "o2m_child_2"
        main_data = [
            {
                "ref#key": self.partner_1.ref,
                "name": unique_name,
                "child_ids|1|ref#key": contact_1.ref,
                "child_ids|1|name": contact_1_name,
                "child_ids|2|ref#key": contact_2.ref,
                "child_ids|2|name": contact_2_name,
            }
        ]
        with self._mock_read_import_data(main_data):
            self.ir_exports._generate_import_with_pattern_job(
                self.empty_patterned_import_export
            )
        self.assertEquals(unique_name, self.partner_1.name)
        self.assertEquals(contact_1_name, contact_1.name)
        self.assertEquals(contact_2_name, contact_2.name)

    @mute_logger("odoo.sql_db")
    def test_wrong_import(self):
        main_data = [{"login#key": self.user3.login, "name": ""}]
        with self._mock_read_import_data(main_data):
            self.ir_exports_m2m._generate_import_with_pattern_job(
                self.empty_patterned_import_export
            )
            self.assertEqual(self.empty_patterned_import_export.status, "fail")
            self.assertIn(
                "Several error have been found number of errors: 1,"
                " number of warnings: 0",
                self.empty_patterned_import_export.info,
            )

    def test_m2m_with_empty_columns(self):
        unique_name = str(uuid4())
        main_data = [
            {
                "name": unique_name,
                "category_id|1|name": self.partner_cat1.name,
                "category_id|2|name": None,
                "category_id|3|name": "",
            }
        ]
        with self._mock_read_import_data(main_data):
            self.ir_exports._generate_import_with_pattern_job(
                self.empty_patterned_import_export
            )
        partner = self.env["res.partner"].search([("name", "=", unique_name)])
        self.assertEqual(self.empty_patterned_import_export.status, "success")
        self.assertEqual(len(partner), 1)
        self.assertEquals(self.partner_cat1, partner.category_id)

    def test_empty_o2m(self):
        unique_name = str(uuid4())
        partner2_name = str(uuid4())
        main_data = [
            {
                "name": unique_name,
                "child_ids|1|name": partner2_name,
                "child_ids|1|country_id|code": "FR",
                "child_ids|2|name": "",
                "child_ids|2|country_id|code": "",
                "child_ids|3|name": None,
                "child_ids|3|country_id|code": None,
                "child_ids|4|name": None,
                "child_ids|4|country_id|code": "",
            }
        ]
        with self._mock_read_import_data(main_data):
            self.ir_exports._generate_import_with_pattern_job(
                self.empty_patterned_import_export
            )
        self.assertEqual(
            self.empty_patterned_import_export.status,
            "success",
            self.empty_patterned_import_export.info,
        )
        partner = self.env["res.partner"].search([("name", "=", unique_name)])
        self.assertEqual(len(partner), 1)
        self.assertEqual(len(partner.child_ids), 1)

    def test_empty_m2m_with_o2m(self):
        unique_name = str(uuid4())
        partner2_name = str(uuid4())
        main_data = [
            {
                "name": unique_name,
                "child_ids|1|name": partner2_name,
                "child_ids|1|country_id|code": "FR",
                "child_ids|1|category_id|1|name": "Prospects",
                "child_ids|1|category_id|2|name": "Services",
                "child_ids|1|category_id|3|name": None,
            }
        ]
        with self._mock_read_import_data(main_data):
            self.ir_exports._generate_import_with_pattern_job(
                self.empty_patterned_import_export
            )
        self.assertEqual(
            self.empty_patterned_import_export.status,
            "success",
            self.empty_patterned_import_export.info,
        )
        partner = self.env["res.partner"].search([("name", "=", unique_name)])
        self.assertEqual(len(partner), 1)
        self.assertEqual(len(partner.child_ids), 1)
        self.assertEqual(
            set(partner.child_ids.category_id.mapped("name")),
            {"Prospects", "Services"})

    def test_missing_record(self):
        main_data = [{"name": str(uuid4()), "country_id|code": "Fake"}]
        with self._mock_read_import_data(main_data):
            self.ir_exports._generate_import_with_pattern_job(
                self.empty_patterned_import_export
            )
        self.assertEqual(self.empty_patterned_import_export.status, "fail")
        self.assertIn(
            (
                "Fail to process field 'Country'.\n"
                "No value found for model 'Country' with the field 'code' "
                "and the value 'Fake'"
            ),
            self.empty_patterned_import_export.info,
        )

    def disable_test_import_m2o_key(self):
        name = str(uuid4())
        ref = str(uuid4())
        main_data = [{"name": name, "country_id|code#key": "FR", "ref#key": ref}]
        with self._mock_read_import_data(main_data):
            self.ir_exports._generate_import_with_pattern_job(
                self.empty_patterned_import_export
            )
        self.assertEqual(
            self.empty_patterned_import_export.status,
            "success",
            self.empty_patterned_import_export.info,
        )
        partner = self.env["res.partner"].search([("name", "=", name)])
        self.assertEqual(len(partner), 1)
        self.assertEqual(len(partner.ref), ref)
        self.assertEqual(len(partner.name), name)
        self.assertEqual(len(partner.country_id.code), "FR")
