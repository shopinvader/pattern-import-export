#  Copyright (c) Akretion 2020
#  License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

import urllib.parse

from odoo import _, api, fields, models


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
    export_id = fields.Many2one("ir.exports", required=True, string="Export pattern")

    @api.model
    def create(self, vals):
        result = super().create(vals)
        if "state" in vals.keys():
            result._notify_user()
        return result

    def write(self, vals):
        result = super().write(vals)
        if "state" in vals.keys():
            for rec in self:
                rec._notify_user()
        return result

    def _notify_user(self):
        import_or_export = "Import" if self.kind == "import" else "Export"
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
        else:
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
            "action="
            + str(self.env.ref("pattern_import_export.action_pattern_file_imports").id),
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
