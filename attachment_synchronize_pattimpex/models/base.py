# Copyright 2020 Akretion (http://www.akretion.com).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

from odoo import api, models

from odoo.addons.queue_job.job import job

_logger = logging.getLogger(__name__)


class Base(models.AbstractModel):
    _inherit = "base"

    # Export part

    @api.multi
    @job(default_channel="root.exportwithpattern")
    def _generate_export_with_pattern_job(self, export_pattern):
        export = super()._generate_export_with_pattern_job(export_pattern)
        if export.status == "success" and self.env.context.get(
            "export_patterned_attachment_queue"
        ):
            task_id = self.env.context.get("export_patterned_attachment_queue")
            self.env["attachment.queue"].create(
                {
                    "attachment_id": export.attachment_id.id,
                    "file_type": "export",
                    "task_id": task_id,
                    "pattimpex_id": export.id,
                }
            )
        return export
