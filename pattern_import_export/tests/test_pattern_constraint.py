# Copyright 2020 Akretion France (http://www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import exceptions
from odoo.tests.common import SavepointCase


class TestPatternConstraint(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context={"skip_check": True})
        cls.pattern_config = cls.env["pattern.config"].create(
            {
                "name": "Test Partner",
                "model_id": cls.env.ref("base.model_res_partner").id,
            }
        )

    def _check_case(self, case, expected):
        for name in case:
            line = self.env["ir.exports.line"].create(
                {"export_id": self.pattern_config.export_id.id, "name": name}
            )
        self.assertEqual(line.required_fields, expected)

    def test_field_m2o_required_one_level(self):
        CASE = ["parent_id", "parent_id/name"]
        self._check_case(CASE, "field2_id")

    def test_field_m2o_required_two_level(self):
        CASE = ["parent_id/parent_id", "parent_id/parent_id/name"]
        self._check_case(CASE, "field2_id,field3_id")

    def test_field_m2o_required_three_level(self):
        CASE = ["parent_id/parent_id/parent_id", "parent_id/parent_id/parent_id/name"]
        self._check_case(CASE, "field2_id,field3_id,field4_id")

    def test_field_m2m_required_one_level(self):
        CASE = ["category_id", "category_id/name"]
        self._check_case(CASE, "field2_id,number_occurence")

    def test_field_m2m_required_two_level(self):
        CASE = ["parent_id/category_id", "parent_id/category_id/name"]
        self._check_case(CASE, "field2_id,field3_id,number_occurence")

    def test_field_m2m_required_three_level(self):
        CASE = [
            "parent_id/parent_id/category_id",
            "parent_id/parent_id/category_id/name",
        ]
        self._check_case(CASE, "field2_id,field3_id,field4_id,number_occurence")

    def test_field_o2m_required_one_level(self):
        CASE = ["child_ids"]
        self._check_case(CASE, "number_occurence,sub_pattern_config_id")

    def test_field_o2m_required_two_level(self):
        CASE = ["child_ids/child_ids"]
        self._check_case(CASE, "field2_id,number_occurence,sub_pattern_config_id")

    def test_field_o2m_required_three_level(self):
        CASE = ["child_ids/child_ids/child_ids"]
        self._check_case(
            CASE, "field2_id,field3_id,number_occurence,sub_pattern_config_id"
        )

    def test_create_wrong_pattern(self):
        with self.assertRaises(exceptions.ValidationError) as em:
            self.env["ir.exports.line"].with_context(skip_check=False).create(
                {"export_id": self.pattern_config.export_id.id, "name": "category_id"}
            )
        self.assertEqual(
            em.exception.name, u"The field field2_id is empty for the line category_id"
        )
