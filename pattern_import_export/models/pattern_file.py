#  Copyright (c) Akretion 2020
#  License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

import urllib.parse

from odoo import _, api, fields, models


class PatternFile(models.Model):
    _name = "pattern.file"
    _inherits = {"ir.attachment": "attachment_id"}
    _description = "Attachment with pattern file metadata"

    attachment_id = fields.Many2one("ir.attachment", required=True, ondelete="cascade")
    kind = fields.Selection([("import", "import"), ("export", "export")], required=True)
    pattern_config_id = fields.Many2one(
        "pattern.config", required=True, string="Export pattern"
    )
    chunk_group_id = fields.Many2one("chunk.group")
    chunk_item_ids = fields.One2many("chunk.item", related="chunk_group_id.item_ids")
    state = fields.Selection(
        [("pending", "Pending"), ("failed", "Failed"), ("done", "Done")],
        compute="_compute_state",
    )
    date_done = fields.Date(compute="_compute_date_done", store=True)
    progress = fields.Float(related="chunk_group_id.progress")
    nbr_error = fields.Integer(related="chunk_group_id.nbr_error")
    nbr_success = fields.Integer(related="chunk_group_id.nbr_success")
    info = fields.Char(related="chunk_group_id.info")

    _sql_constraints = [
        ("uniq_group_id", "unique(group_id)", "The Group must be unique!")
    ]

    def _add_chunk_group(self):
        for record in self:
            config = record.pattern_config_id
            record.chunk_group_id = self.env["chunk.group"].create(
                {
                    "job_priority": config.job_priority,
                    "process_multi": config.process_multi,
                    "data_format": "json",
                    "apply_on_model": config.resource,
                    "usage": "pattern.import",
                }
            )

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._add_chunk_group()
        return records

    @api.depends("kind", "chunk_group_id.date_done")
    def _compute_date_done(self):
        for record in self:
            if record.kind == "export" and not record.date_done:
                record.date_done = fields.Date.today()
            elif record.kind == "import":
                record.date_done = record.chunk_group_id.date_done

    @api.depends("kind", "chunk_group_id.state")
    def _compute_state(self):
        for record in self:
            if record.kind == "export":
                record.state = "done"
            elif record.kind == "import":
                record.state = record.chunk_group_id.state
            record._notify_user()

    def _notify_user(self):
        import_or_export = _("Import") if self.kind == "import" else _("Export")
        details = self._helper_build_details()
        if self.state == "failed":
            self.env.user.notify_danger(
                message=_(
                    "{} job has failed. \nFor more details: {}".format(
                        import_or_export, details
                    )
                ),
                sticky=True,
            )
        elif self.state == "done":
            self.env.user.notify_success(
                message=_(
                    "{} job has finished. \nFor more details: {}".format(
                        import_or_export, details
                    )
                ),
                sticky=True,
            )

    def _helper_build_details(self):
        details = self._helper_build_link()
        if self.kind == "export":
            details += (self.name and self._helper_build_content_link()) or ""
        return details

    def _helper_build_link(self):
        base = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        web = "/web#"
        args = [
            "action=pattern_import_export.action_pattern_file_imports",
            "id=" + str(self.id),
            "model=pattern.file",
            "menu_id="
            + str(self.env.ref("pattern_import_export.import_export_menu_root").id),
        ]
        link = "<br>"
        url = base + web + "&".join(args)
        link += "<a href=" + url + ">" + _("View Job") + "</a>"
        return link

    def _helper_build_content_link(self):
        base = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        web = "/web/content/"
        args = [
            "?model=" + "pattern.file",
            "id=" + str(self.id),
            "filename_field=name",
            "field=datas",
            "download=true",
            "filename=" + urllib.parse.quote(self.name),
        ]
        link = "<br>"
        url = base + web + "&".join(args)
        link += "<a href=" + url + ">" + _("Download") + "</a>"
        return link

    def split_in_chunk(self):
        return self.chunk_group_id.split_in_chunk()

    def refresh(self):
        """Empty function to refresh view"""
        return True
