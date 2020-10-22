# Copyright 2020 Akretion (http://www.akretion.com).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

from odoo import api, fields, models
from odoo.osv import expression
from odoo.tools import safe_eval

_logger = logging.getLogger(__name__)


class AttachmentSynchronizeTask(models.Model):
    _inherit = "attachment.synchronize.task"

    export_id = fields.Many2one("ir.exports", string="Import/Export pattern")

    # Export part

    def _get_records_to_export(self):
        model_name = self.export_id.resource
        domain = safe_eval(self.domain_pattimpex_export)
        return self.env[model_name].search(domain)

    def service_trigger_exports(self):
        records = self._get_records_to_export()
        records.with_context(
            self.env.context, export_patterned_attachment_queue=self.id
        )._generate_export_with_pattern_job(self.export_id)

    # Import part

    def _prepare_attachment_vals(self, data, filename):
        vals = super()._prepare_attachment_vals(data, filename)
        export_id = self.env.context.get("pattern_export_id")
        if export_id:
            vals["export_id"] = export_id
            vals["file_type"] = "import_pattern"
        return vals

    @api.model
    # TODO rename ?
    def run_task_import_using_patterns_scheduler_step_1(self, domain=None):
        if domain is None:
            domain = []
        domain = expression.AND(
            [domain, [("method_type", "=", "import_pattern"), ("enabled", "=", True)]]
        )
        for task in self.search(domain):
            task.run_import()  # Runs the import storage -> attachment.queues

    @api.model
    # TODO rename ?
    def run_task_import_using_patterns_scheduler_step_2(self, domain=None):
        if domain is None:
            domain = []
        domain = expression.AND(
            [domain, [("method_type", "=", "import_pattern"), ("enabled", "=", True)]]
        )
        for task in self.search(domain):
            task = task.with_context(
                self.env.context, pattern_export_id=task.export_id and task.export_id.id
            )
            task.run_export()  # Careful ! This is a misnomer; run_export simply run()s
            # associated attachment.queue. It is not specifically an export. This will
            # run imports because the file types are "import_pattern".
            # Alternatively, just consider the "export" is exporting INTO Odoo...
