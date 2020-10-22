# Copyright 2020 Akretion (https://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class IrExports(models.Model):
    _inherit = "ir.exports"

    import_task_ids = fields.One2many(
        "attachment.synchronize.task", "export_id", "Import Task"
    )
