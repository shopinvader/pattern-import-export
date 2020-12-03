#  Copyright (c) Akretion 2020
#  License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

import base64
import json
import urllib.parse

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from odoo.addons.queue_job.job import job


class PatternFile(models.Model):
    _name = "pattern.file"
    _inherits = {"ir.attachment": "attachment_id"}
    _description = "Attachment with pattern file metadata"

    attachment_id = fields.Many2one("ir.attachment", required=True, ondelete="cascade")
    state = fields.Selection(
        [("pending", "Pending"), ("fail", "Fail"), ("success", "Success")],
        default="pending",
    )
    info = fields.Char()
    info_detail = fields.Char()
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
        if self.state == "fail":
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
            details += (self.datas_fname and self._helper_build_content_link()) or ""
        return details

    def _helper_build_link(self):
        base = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        web = "/web#"
        args = [
            "action=pattern_import_export.action_pattern_file_imports",
            "id=" + str(self.id),
            "model=pattern.file",
            "view_type=form",
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
            "filename_field=datas_fname",
            "field=datas",
            "download=true",
            "filename=" + urllib.parse.quote(self.datas_fname),
        ]
        link = "<br>"
        url = base + web + "&".join(args)
        link += "<a href=" + url + ">" + _("Download") + "</a>"
        return link

    def enqueue(self):
        description = _(
            "Generate import '{model}' with pattern '{export_name}' using "
            "format {format}"
        ).format(
            model=self.pattern_config_id.model_id.model,
            export_name=self.pattern_config_id.name,
            format=self.pattern_config_id.export_format,
        )
        self.with_delay(description=description).split_in_chunk()

    @api.multi
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
            chunk.with_delay().run()
        return chunk

    @job(default_channel="root.pattern.split_in_chunk")
    def split_in_chunk(self):
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
                items.append(item)
                previous_idx = idx
            if items:
                self._create_chunk(start_idx, idx, items)
        except Exception as e:
            self.state = "fail"
            self.info = _("Failed to read (check details)")
            self.info_detail = e
        return True

    def set_import_done(self):
        for record in self:
            if record.nbr_error:
                record.state = "fail"
                record.post_process_error()
            else:
                record.state = "success"
            record.date_done = fields.Datetime.now()

    def post_process_error(self):
        # TODO maybe we can generate a html report ?
        pass

    def _process_load_message(self, messages):
        count_errors = 0
        count_warnings = 0
        error_message = _(
            "\n Several error have been found "
            "number of errors: {}, number of warnings: {}"
            "\nDetail:\n {}"
        )
        error_details = []
        for message in messages:
            error_details.append(
                _("Line {} : {}, {}").format(
                    message["rows"]["to"], message["type"], message["message"]
                )
            )
            if message["type"] == "error":
                count_errors += 1
            elif message["type"] == "warning":
                count_warnings += 1
            else:
                raise UserError(
                    _("Message type {} is not supported").format(message["type"])
                )
        if count_errors or count_warnings:
            return error_message.format(
                count_errors, count_warnings, "\n".join(error_details)
            )
        return ""

    def refresh(self):
        """Empty function to refresh view"""
        return True
