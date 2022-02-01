# Copyright (C) 2022 Akretion (<http://www.akretion.com>).
# @author Kévin Roche <kevin.roche@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models

from odoo.addons.pattern_import_export.models.common import (
    COLUMN_X2M_SEPARATOR,
    IDENTIFIER_SUFFIX,
)


class PatternConfig(models.Model):
    _inherit = "pattern.config"

    use_custom_header = fields.Boolean(string="Use custom header names")
    custom_header_field_name_ids = fields.One2many(
        comodel_name="pattern.custom.header",
        inverse_name="pattern_id",
        string="Custom Header names",
    )

    def _get_header(self, use_description=False):
        res = super()._get_header()
        if self.use_custom_header and "get_initial_headers" not in self._context:
            for rec in self.custom_header_field_name_ids:
                if rec.initial_header_name:
                    res = [
                        rec.custom_name
                        if (header == rec.initial_header_name and rec.custom_name)
                        else header
                        for header in res
                    ]
                elif rec.custom_name and not rec.initial_header_name:
                    res.append(rec.custom_name)
        return res

    def generate_custom_header_field(self):
        header_field_name_ids = []
        for _idx, rec in enumerate(
            self.with_context(get_initial_headers=True)._get_header(
                self.use_description
            )
        ):
            values = {}
            values["initial_header_name"] = rec
            values["pattern_id"] = self.id
            if self.custom_header_field_name_ids:
                custom_header = self.env["pattern.custom.header"].search(
                    [("pattern_id", "=", self.id), ("initial_header_name", "=", rec)]
                )
                values["custom_name"] = custom_header.custom_name or ""
            header_field_name_ids.append((0, 0, values))
        self.custom_header_field_name_ids = [(6, 0, [])]
        self.write({"custom_header_field_name_ids": header_field_name_ids})
        return

    def json2pattern_format(self, data):
        if self.use_custom_header:
            res = {}
            sorted_headers = self.custom_header_field_name_ids.sorted(
                key=lambda h: h.sequence
            )
            headers = dict(
                zip(
                    sorted_headers.mapped("initial_header_name"),
                    sorted_headers.mapped("custom_name"),
                )
            )
            for header, custom_header in headers.items():
                if header:
                    try:
                        val = data
                        for key in header.split(COLUMN_X2M_SEPARATOR):
                            if key.isdigit():
                                key = int(key) - 1
                            elif IDENTIFIER_SUFFIX in key:
                                key = key.replace(IDENTIFIER_SUFFIX, "")
                            if key == ".id":
                                key = "id"
                            val = val[key]
                            if val is None:
                                break
                    except IndexError:
                        val = None
                    res[custom_header] = val
            return res
        else:
            return super().json2pattern_format(data)


class PatternCustomHeader(models.Model):
    _name = "pattern.custom.header"
    _description = "Pattern custom header"
    _order = "sequence"

    sequence = fields.Integer()
    custom_name = fields.Char(string="Custom Header Name")
    initial_header_name = fields.Char(string="Initial Header Name")
    pattern_id = fields.Many2one("pattern.config")
