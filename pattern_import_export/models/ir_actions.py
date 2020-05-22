# Copyright 2020 Akretion France (http://www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class IrActions(models.Model):
    _inherit = "ir.actions.actions"

    @api.model
    def get_bindings(self, model_name):
        """ Add an action to all Model objects of the ERP """
        res = super(IrActions, self).get_bindings(model_name)
        action = self.env.ref("pattern_import_export.action_export_with_pattern")
        res["action"].append(action.read()[0])
        return res
