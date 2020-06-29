# Copyright 2020 Akretion France (http://www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class IrCron(models.Model):
    _inherit = "ir.cron"

    export_attachment_delay = fields.Integer(
        string="Export attachments created since",
        help=u"Autovacuum export attachments created a number of days ago",
    )
