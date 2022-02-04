# Copyright (C) 2022 Akretion (<http://www.akretion.com>).
# @author Kévin Roche <kevin.roche@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class PatternConfig(models.Model):
    _inherit = "pattern.config"

    header_format = fields.Selection(
        selection_add=[("custom", "Custom")], ondelete={"custom": "set default"}
    )
    custom_header_ids = fields.One2many(
        comodel_name="pattern.custom.header",
        inverse_name="pattern_id",
        string="Custom Header names",
    )

    def _map_with_custom_header(self, data):
        return {
            item.name: data.get(item.initial_header_name)
            for item in self.custom_header_ids
        }

    def _get_data_to_export_by_record(self, record, parser):
        data = super()._get_data_to_export_by_record(record, parser)
        if self.header_format == "custom":
            return self._map_with_custom_header(data)
        else:
            return data

    def _get_output_headers(self):
        if self.header_format == "custom":
            return [{item.name: item.name for item in self.custom_header_ids}]
        else:
            return super()._get_output_headers()

    def generate_custom_header_field(self):
        header = self._get_header()
        for item in self.custom_header_ids:
            if item.initial_header_name:
                if item.initial_header_name not in header:
                    item.unlink()
                else:
                    header.remove(item.initial_header_name)
        start = max([0] + self.custom_header_ids.mapped("sequence")) + 1
        self.write(
            {
                "custom_header_ids": [
                    (
                        0,
                        0,
                        {
                            "sequence": seq,
                            "initial_header_name": name,
                        },
                    )
                    for seq, name in enumerate(header, start=start)
                ]
            }
        )


class PatternCustomHeader(models.Model):
    _name = "pattern.custom.header"
    _description = "Pattern custom header"
    _order = "sequence"

    sequence = fields.Integer()
    name = fields.Char(compute="_compute_name")
    custom_name = fields.Char(string="Custom Header Name")
    initial_header_name = fields.Char(string="Initial Header Name")
    pattern_id = fields.Many2one("pattern.config", required=True)

    def _compute_name(self):
        for record in self:
            record.name = record.custom_name or record.initial_header_name
