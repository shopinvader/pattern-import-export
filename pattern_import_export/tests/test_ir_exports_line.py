# Copyright 2020 Akretion France (http://www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo.tests.common import SavepointCase
from .common import ExportPatternCommon


class TestPatternExport(ExportPatternCommon, SavepointCase):
    def test_check_column_match1(self):
        """
        Ensure the _check_column_match works properly for simple field's name.
        For this case, we ensure the result is correct when fields are
        considered as simple (char, integer etc).
        @return:
        """
        id_line = self.ir_exports.export_fields.filtered(lambda l: l.name == "id")
        name_line = self.ir_exports.export_fields.filtered(lambda l: l.name == "name")
        street_line = self.ir_exports.export_fields.filtered(lambda l: l.name == "street")
        # ID Field
        self.assertTrue(id_line._check_column_match("id"))
        self.assertFalse(id_line._check_column_match("name"))
        self.assertFalse(id_line._check_column_match("ids"))
        self.assertFalse(id_line._check_column_match("company_id/id"))
        self.assertFalse(id_line._check_column_match("1id"))
        self.assertFalse(id_line._check_column_match("id1"))
        # Name Field
        self.assertTrue(name_line._check_column_match("name"))
        self.assertFalse(name_line._check_column_match("id"))
        self.assertFalse(name_line._check_column_match("names"))
        self.assertFalse(name_line._check_column_match("company_id/name"))
        self.assertFalse(name_line._check_column_match("1name"))
        self.assertFalse(name_line._check_column_match("name1"))
        # Street Field
        self.assertTrue(street_line._check_column_match("street"))
        self.assertFalse(street_line._check_column_match("street_id"))
        self.assertFalse(street_line._check_column_match("streets"))
        self.assertFalse(street_line._check_column_match("company_id/street"))
        self.assertFalse(street_line._check_column_match("1street"))
        self.assertFalse(street_line._check_column_match("street1"))

    def test_check_column_match2(self):
        """
        Ensure the _check_column_match works properly for simple field's name.
        For this case, we ensure the result is correct when fields are
        considered as complex (M2M, O2M, M2O).
        @return:
        """
        country_id_line = self.ir_exports.export_fields.filtered(lambda l: l.name == "country_id")
        child_ids_line = self.ir_exports.export_fields.filtered(lambda l: l.name == "child_ids")
        # Country_id Field
        self.assertTrue(country_id_line._check_column_match("country_id"))
        self.assertTrue(country_id_line._check_column_match("country_id/id"))
        self.assertTrue(country_id_line._check_column_match("country_id/name"))
        self.assertTrue(country_id_line._check_column_match("country_id/code"))
        self.assertTrue(country_id_line._check_column_match("country_id/active"))
        self.assertFalse(country_id_line._check_column_match("country_ids"))
        self.assertFalse(country_id_line._check_column_match("country_ids/id"))
        self.assertFalse(country_id_line._check_column_match("country_ids/name"))
        self.assertFalse(country_id_line._check_column_match("country_ids/code"))
        self.assertFalse(country_id_line._check_column_match("country_ids/active"))
        self.assertFalse(country_id_line._check_column_match("country_id|1"))
        self.assertFalse(country_id_line._check_column_match("country_id|1|id"))
        self.assertFalse(country_id_line._check_column_match("country_id|1|name"))
        self.assertFalse(country_id_line._check_column_match("country_id1"))
        self.assertFalse(country_id_line._check_column_match("1country_id"))
