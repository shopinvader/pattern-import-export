# Copyright 2020 Akretion France (http://www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import SavepointCase


class TestPatternExport(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super(TestPatternExport, cls).setUpClass()
        exports_select_tab_vals = {
            "name": "Partner Export Test",
            "resource": "res.partner",
        }
        cls.ir_exports_select_tab = cls.env["ir.exports.select.tab"].create(
            exports_select_tab_vals
        )
        exports_line_vals = [
            {"name": "name", "select_tab_id": cls.ir_exports_select_tab.id},
            {"name": "street", "select_tab_id": cls.ir_exports_select_tab.id},
        ]
        cls.ir_exports_line = cls.env["ir.exports.line"].create(exports_line_vals)

    def test_generate_pattern(self):
        self.ir_exports_select_tab.pattern_last_generation_date = False
        self.ir_exports_select_tab.pattern_file = False
        res = self.ir_exports_select_tab.generate_pattern()
        self.assertEqual(res, True)
        self.assertNotEqual(self.ir_exports_select_tab.pattern_file, False)
        self.assertNotEqual(
            self.ir_exports_select_tab.pattern_last_generation_date, False
        )
