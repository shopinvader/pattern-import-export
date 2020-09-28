# Copyright 2020 Akretion France (http://www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
# pylint: disable=missing-manifest-dependency
import csv
import io
from odoo import _, api, fields, models

class IrExports(models.Model):
    _inherit = "ir.exports"

    export_format = fields.Selection(selection_add=[("csv", "CSV")])

    def _write_headers(self, writer):
        if self.use_description:
            writer.writerow(self._get_header(use_description=True))
        writer.writerow(self._get_header(False))

    def _write_rows(self, writer, records):
        for row in self._get_data_to_export(records):
            writer.writerow(row.values())

    @api.multi
    def _create_csv_file(self, records):
        self.ensure_one()
        virtual_file = io.StringIO()
        writer = csv.writer(virtual_file)
        self._write_headers(writer)
        self._write_rows(writer, records)
        return virtual_file

    @api.multi
    def _export_with_record_csv(self, records):
        self.ensure_one()
        csv_contents = self._create_csv_file(records)
        csv_contents.seek(0)
        return csv_contents.getvalue().encode("utf-8")

    # Import part

    @api.multi
    def _read_import_data_csv(self, datafile):
        file_fmtd = io.StringIO(datafile.decode("utf-8"))
        reader = csv.DictReader(file_fmtd)
        for line in reader:
            print(line)
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
