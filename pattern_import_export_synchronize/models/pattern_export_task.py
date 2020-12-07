# Copyright 2020 Akretion (https://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import ast

from odoo import _, fields, models
from odoo.osv import expression

from odoo.addons.queue_job.job import job


class PatternExportTask(models.Model):
    _name = "pattern.export.task"
    _description = "Pattern Export Task"

    name = fields.Char(required=True)
    filter_id = fields.Many2one("ir.filters")
    pattern_config_id = fields.Many2one(
        "pattern.config", string="Pattern Config", required=True
    )
    sync_task_id = fields.Many2one(
        "attachment.synchronize.task",
        "Synchronize Task",
        domain=[("method_type", "=", "export")],
        required=True,
    )
    count_failed_job = fields.Integer(compute="_compute_count_job")
    count_pending_job = fields.Integer(compute="_compute_count_job")
    count_generated_file = fields.Integer(compute="_compute_count_generated_file")
    pattern_file_ids = fields.One2many("pattern.file", "export_task_id", "Pattern File")
    active = fields.Boolean(default=True)

    def _get_job_domain(self):
        return [
            ("model_name", "=", self._name),
            ("method_name", "=", "_run"),
            ("record_ids", "ilike", "[{}]".format(self.id)),
        ]

    def _compute_count_job(self):
        for record in self:
            domain = record._get_job_domain()
            pending_domain = expression.AND(
                [domain, [("state", "in", ("pending", "started"))]]
            )
            record.count_pending_job = self.env["queue.job"].search_count(
                pending_domain
            )
            failed_domain = expression.AND([domain, [("state", "=", "failed")]])
            record.count_failed_job = self.env["queue.job"].search_count(failed_domain)

    def _compute_count_generated_file(self):
        for record in self:
            record.count_generated_file = len(record.pattern_file_ids)

    def open_failed_job(self):
        return self._open_job(["failed"])

    def open_pending_job(self):
        return self._open_job(["pending", "started"])

    def _open_job(self, states):
        self.ensure_one()
        context = self._context.copy()
        for state in states:
            context["search_default_{}".format(state)] = 1
        return {
            "name": _("Export Job"),
            "view_type": "form",
            "view_mode": "tree,form",
            "res_model": "queue.job",
            "type": "ir.actions.act_window",
            "domain": self._get_job_domain(),
            "context": context,
        }

    def open_generated_file(self):
        return self.pattern_config_id._open_pattern_file(
            [("state", "=", "done"), ("export_task_id", "=", self.id)]
        )

    def _get_records_to_export(self):
        if self.filter_id.domain:
            domain = ast.literal_eval(self.filter_id.domain)
        else:
            domain = []
        return self.env[self.pattern_config_id.resource].search(domain)

    @job(default_channel="root.pattern.export")
    def _run(self):
        self.ensure_one()
        records = self._get_records_to_export()
        pattern_file = records._generate_export_with_pattern_job(self.pattern_config_id)
        pattern_file.export_task_id = self
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

    def button_duplicate_record(self):
        # due to orm limitation method call from ui should not have params
        # so we need to define this method to be able to copy
        # if we do not do this the context will be injected in default params
        # in V14 maybe we can call copy directly
        self.copy()

    def copy(self, default=None):
        if default is None:
            default = {}
        if "active" not in default:
            default["active"] = False
        return super().copy(default=default)
