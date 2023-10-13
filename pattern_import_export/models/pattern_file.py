#  Copyright (c) Akretion 2020
#  License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

import base64
import json
import urllib.parse

from odoo import _, api, fields, models


class PatternFile(models.Model):
    _name = "pattern.file"
    _inherits = {"ir.attachment": "attachment_id"}
    _description = "Attachment with pattern file metadata"
    _order = "id desc"

    attachment_id = fields.Many2one("ir.attachment", required=True, ondelete="cascade")
    state = fields.Selection(
        [("pending", "Pending"), ("failed", "Failed"), ("done", "Done")],
        default="pending",
    )
    info = fields.Char()
    kind = fields.Selection([("import", "import"), ("export", "export")], required=True)
    pattern_config_id = fields.Many2one(
        "pattern.config", required=True, string="Export pattern"
    )
    nbr_error = fields.Integer(compute="_compute_stat")
    nbr_success = fields.Integer(compute="_compute_stat")
    progress = fields.Float(compute="_compute_stat")
    chunk_ids = fields.One2many("pattern.chunk", "pattern_file_id", "Chunk")
    date_done = fields.Datetime()

    @api.depends("chunk_ids.nbr_error", "chunk_ids.nbr_success")
    def _compute_stat(self):
        for record in self:
            record.nbr_error = sum(record.mapped("chunk_ids.nbr_error"))
            record.nbr_success = sum(record.mapped("chunk_ids.nbr_success"))
            todo = sum(record.mapped("chunk_ids.nbr_item"))
            if todo:
                record.progress = (record.nbr_error + record.nbr_success) * 100.0 / todo
            else:
                record.progress = 0

    @api.model_create_multi
    def create(self, vals):
        result = super().create(vals)
        for record in result:
            if record.state != "pending":
                record._notify_user()
        return result

    def write(self, vals):
        result = super().write(vals)
        if "state" in vals.keys() and vals["state"] != "pending":
            for rec in self:
                rec._notify_user()
        return result

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

    def _parse_data(self):
        data = base64.b64decode(self.datas.decode("utf-8"))
        target_function = "_parse_data_{format}".format(
            format=self.pattern_config_id.export_format or ""
        )
        if not hasattr(self, target_function):
            raise NotImplementedError()
        return getattr(self, target_function)(data)

    def _parse_data_json(self, data):
        items = json.loads(data.decode("utf-8"))
        for idx, item in enumerate(items):
            yield idx + 1, item

    def _prepare_chunk(self, start_idx, stop_idx, data):
        return {
            "start_idx": start_idx,
            "stop_idx": stop_idx,
            "data": data,
            "nbr_item": len(data),
            "state": "pending",
            "pattern_file_id": self.id,
        }

    def _should_create_chunk(self, items, next_item):
        """Customise this code if you want to add some additionnal
        item after reaching the limit"""
        return len(items) > self.pattern_config_id.chunk_size

    def _create_chunk(self, start_idx, stop_idx, data):
        vals = self._prepare_chunk(start_idx, stop_idx, data)
        chunk = self.env["pattern.chunk"].create(vals)
        # we enqueue the chunk in case of multi process of if it's the first chunk
        if self.pattern_config_id.process_multi or len(self.chunk_ids) == 1:
            chunk.with_delay(priority=self.pattern_config_id.job_priority).run()
        return chunk

    def split_in_chunk(self):
        """Split Pattern File into Pattern Chunk"""
        # purge chunk in case of retring a job
        self.chunk_ids.unlink()
        try:
            items = []
            start_idx = 1
            previous_idx = None
            # idx is the index position in the original file
            # we can have empty line that can be skipped
            for idx, item in self._parse_data():
                if self._should_create_chunk(items, item):
                    self._create_chunk(start_idx, previous_idx, items)
                    items = []
                    start_idx = idx
                items.append((idx, item))
                previous_idx = idx
            if items:
                self._create_chunk(start_idx, idx, items)
            else:
                # document has an header and no data lines
                # valid document. So create a dummy chunk
                # to have progression and status
                self._create_chunk(-1, -1, [])
        except Exception as e:
            self.state = "failed"
            self.info = _("Failed to create the chunk: %s") % e
        return True

    def set_import_done(self):
        for record in self:
            if record.nbr_error:
                record.state = "failed"
            else:
                record.state = "done"
            record.date_done = fields.Datetime.now()

    def refresh(self):
        """Empty function to refresh view"""
        return True
