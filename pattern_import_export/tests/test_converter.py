# Copyright 2020 Akretion France (http://www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api
from odoo.tests.common import SavepointCase


class TestConvertID(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.converter = cls.env["ir.fields.converter"]

    def _patch_search(self, model_name):
        self.search_domain = []
        search_domain = self.search_domain

        @api.model
        def _search(self, domain, **kwargs):
            search_domain.append(domain)
            return _search.origin(self, domain, **kwargs)

        self.env[model_name]._patch_method("_search", _search)

    def test_list_domain_is_injected(self):
        self.env["res.partner"].create({"name": "foo"})
        model = self.env["res.partner.bank"]
        field = model._fields["partner_id"]
        self._patch_search("res.partner")
        self.converter.db_id_for(model, field, "name", "foo")
        # Odoo add the following domain to partner_id
        # ['|', ('is_company', '=', True), ('parent_id', '=', False)]
        self.assertEqual(
            self.search_domain,
            [
                [
                    "&",
                    "|",
                    ("is_company", "=", True),
                    ("parent_id", "=", False),
                    ("name", "=", "foo"),
                ]
            ],
        )

    def test_string_domain_is_ignored(self):
        model = self.env["res.partner"]
        field = model._fields["state_id"]
        self._patch_search("res.country.state")
        self.converter.db_id_for(model, field, "name", "Rio de Janeiro")
        self.assertEqual(self.search_domain, [[("name", "=", "Rio de Janeiro")]])

    def test_convert_value_to_domain(self):
        field_name = None
        value = {
            "partner_id": {
                "name": "abcdef",
                "phone": "06707507",
                "country_id": {
                    "code": "FR",
                    "name": "France",
                },
                "user_id": {
                    "name": "Someone",
                    "false": False,
                    "true": True,
                    "none": None,
                },
            },
            "direct_value": "some string",
            "another_partner_id": {"name": "abcdef", "phone": "0000000"},
        }
        expected = [
            ["partner_id.name", "=", "abcdef"],
            ["partner_id.phone", "=", "06707507"],
            ["partner_id.country_id.code", "=", "FR"],
            ["partner_id.country_id.name", "=", "France"],
            ["partner_id.user_id.name", "=", "Someone"],
            ["partner_id.user_id.false", "=", False],
            ["partner_id.user_id.true", "=", True],
            ["partner_id.user_id.none", "=", None],
            ["direct_value", "=", "some string"],
            ["another_partner_id.name", "=", "abcdef"],
            ["another_partner_id.phone", "=", "0000000"],
        ]

        result = self.env["res.partner"]._convert_value_to_domain(field_name, value)
        for expectation in expected:
            self.assertIn(expectation, result)
        self.assertEqual(len(expected), len(result))

        # now test with a field_name
        expected2 = [
            ["partner_id.name", "=", "abcdef"],
            ["partner_id.phone", "=", "06707507"],
            ["partner_id.country_id.code", "=", "FR"],
            ["partner_id.country_id.name", "=", "France"],
            ["partner_id.user_id.name", "=", "Someone"],
            ["partner_id.user_id.false", "=", False],
            ["partner_id.user_id.true", "=", True],
            ["partner_id.user_id.none", "=", None],
        ]
        result2 = self.env["res.partner"]._convert_value_to_domain(
            "partner_id", value["partner_id"]
        )
        for expectation in expected2:
            self.assertIn(expectation, result2)
        self.assertEqual(len(expected2), len(result2))
