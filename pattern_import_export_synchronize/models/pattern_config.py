# Copyright 2020 Akretion (https://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class IrExports(models.Model):
    _inherit = "pattern.config"

    import_task_ids = fields.One2many(
        "attachment.synchronize.task",
        "pattern_config_id",
        "Import Task",
        context={"active_test": False},
    )

    export_task_ids = fields.One2many(
        "pattern.export.task",
        "pattern_config_id",
        "Export Task",
        context={"active_test": False},
    )
