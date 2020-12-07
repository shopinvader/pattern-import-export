# Copyright 2020 Akretion (http://www.akretion.com).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class AttachmentQueue(models.Model):
    _inherit = "attachment.queue"

    file_type = fields.Selection(
        selection_add=[("import_pattern", "Import using Patterns")]
    )

    def _run_import_pattern(self):
        pattern_file_import = self.env["pattern.file"].create(
            {
                "name": self.name,
                "attachment_id": self.attachment_id.id,
                "kind": "import",
                "pattern_config_id": self.task_id.pattern_config_id.id,
            }
        )
        pattern_file_import.with_delay().split_in_chunk()
        self.state = "done"
        self.state_message = "Pattern file and its job has been created"

    def _run(self):
        super()._run()
        if self.file_type == "import_pattern":
            self._run_import_pattern()
