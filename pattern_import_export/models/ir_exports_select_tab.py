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
        return [self.field_id.name]

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
        return self.env[model].read_group(domain, [field], [field], orderby=field)

    @api.multi
    def _get_data_to_export(self):
        """
        Iterator who built data dict record by record
        @return: dict
        """
        for record in self._get_records_to_export():
            data = {}
            for header in self._get_header():
                data.update({header: record[header]})
            yield data

    @api.multi
    def _generate_additional_sheet(self, book, style):
        for select_tab in self:
            field = select_tab.field_id.name
            sheet_name = "{record_name} ({field})".format(
                record_name=select_tab.name, field=field
            )
            sheet = book.add_worksheet(sheet_name)
            for col, header in enumerate(select_tab._get_header()):
                sheet.write(0, col, header, style)
            row = 1
            for row, values in enumerate(select_tab._get_data_to_export(), start=1):
                for col, value in enumerate(values.values()):
                    sheet.write(row, col, value)
        return sheet, row
