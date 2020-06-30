# Copyright 2020 Akretion France (http://www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class IrAttachment(models.Model):
    _inherit = "ir.attachment"

    @api.model
    def _check_contents(self, values):
        # for not force text in mimetype when user is not in system group
        if not self.env.user._is_system() and self.env.context.get(
            "no_check_access_rule", False
        ):
            self = self.sudo()
        return super(IrAttachment, self)._check_contents(values)
