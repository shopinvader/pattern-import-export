# Copyright 2020 Akretion France (http://www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from uuid import uuid4

from odoo.tests.common import SavepointCase
from odoo.tools import mute_logger

from .common import PatternCommon


class TestPatternImport(PatternCommon, SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.pattern_config_m2m.export_format = "json"
        cls.pattern_config_o2m.export_format = "json"
        cls.pattern_config.export_format = "json"

    def run_pattern_file(self, pattern_file):
        model = self.env[pattern_file.pattern_config_id.model_id.model].with_context(
            active_test=False
        )
        records = model.search([])
        pattern_file.split_in_chunk()
        return model.search([("id", "not in", records.ids)])

    def assertPatternDone(self, pattern_file):
        self.assertEqual(
            pattern_file.state,
            "done",
            "\n".join(pattern_file.mapped("chunk_ids.result_info")),
        )

    def test_update_inactive(self):
        unique_name = str(uuid4())
        partner = self.env["res.partner"].create({"name": unique_name, "active": False})
        data = [{"name#key": unique_name, "street": "foo"}]
        pattern_file = self.create_pattern(self.pattern_config, "import", data)
        self.run_pattern_file(pattern_file)
        self.assertEqual(partner.street, "foo")

    def test_update_with_external_id(self):
        """
        For this test, simulate the case of an update of existing record
        with 'simple' fields and ensure no new records are created
        @return:
        """
        unique_name = str(uuid4())
        data = [{"id": self.user3.get_xml_id().get(self.user3.id), "name": unique_name}]
        pattern_file = self.create_pattern(self.pattern_config_m2m, "import", data)
        records = self.run_pattern_file(pattern_file)
        self.assertFalse(records)
        self.assertEqual(unique_name, self.user3.name)

    def test_update_with_external_id_bad_data_1(self):
        """
        For this test, simulate the case of an update of existing record
        with 'simple' fields and ensure no new records are created
        @return:
        """
        unique_name = str(uuid4())
        data = [{"id": 0, "name": unique_name}]
        pattern_file = self.create_pattern(self.pattern_config_m2m, "import", data)
        records = self.run_pattern_file(pattern_file)
        self.assertFalse(records)
        self.assertEqual(pattern_file.state, "failed")
        # TODO it will be better to retour a better exception
        # but it's not that easy
        chunk = pattern_file.chunk_ids
        self.assertEqual(
            chunk.result_info,
            "<p>Fail to process chunk 'int' object has no attribute 'split'</p>",
        )

    def test_update_with_external_id_bad_data_2(self):
        """
        For this test, simulate the case of an update of existing record
        with 'simple' fields and ensure no new records are created
        @return:
        """
        unique_name = str(uuid4())
        data = [{".id": "bad data", "name": unique_name}]
        pattern_file = self.create_pattern(self.pattern_config_m2m, "import", data)
        records = self.run_pattern_file(pattern_file)
        self.assertFalse(records)
        self.assertEqual(pattern_file.state, "failed")
        chunk = pattern_file.chunk_ids
        self.assertIn("Invalid database identifier", chunk.result_info)

    def test_create_new_record(self):
        """
        For this test, simulate the case of the creation of a new record
        @return:
        """
        unique_name = str(uuid4())
        unique_login = str(uuid4())
        data = [{"name": unique_name, "login": unique_login}]
        pattern_file = self.create_pattern(self.pattern_config_m2m, "import", data)
        records = self.run_pattern_file(pattern_file)
        self.assertEqual(len(records), 1)
        self.assertEqual(unique_name, records.name)
        self.assertEqual(unique_login, records.login)

    def test_empty_external_id(self):
        unique_name = str(uuid4())
        unique_login = str(uuid4())
        data = [{"name": unique_name, "login": unique_login, "id": None}]
        pattern_file = self.create_pattern(self.pattern_config_m2m, "import", data)
        records = self.run_pattern_file(pattern_file)
        self.assertPatternDone(pattern_file)
        self.assertEqual(len(records), 1)
        self.assertEqual(records.name, unique_name)

    def test_empty_id(self):
        unique_name = str(uuid4())
        unique_login = str(uuid4())
        data = [{"name": unique_name, "login": unique_login, ".id": None}]
        pattern_file = self.create_pattern(self.pattern_config_m2m, "import", data)
        records = self.run_pattern_file(pattern_file)
        self.assertPatternDone(pattern_file)
        self.assertEqual(len(records), 1)
        self.assertEqual(records.name, unique_name)

    def test_update_o2m_with_external_id(self):
        """
        For this test, simulate the case of a complex update (O2M) on existing record
        and ensure no new records are created
        @return:
        """
        unique_name = str(uuid4())
        partner2_name = str(uuid4())
        partner3_name = str(uuid4())
        data = [
            {
                "id": self.partner_1.get_xml_id().get(self.partner_1.id),
                "name": unique_name,
                "child_ids|1|id": self.partner_2.get_xml_id().get(self.partner_2.id),
                "child_ids|1|name": partner2_name,
                "child_ids|2|id": self.partner_3.get_xml_id().get(self.partner_3.id),
                "child_ids|2|name": partner3_name,
            }
        ]
        pattern_file = self.create_pattern(self.pattern_config, "import", data)
        records = self.run_pattern_file(pattern_file)

        self.assertFalse(records)
        # Special case: as the name comes from the related res.partner and
        # we link these 3 users together, the name will be the one
        # set in last position
        self.assertEqual(unique_name, self.partner_1.name)
        self.assertEqual(partner2_name, self.partner_2.name)
        self.assertEqual(partner3_name, self.partner_3.name)
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
        data = [
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
        pattern_file = self.create_pattern(self.pattern_config, "import", data)
        records = self.run_pattern_file(pattern_file)

        self.assertFalse(records)
        self.assertEqual(unique_name, self.partner_1.name)
        self.assertIn(self.partner_cat1, self.partner_1.category_id)
        self.assertIn(self.partner_cat2, self.partner_1.category_id)
        self.assertEqual(self.country_be, self.partner_1.country_id)
        self.assertIn(self.partner_2, self.partner_1.child_ids)
        self.assertIn(self.partner_3, self.partner_1.child_ids)
        self.assertEqual(user1_name, self.partner_2.name)
        self.assertEqual(self.industry1, self.partner_2.industry_id)
        self.assertEqual(self.country_be, self.partner_2.country_id)
        self.assertIn(self.partner_cat1, self.partner_2.category_id)
        self.assertIn(self.partner_cat2, self.partner_2.category_id)
        self.assertEqual(user2_name, self.partner_3.name)
        self.assertEqual(self.industry2, self.partner_3.industry_id)
        # Because if the country is edited on the parent,
        # so the country is updated automatically on children.
        self.assertEqual(self.country_be, self.partner_3.country_id)
        self.assertEqual(self.partner_cat2, self.partner_3.category_id)

    def test_update_with_key(self):
        unique_name = str(uuid4())
        data = [{"login#key": self.user3.login, "name": unique_name}]
        pattern_file = self.create_pattern(self.pattern_config_m2m, "import", data)
        records = self.run_pattern_file(pattern_file)
        self.assertFalse(records)
        self.assertEqual(unique_name, self.user3.name)

    def test_update_with_muli_cols_pkey(self):
        """ensure we identify the row to update
        based on multiple columns with
        different depths
        """
        unique_name = str(uuid4())
        data = [
            {
                "partner_id#key|email": self.user3.partner_id.email,
                "partner_id#key|name": self.user3.partner_id.name,
                "partner_id#key|country_id|code": self.user3.partner_id.country_id.code,
                "name": unique_name,
            }
        ]
        pattern_file = self.create_pattern(self.pattern_config_m2m, "import", data)
        records = self.run_pattern_file(pattern_file)
        self.assertFalse(records)
        self.assertEqual(unique_name, self.user3.name)

        # same test with ambigus key
        # the record should not be updated because the key
        # returns more than 1 record
        ambigus = self.user3.search(
            [["country_id.code", "=", self.user3.partner_id.country_id.code]]
        )
        self.assertTrue(len(ambigus) > 1, "Verify conditions")
        unique_name_2 = str(uuid4())
        data = [
            {
                "partner_id#key|country_id|code": self.user3.partner_id.country_id.code,
                "name": unique_name_2,
            }
        ]
        pattern_file = self.create_pattern(self.pattern_config_m2m, "import", data)
        records = self.run_pattern_file(pattern_file)
        self.assertFalse(records)
        self.assertEqual(unique_name, self.user3.name, "Ensure value not updated")

    def test_update_o2m_with_key(self):
        unique_name = str(uuid4())
        contact_1_name = str(uuid4())
        contact_2_name = str(uuid4())
        self.partner_1.ref = "o2m_main"
        contact_1 = self.env.ref("base.res_partner_address_1")
        contact_2 = self.env.ref("base.res_partner_address_2")
        contact_1.ref = "o2m_child_1"
        contact_2.ref = "o2m_child_2"
        data = [
            {
                "ref#key": self.partner_1.ref,
                "name": unique_name,
                "child_ids|1|ref#key": contact_1.ref,
                "child_ids|1|name": contact_1_name,
                "child_ids|2|ref#key": contact_2.ref,
                "child_ids|2|name": contact_2_name,
            }
        ]
        pattern_file = self.create_pattern(self.pattern_config, "import", data)
        self.run_pattern_file(pattern_file)
        self.assertPatternDone(pattern_file)
        self.assertEqual(unique_name, self.partner_1.name)
        self.assertEqual(contact_1_name, contact_1.name)
        self.assertEqual(contact_2_name, contact_2.name)

    def test_update_o2m_with_key_only_one_record(self):
        unique_name = str(uuid4())
        self.partner_1.ref = "o2m_main"
        contact_1 = self.env.ref("base.res_partner_address_1")
        contact_2 = self.env.ref("base.res_partner_address_2")
        contact_1.ref = "o2m_child_1"
        contact_2.ref = "o2m_child_2"
        data = [
            {
                "ref#key": self.partner_1.ref,
                "name": unique_name,
                "child_ids|1|ref#key": contact_1.ref,
            }
        ]
        pattern_file = self.create_pattern(self.pattern_config, "import", data)
        self.run_pattern_file(pattern_file)
        self.assertEqual(unique_name, self.partner_1.name)

    def test_update_o2m_with_sub_keys(self):
        unique_name = str(uuid4())

        # state_ie_27,ie,"Antrim","AM"
        # there is multiple state with code = AM
        # in demo data, but only one with Currency = euro

        # ensure we picked a reference to only one record
        only_one_rec = self.env["res.country"].search(
            [["state_ids.code", "=", "AM"], ["currency_id.symbol", "=", "€"]]
        )
        self.assertEqual(len(only_one_rec), 1, "Ensure data for test valid")
        previous_country = self.partner_1.country_id
        new_country = only_one_rec
        data = [
            {
                "email#key": self.partner_1.email,
                "phone#key": self.partner_1.phone,
                "name": unique_name,
                "country_id|currency_id|symbol": "€",
                "country_id|state_ids|code": "AM",
                "title|name": "Professor",
            }
        ]
        pattern_file = self.create_pattern(self.pattern_config_o2m, "import", data)
        self.run_pattern_file(pattern_file)
        self.assertNotEqual(previous_country.id, new_country.id)
        self.assertEqual(
            unique_name, self.partner_1.name, "direct field has been updated"
        )
        self.assertEqual(
            new_country.id,
            self.partner_1.country_id.id,
            "relation field has been updated",
        )
        self.assertEqual(
            "Professor", self.partner_1.title.name, "relation field has been updated"
        )

    @mute_logger("odoo.sql_db")
    def test_wrong_import(self):
        data = [{"login#key": self.user3.login, "name": ""}]
        pattern_file = self.create_pattern(self.pattern_config_m2m, "import", data)
        self.run_pattern_file(pattern_file)
        self.assertEqual(pattern_file.state, "failed")
        self.assertEqual(pattern_file.nbr_error, 1)
        self.assertIn("res_partner_check_name", pattern_file.chunk_ids.result_info)

    def test_m2m_with_empty_columns(self):
        unique_name = str(uuid4())
        data = [
            {
                "name": unique_name,
                "category_id|1|name": self.partner_cat1.name,
                "category_id|2|name": None,
                "category_id|3|name": "",
            }
        ]
        pattern_file = self.create_pattern(self.pattern_config, "import", data)
        partner = self.run_pattern_file(pattern_file)
        self.assertPatternDone(pattern_file)
        self.assertEqual(len(partner), 1)
        self.assertEqual(partner.name, unique_name)
        self.assertEqual(self.partner_cat1, partner.category_id)

    def test_m2m_update(self):
        self.partner_1.category_id = self.partner_cat2
        item = {".id": self.partner_1.id, "category_id|1|name": self.partner_cat1.name}
        pattern_file = self.create_pattern(self.pattern_config, "import", [item])
        self.run_pattern_file(pattern_file)
        self.assertPatternDone(pattern_file)
        self.assertEqual(self.partner_cat1, self.partner_1.category_id)

    def test_o2m_with_empty_value(self):
        unique_name = str(uuid4())
        partner2_name = str(uuid4())
        data = [
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
        pattern_file = self.create_pattern(self.pattern_config, "import", data)
        partners = self.run_pattern_file(pattern_file)

        self.assertPatternDone(pattern_file)
        self.assertEqual(len(partners), 2)
        self.assertEqual(partners[0].name, unique_name)
        self.assertEqual(partners[0].child_ids, partners[1])

    def _helper_o2m_update(self):
        unique_name = str(uuid4())
        partner = self.env["res.partner"].create(
            {
                "name": unique_name,
                "child_ids": [
                    (0, 0, {"name": f"{unique_name}-c1", "email": "c1@example.org"}),
                    (0, 0, {"name": f"{unique_name}-c2", "email": "c2@example.org"}),
                ],
            }
        )
        child_1, child_2 = partner.child_ids
        data = [
            {
                ".id": partner.id,
                "child_ids|1|name": f"{unique_name}-c1-renamed",
                "child_ids|1|email#key": "c1@example.org",
                "child_ids|2|name": f"{unique_name}-d2",
                "child_ids|2|email#key": "d2@example.org",
                "child_ids|3|name": f"{unique_name}-d3",
                "child_ids|3|email#key": "d3@example.org",
            }
        ]
        pattern_file = self.create_pattern(self.pattern_config, "import", data)
        self.run_pattern_file(pattern_file)
        self.assertPatternDone(pattern_file)
        return partner, child_1, child_2

    def test_o2m_update_with_purge(self):
        self.pattern_config.purge_one2many = True
        partner, child_1, child_2 = self._helper_o2m_update()
        self.assertEqual(len(partner.child_ids), 3)
        self.assertIn(child_1, partner.child_ids)
        self.assertNotIn(child_2, partner.child_ids)

    def test_o2m_update_without_purge(self):
        self.pattern_config.purge_one2many = False
        partner, child_1, child_2 = self._helper_o2m_update()
        self.assertEqual(len(partner.child_ids), 4)
        self.assertIn(child_1, partner.child_ids)
        self.assertIn(child_2, partner.child_ids)

    def test_empty_m2m_with_o2m(self):
        unique_name = str(uuid4())
        partner2_name = str(uuid4())
        data = [
            {
                "name": unique_name,
                "child_ids|1|name": partner2_name,
                "child_ids|1|country_id|code": "FR",
                "child_ids|1|category_id|1|name": "Prospects",
                "child_ids|1|category_id|2|name": "Services",
                "child_ids|1|category_id|3|name": None,
            }
        ]
        pattern_file = self.create_pattern(self.pattern_config, "import", data)
        partners = self.run_pattern_file(pattern_file)

        self.assertPatternDone(pattern_file)
        self.assertEqual(len(partners), 2)
        self.assertEqual(partners[0].name, unique_name)
        self.assertEqual(partners[1].name, partner2_name)
        self.assertEqual(partners[0].child_ids, partners[1])
        self.assertEqual(
            set(partners[1].category_id.mapped("name")), {"Prospects", "Services"}
        )

    def test_missing_record(self):
        data = [{"name": str(uuid4()), "country_id|code": "Fake"}]
        pattern_file = self.create_pattern(self.pattern_config_m2m, "import", data)
        partner = self.run_pattern_file(pattern_file)
        self.assertEqual(len(partner), 0)
        self.assertEqual(pattern_file.state, "failed")
        self.assertIn(
            (
                "Fail to process field 'Country'.\n"
                "No value found for model 'Country' with the field 'code' "
                "and the value 'Fake'"
            ),
            pattern_file.chunk_ids.result_info,
        )

    def test_import_m2o_key(self):
        name = str(uuid4())
        ref = str(uuid4())
        data = [{"name": name, "country_id#key|code": "FR", "ref#key": ref}]
        pattern_file = self.create_pattern(self.pattern_config, "import", data)
        partner = self.run_pattern_file(pattern_file)

        self.assertPatternDone(pattern_file)
        self.assertEqual(len(partner), 1)
        self.assertEqual(partner.ref, ref)
        self.assertEqual(partner.name, name)
        self.assertEqual(partner.country_id.code, "FR")

    def test_import_m2o_db_id_key(self):
        name = str(uuid4())
        ref = str(uuid4())
        country = self.env.ref("base.fr")
        data = [{"name": name, "country_id#key|.id": country.id, "ref#key": ref}]
        pattern_file = self.create_pattern(self.pattern_config, "import", data)
        partner = self.run_pattern_file(pattern_file)

        self.assertPatternDone(pattern_file)
        self.assertEqual(len(partner), 1)
        self.assertEqual(partner.name, name)
        self.assertEqual(partner.country_id.code, "FR")

    def test_import_m2o_parents(self):
        """
        Test import works when records reference a parent (=m2o with same model)
         that was defined in a previous row
        """
        data = [
            {"name#key": "Apple"},
            {"name#key": "Steve Jobs", "parent_id|name": "Apple"},
        ]
        pattern_file = self.create_pattern(self.pattern_config, "import", data)
        partners = self.run_pattern_file(pattern_file)
        self.assertEqual(len(partners), 2)
        self.assertEqual(partners[0], partners[1].parent_id)

    def test_update_m2m_with_a_lot_of_item(self):
        unique_name = str(uuid4())
        data = {"name": unique_name}
        for idx in range(1, 15):
            categ_name = "partner_categ_{}".format(idx)
            self.env["res.partner.category"].create({"name": categ_name})
            data["category_id|{}|name".format(idx)] = categ_name
        pattern_file = self.create_pattern(self.pattern_config, "import", [data])
        partner = self.run_pattern_file(pattern_file)
        self.assertEqual(len(partner), 1)
        self.assertEqual(len(partner.category_id), 14)

    @mute_logger("odoo.sql_db")
    def test_partial_import(self):
        data = [
            {"name": "foo"},
            {"name": "bar"},
            {"name": "", "street": "empty"},
            {"name": "foobar"},
        ]
        pattern_file = self.create_pattern(self.pattern_config, "import", data)
        records = self.run_pattern_file(pattern_file)
        self.assertEqual(len(records), 3)
        self.assertEqual(pattern_file.nbr_error, 1)
        self.assertEqual(pattern_file.nbr_success, 3)

    @mute_logger("odoo.sql_db")
    def test_partial_import_too_many_error(self):
        data = (
            [{"name": "foo"}, {"name": "bar"}]
            + [{"name": "", "street": "empty"}] * 15
            + [{"name": "foobar"}]
        )
        pattern_file = self.create_pattern(self.pattern_config, "import", data)
        records = self.run_pattern_file(pattern_file)
        self.assertEqual(len(records), 2)
        self.assertEqual(pattern_file.state, "failed")
        self.assertEqual(pattern_file.nbr_error, 16)
        self.assertIn("Contacts require a name", pattern_file.chunk_ids.result_info)
        self.assertIn("Found more than 10 errors", pattern_file.chunk_ids.result_info)
