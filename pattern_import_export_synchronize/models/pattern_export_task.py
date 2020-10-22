# Copyright 2020 Akretion (https://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import ast

from odoo import fields, models

from odoo.addons.queue_job.job import job


class PatternExportTask(models.Model):
    _name = "pattern.export.task"
    _description = "Pattern Export Task"

    name = fields.Char()
    filter_id = fields.Many2one("ir.filters")
    export_id = fields.Many2one("ir.exports", string="Pattern Config")
    count_pending_job = fields.Integer(compute="_compute_count_pending_job")
    sync_task_id = fields.Many2one(
        "attachment.synchronize.task",
        "Synchronize Task",
        domain=[("method_type", "=", "export")],
    )

    def _compute_count_pending_job(self):
        for record in self:
            record.count_pending_job = self.env["queue.job"].search_count(
                [
                    ("model_name", "=", self._name),
                    ("method_name", "=", "_run"),
                    ("record_ids", "ilike", "[{}]".format(record.id)),
                ]
            )

    def _get_records_to_export(self):
        if self.filter_id.domain:
            domain = ast.literal_eval(self.filter_id.domain)
        else:
            domain = []
        return self.env[self.export_id.resource].search(domain)

    @job(default_channel="root.exportwithpattern")
    def _run(self):
        self.ensure_one()
        records = self._get_records_to_export()
        pattern_file = records._generate_export_with_pattern_job(self.export_id)
        self.env["attachment.queue"].create(
            {
                "attachment_id": pattern_file.attachment_id.id,
                "task_id": self.sync_task_id.id,
                "file_type": "export",
            }
        )

    def run(self):
        for record in self:
            record.with_delay()._run()
