# Copyright 2020 Akretion France (http://www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
# pylint: disable=missing-manifest-dependency
import csv
import io
from odoo import _, api, fields, models


class IrExports(models.Model):
    _inherit = "ir.exports"

    export_format = fields.Selection(selection_add=[("csv", "CSV")])

    @api.multi
    def _create_csv_file(self, records):
        self.ensure_one()
        csv_content = io.StringIO()
        writer = csv.writer(csv_content, delimiter=",")
        self._write_headers(writer)
        self._write_rows(writer, records)
        return csv_content

    def _write_headers(self, writer):
        if self.use_description:
            writer.writerow((self._get_header(True)))
        writer.writerow(self._get_header())

    def _write_rows(self, writer, records):
        for row in self._get_data_to_export(records):
            writer.writerow(row.values())

    @api.multi
    def _export_with_record_csv(self, records):
        self.ensure_one()
        csv_file = self._create_csv_file(records)
        return csv_file.getvalue().encode("utf-8")

    # Import part

    @api.multi
    def _read_import_data_csv(self, datafile):
        reader = csv.reader(datafile)
        for line in reader:
            yield line

    def _process_load_result_for_csv(self, attachment, res):
        ids = res["ids"] or []
        info = _(
            "Number of record imported {} Number of error/warning {}"
            "\nrecord ids details: {}"
            "\n{}"
        ).format(
            len(ids),
            len(res.get("messages", [])),
            ids,
            "\n".join(
                [
                    "{}: {}".format(message["type"], message["message"])
                    for message in res["messages"]
                ]
            ),
        )
        if res.get("messages"):
            status = "fail"
        else:
            status = "success"
        return info, status

    def _process_load_result(self, attachment, res):
        if self.export_format == "csv":
            return self._process_load_result_for_csv(attachment, res)
        else:
            return super()._process_load_result(attachment, res)
