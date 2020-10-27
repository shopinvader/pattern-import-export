# Copyright 2020 Akretion (http://www.akretion.com).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, fields, models


class AttachmentQueue(models.Model):
    _inherit = "attachment.queue"

    file_type = fields.Selection(
        selection_add=[("import_pattern", "Import using Patterns")]
    )

    def _run_import_pattern(self):
        pattern_file_import = self.env["pattern.file"].create(
            {
                "name": self.datas_fname,
                "attachment_id": self.attachment_id.id,
                "kind": "import",
                "export_id": self.task_id.export_id.id,
            }
        )
        description = _(
            "Generate import '{model}' with pattern '{export_name}' using "
            "format {format}"
        ).format(
            model=pattern_file_import.export_id.model_id.model,
            export_name=pattern_file_import.export_id.name,
            format=pattern_file_import.export_id.export_format,
        )
        pattern_file_import.export_id.with_delay(
            description=description
        )._generate_import_with_pattern_job(pattern_file_import)
        self.state = "done"
        self.state_message = "Pattern file and its job has been created"

    def _run(self):
        super()._run()
        if self.file_type == "import_pattern":
            self._run_import_pattern()
