# Copyright 2020 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, fields, models


class ImportPatternWizard(models.TransientModel):
    """
    Wizard used to load a file to import using the pattern format.
    The purpose is to read the file to import (with specific format) and
    transform it into a data-structure readable by standard Odoo import.
    """

    _name = "import.pattern.wizard"
    _description = "Import pattern wizard"

    ir_exports_id = fields.Many2one(
        comodel_name="ir.exports",
        string="Import pattern",
        required=True,
        help="Pattern used to import this file (it should be the same "
        "used for the export)",
    )
    import_file = fields.Binary(String="File to import", required=True)
    filename = fields.Char()

    def action_launch_import(self):
        """

        @return: dict/action
        """
        self.ensure_one()
        patterned_import = self.env["patterned.import.export"].create(
            {
                "name": self.filename,
                "datas": self.import_file,
                "datas_fname": self.filename,
                "kind": "import",
                "export_id": self.ir_exports_id.id,
            }
        )

        description = _(
            "Generate import '{model}' with pattern '{export_name}' using "
            "format {format}"
        ).format(
            model=self.ir_exports_id.model_id.model,
            export_name=self.ir_exports_id.name,
            format=self.ir_exports_id.export_format,
        )

        self.ir_exports_id.with_delay(
            description=description
        )._generate_import_with_pattern_job(patterned_import)
        return {}
