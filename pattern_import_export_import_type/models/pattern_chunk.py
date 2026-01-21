# Copyright 2023 Akretion (https://www.akretion.com).
# @author Kévin Roche <kevin.roche@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class PatternChunk(models.Model):
    _inherit = "pattern.chunk"

    def run_import(self):
        import_type = self.pattern_file_id.pattern_config_id.import_type
        return super(
            PatternChunk, self.with_context(pattern_import_type=import_type)
        ).run_import()
