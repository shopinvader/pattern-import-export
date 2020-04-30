# Copyright 2020 Akretion France (http://www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class IrExportsSelectTab(models.Model):
    _name = "ir.exports.select.tab"
    _description = "Exports Select Tab"

    name = fields.Char(string="Name")
    field_id = fields.Many2one(
        "ir.model.fields", string="Field", domain="[('model_id', '=', model_id)]"
    )
    domain = fields.Char(string="Domain")
    model_id = fields.Many2one("ir.model", string="Model")
