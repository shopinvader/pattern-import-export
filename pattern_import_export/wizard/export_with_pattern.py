# Copyright 2020 Akretion France (http://www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models


class ExportPatternWizard(models.Model):
    _name = "export.pattern.wizard"

    model = fields.Char(
        string="Model to export",
        default=lambda s: s.env.context.get("active_model", False),
    )
    ir_exports_id = fields.Many2one("ir.exports", string="Export Pattern")
    no_export_pattern = fields.Boolean(
        string="No Export Pattern", compute="_compute_no_export_pattern"
    )

    @api.depends("model")
    @api.multi
    def _compute_no_export_pattern(self):
        for wiz in self:
            ir_exports = wiz.env["ir.exports"].search([("resource", "=", wiz.model)])
            if not ir_exports:
                wiz.no_export_pattern = True

    @api.multi
    def run(self):
        for wiz in self:
            description = _("Generate export '%s' with export pattern '%s'") % (
                wiz.model,
                wiz.ir_exports_id.name,
            )
            records = self.env[wiz.model].browse(
                self.env.context.get("active_ids", False)
            )
            job_uuid = records.with_delay(
                description=description
            )._generate_export_with_pattern_job(wiz.ir_exports_id)
        return job_uuid
