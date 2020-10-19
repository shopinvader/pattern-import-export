# Copyright 2020 Akretion France (http://www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
# pylint: disable=missing-manifest-dependency
import csv
import io

from odoo import _, api, fields, models

from ..constants import CSV_LINE_DELIMITER


class IrExports(models.Model):
    _inherit = "ir.exports"

    export_format = fields.Selection(selection_add=[("csv", "CSV")])
    csv_value_delimiter = fields.Char(default=",")
    csv_quote_character = fields.Char(default='"')

    # Export part

    def _csv_write_headers(self, writer):
        if self.use_description:
            # note DictWriter needs a dict; uses keys to determine order
            headers_zipped = zip(
                self._get_header(use_description=False),
                self._get_header(use_description=True),
            )
            headers = {k: v for k, v in headers_zipped}
            writer.writerow(headers)
        headers = {k: k for k in self._get_header(use_description=False)}
        writer.writerow(headers)

    def _csv_write_rows(self, writer, records):
        for row in self._get_data_to_export(records):
            writer.writerow(row)

    @api.multi
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

    # Import part

    def _csv_make_nondescriptive(self, datafile):
        contents = datafile.decode("utf-8")
        # manually delete first line
        idx_second_line = contents.find(CSV_LINE_DELIMITER) + 1
        contents_no_first_line = contents[idx_second_line:]
        return contents_no_first_line.encode("utf-8")

    @api.multi
    def _read_import_data_csv(self, datafile):
        if self.use_description:
            datafile = self._csv_make_nondescriptive(datafile)
        reader = csv.DictReader(
            io.StringIO(datafile.decode("utf-8")),
            delimiter=self.csv_value_delimiter,
            quotechar=self.csv_quote_character,
        )
        for line in reader:
            for k, v in line.items():
                if v == "":
                    line[k] = None
            yield line

    def _process_load_result_for_csv(self, attachment, res):
        ids = res["ids"] or []
        info = _("Number of record imported {} Number of error/warning {}").format(
            len(ids), len(res.get("messages", []))
        )
        concatenated_msgs = "\n".join(
            [
                "{}: {}".format(message["type"], message["message"])
                for message in res["messages"]
            ]
        )
        info_detail = _("Details: ids: {}, messages: {}".format(ids, concatenated_msgs))
        if res.get("messages"):
            status = "fail"
        else:
            status = "success"
        return info, info_detail, status

    def _process_load_result(self, attachment, res):
        if self.export_format == "csv":
            return self._process_load_result_for_csv(attachment, res)
        else:
            return super()._process_load_result(attachment, res)
