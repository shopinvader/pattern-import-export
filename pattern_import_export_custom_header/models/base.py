# Copyright (C) 2023 Akretion (<http://www.akretion.com>).
# @author Chafique Delli <chafique.delli@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class Base(models.AbstractModel):
    _inherit = "base"

    def _pattern_format2json(self, row):
        config = self._context["pattern_config"]["pattern_file"].pattern_config_id
        new_row = {
            header.initial_header_name: row.get(header.name)
            or header.import_default_value
            for header in config.custom_header_ids
        }
        if new_row:
            row = new_row
        return super()._pattern_format2json(row=row)
