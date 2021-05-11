# Copyright 2021 Akretion (https://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo.tests import SavepointCase


class TestConfig(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def test_create_config(self):
        config = self.env["pattern.config"].create(
            {
                "name": "Partner",
                "resource": "res.partner",
                "export_fields": [
                    (0, 0, {"name": "name"}),
                    (0, 0, {"name": "country_id/code"}),
                    (0, 0, {"name": "ref", "is_key": True}),
                ],
            }
        )
        lines = config.export_fields
        self.assertEqual(lines[0].level, 0)
        self.assertEqual(lines[1].level, 1)
        self.assertEqual(lines[2].level, 0)
