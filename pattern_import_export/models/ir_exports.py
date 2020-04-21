# Copyright 2020 Akretion France (http://www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class IrExportsLine(models.Model):
    _inherit = "ir.exports.line"

    select_tab_id = fields.Many2one("ir.exports.select.tab", string="Select tab")
    split_nbr = fields.Integer(string="Split nbr")
