# Copyright 2020 Akretion France (http://www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import ast

from odoo import api, fields, models


class IrExportsSelectTab(models.Model):
    _name = "ir.exports.select.tab"
    _description = "Exports Select Tab"

    name = fields.Char(string="Name", required=True)
    domain = fields.Char(string="Domain")
    model_id = fields.Many2one("ir.model", string="Model", required=True)
    field_id = fields.Many2one("ir.model.fields", string="Field", required=True)

    @api.multi
    def _get_header(self):
        """
        Get the header
        @return: list of string
        """
        self.ensure_one()
        return [self._get_field_label()]

    @api.multi
    def _get_field_label(self):
        """

        @return: str
        """
        return self.env[self.model_id.model]._fields.get(self.field_id.name).string

    @api.multi
    def _get_records_to_export(self):
        """
        Get recordset to export
        @return: recordset
        """
        self.ensure_one()
        field = self.field_id.name
        model = self.model_id.model
        domain = []
        if self.domain:
            domain = ast.literal_eval(self.domain)
        return self.env[model].read_group(
            domain, [field], [field], orderby=field, lazy=False
        )

    @api.multi
    def _get_data_to_export(self):
        """
        Iterator who built data dict record by record
        @return: dict
        """
        for record in self._get_records_to_export():
            data = {}
            for header in self._get_header():
                value = record[self.field_id.name]
                if value and isinstance(value, (list, tuple)):
                    value = value[1]
                data.update({header: value})
            yield data
