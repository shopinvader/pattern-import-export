#  Copyright (c) Akretion 2020
#  License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

from odoo import fields, models


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
