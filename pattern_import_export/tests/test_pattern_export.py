# Copyright 2020 Akretion France (http://www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields
from odoo.tests.common import SavepointCase


class TestPatternExport(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super(TestPatternExport, cls).setUpClass()
        cls.ir_exports = cls.env["ir.exports.select.tab"].create(
            {"name": "test_ir_exports_select_tab"}
        )

    def test_generate_pattern(self):
        res = self.ir_exports.generate_pattern()
        self.assertEqual(res, True)
        self.assertEqual(self.ir_exports.pattern_file, False)
        self.assertEqual(
            self.ir_exports.pattern_last_generation_date.hour,
            fields.Datetime.now().hour,
        )
