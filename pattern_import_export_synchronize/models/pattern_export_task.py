# Copyright 2020 Akretion (https://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class PatternExportTask(models.Model):
    _inherit = "pattern.export.task"

    # TODO filter?
    domain_pattimpex_export = fields.Char(
        string="Domain for filtering records to export", default="[]"
    )
