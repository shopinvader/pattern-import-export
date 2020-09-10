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
