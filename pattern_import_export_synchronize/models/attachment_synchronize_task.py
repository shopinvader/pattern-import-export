# Copyright 2020 Akretion (http://www.akretion.com).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import fields, models


class AttachmentSynchronizeTask(models.Model):
    _inherit = "attachment.synchronize.task"

    pattern_config_id = fields.Many2one("pattern.config", string="Pattern Config")
