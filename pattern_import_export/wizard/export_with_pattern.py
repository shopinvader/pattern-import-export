# Copyright 2020 Akretion France (http://www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ExportPatternWizard(models.Model):
    _name = "export.pattern.wizard"

    model = fields.Char(
        string="Model to export",
        default=lambda s: s.env.context.get("active_model", False),
    )
    ir_exports_id = fields.Many2one("ir.exports", string="Export")
    no_export_pattern = fields.Boolean(
        string="No Export Pattern", compute="_compute_no_export_pattern"
    )

    @api.depends("model")
    def _compute_no_export_pattern(self):
        for wiz in self:
            ir_exports = wiz.env["ir.exports"].search(
                [("pattern_file", "!=", False), ("resource", "=", wiz.model)]
            )
            if not ir_exports:
                wiz.no_export_pattern = True

    @api.multi
    def run(self):
        return True
