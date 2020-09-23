#  Copyright (c) Akretion 2020
#  License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

from odoo import fields, models


class PatternedImportExport(models.Model):
    _name = "patterned.import.export"
    _inherits = {"ir.attachment": "attachment_id"}
    _description = "Attachment with patterned import/export metadata"

    attachment_id = fields.Many2one("ir.attachment", required=True, ondelete="cascade")
    status = fields.Selection(
        [("pending", "Pending"), ("fail", "Fail"), ("success", "Success")],
        default="pending",
    )
    info = fields.Char()
    info_detail = fields.Char()
    kind = fields.Selection([("import", "import"), ("export", "export")], required=True)
