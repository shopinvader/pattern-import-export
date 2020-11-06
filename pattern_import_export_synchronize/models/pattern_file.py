# Copyright 2020 Akretion (https://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo import fields, models


class PatternFile(models.Model):
    _inherit = "pattern.file"

    export_task_id = fields.Many2one("pattern.export.task", "Export Task")
    attachment_queue_ids = fields.Many2many(
        comodel_name="attachment.queue",
        string="Attachment Queue",
        compute="_compute_attachment_queue_ids",
    )

    def _compute_attachment_queue_ids(self):
        for record in self:
            record.attachment_queue_ids = self.env["attachment.queue"].search(
                [("attachment_id", "=", record.attachment_id.id)]
            )
