# Copyright 2020 Akretion France (http://www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo.tests.common import SavepointCase
from odoo import exceptions
from .common import ExportPatternCommon


class TestExportsLine(ExportPatternCommon, SavepointCase):

    def test_constrains_one_key_per_export1(self):
        """
        Ensure the constraint is applied
        @return:
        """
        self.ir_exports.export_fields[0].write({'is_key': True})
        with self.assertRaises(exceptions.ValidationError) as em:
            self.ir_exports.export_fields[1].write({'is_key': True})
        self.assertIn(self.ir_exports.name, em.exception.name)
