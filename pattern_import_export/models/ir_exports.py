# Copyright 2020 Akretion France (http://www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class IrExports(models.Model):
    _inherit = "ir.exports"

    pattern_config_id = fields.Many2one(
        "pattern.config", compute="_compute_pattern_config_id"
    )

    def _compute_pattern_config_id(self):
        for rec in self:
            rec.pattern_config_id = self.env["pattern.config"].search(
                [("export_id", "=", rec.id)]
            )
