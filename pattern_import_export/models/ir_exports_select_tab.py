# Copyright 2020 Akretion France (http://www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class IrExportsSelectTab(models.Model):
    _name = "ir.exports.select.tab"
    _inherit = "ir.exports"

    pattern_file = fields.Binary(string="Pattern file")
    pattern_last_generation_date = fields.Datetime(
        string="Pattern last generation date"
    )
    name = fields.Char(string="Name")
    domain = fields.Char(string="Domain")
    model_id = fields.Many2one("ir.model", string="Model")

    @api.multi
    def generate_pattern(self):
        # Allows you to generate an excel file to be used as
        # a template for the import.
        self.pattern_file = False
        self.pattern_last_generation_date = fields.Datetime.now()
        return True
