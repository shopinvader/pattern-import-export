# Copyright 2020 Akretion France (http://www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
# pylint: disable=missing-manifest-dependency
import csv
import io

from odoo import fields, models


class PatternConfig(models.Model):
    _inherit = "pattern.config"

    export_format = fields.Selection(selection_add=[("csv", "CSV")])
    csv_value_delimiter = fields.Char(default=",")
    csv_quote_character = fields.Char(default='"')

    # Export part

    def _csv_write_headers(self, writer):
        if self.use_description:
            # note DictWriter needs a dict; uses keys to determine order
            writer.writerow(
                dict(
                    zip(
                        self._get_header(use_description=False),
                        self._get_header(use_description=True),
                    )
                )
            )
        writer.writerow({k: k for k in self._get_header(use_description=False)})

    def _csv_write_rows(self, writer, records):
        for row in self._get_data_to_export(records):
            writer.writerow(row)

    def _export_with_record_csv(self, records):
        self.ensure_one()
        output = io.StringIO()
        writer = csv.DictWriter(
            output,
            delimiter=self.csv_value_delimiter,
            quotechar=self.csv_quote_character,
            fieldnames=self._get_header(),
        )
        self._csv_write_headers(writer)
        self._csv_write_rows(writer, records)
        output.seek(0)
        return output.getvalue().encode("utf_8")
