# Copyright 2023 Akretion (https://www.akretion.com).
# @author Kévin Roche <kevin.roche@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class PatternConfig(models.Model):
    _inherit = "pattern.config"

    import_type = fields.Selection(
        selection=[
            ("update_and_creation", "Update and Creation"),
            ("update_only", "Update Only"),
            ("create_only", "Creation Only"),
        ],
        string="Import Type",
        default="update_and_creation",
    )
