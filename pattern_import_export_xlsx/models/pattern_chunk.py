# Copyright 2022 Akretion (https://www.akretion.com).
# @author Chafique DELLI <chafique.delli@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class PatternChunk(models.Model):
    _inherit = "pattern.chunk"

    def check_last(self):
        res = super().check_last()
        if res == "There is still some running chunk":
            for record in self:
                record.pattern_file_id.write_error_in_xlsx()
        return res
