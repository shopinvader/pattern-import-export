# Copyright 2020 Akretion (http://www.akretion.com).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, fields, models


class AttachmentQueue(models.Model):
    _inherit = "attachment.queue"

    export_id = fields.Many2one("ir.exports")
    file_type = fields.Selection(
        selection_add=[("import_pattern", "Import using Patterns")]
    )
    pattimpex_id = fields.Many2one(
        "patterned.import.export",
        readonly=True,
        string="Patterned Import/Export",
        help="The Patterned Import/Export (and its import job) that was created",
    )

    # Import part

    def _run_import_pattern(self):
        patterned_import = self.env["patterned.import.export"].create(
            {
                "name": self.datas_fname,
                "attachment_id": self.attachment_id.id,
                "kind": "import",
            }
        )
        self.pattimpex_id = patterned_import
        description = _(
            "Generate import '{model}' with pattern '{export_name}' using "
            "format {format}"
        ).format(
            model=self.export_id.model_id.model,
            export_name=self.export_id.name,
            format=self.export_id.export_format,
        )
        self.export_id.with_delay(
            description=description
        )._generate_import_with_pattern_job(patterned_import)
        self.state = "done"
        self.state_message = "Patterned Import Export and its job has been created"

    def _run(self):
        res = super()._run()
        for rec in self:
            if rec.file_type == "import_pattern":
                rec._run_import_pattern()
        return res
