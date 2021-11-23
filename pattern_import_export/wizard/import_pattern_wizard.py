# Copyright 2020 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models, api


class ImportPatternWizard(models.TransientModel):
    """
    Wizard used to load a file to import using the pattern format.
    The purpose is to read the file to import (with specific format) and
    transform it into a data-structure readable by standard Odoo import.
    """

    _name = "import.pattern.wizard"
    _description = "Import pattern wizard"

    def _get_model(self):
        model_name = self.env.context.get('active_model')
        active_id = self.env.context.get('active_id')
        if model_name == "pattern.config":
            pattern_config = self.env[model_name].browse(active_id)
            model_name = pattern_config.resource
        return model_name


    pattern_config_id = fields.Many2one(
        comodel_name="pattern.config",
        string="Import pattern",
        required=True,
        help="Pattern used to import this file (it should be the same "
        "used for the export)",
    )
    import_file = fields.Binary(string="File to import", required=True)
    filename = fields.Char()
    model = fields.Char(default=_get_model)
    no_import_pattern = fields.Boolean(compute="_compute_no_import_pattern")

    @api.depends("model")
    def _compute_no_import_pattern(self):
        for wiz in self:
            wiz.no_import_pattern = not wiz.env["pattern.config"].search_count(
                [("resource", "=", wiz.model)]
            )
    def action_launch_import(self):
        """

        @return: dict/action
        """
        self.ensure_one()
        pattern_file_import = self.env["pattern.file"].create(
            {
                "name": self.filename,
                "datas": self.import_file,
                "kind": "import",
                "pattern_config_id": self.pattern_config_id.id,
            }
        )
        pattern_file_import.with_delay(
            priority=self.pattern_config_id.job_priority
        ).split_in_chunk()
        return pattern_file_import
