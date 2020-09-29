# Copyright 2020 Akretion France (http://www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
# pylint: disable=missing-manifest-dependency
import csv
import io
from odoo import _, api, fields, models
import base64
from ..constants import CSV_LINE_DELIMITER, CSV_VAL_DELIMITER

class IrExports(models.Model):
    _inherit = "ir.exports"

    export_format = fields.Selection(selection_add=[("csv", "CSV")])

    # CSV Helpers

    def _bytes_to_csv_writer(self, bytes):
        file_fmtd = io.StringIO(bytes.decode("utf-8"))
        return csv.DictWriter(file_fmtd), file_fmtd

    def _csv_stringio_to_bytes(self, stringio):
        stringio.seek(0)
        return stringio.getvalue().encode("utf_8")

    def _attachment_to_csv_writer(self, attachment):
        # Convention for editing CSV file is to slurp it into memory then
        #   modify it, then save it into a new file
        bytes = base64.b64decode(attachment.datas)
        return self._bytes_to_csv_writer(bytes)

    def _bytes_to_csv_reader(self, bytes):
        file_fmtd = io.StringIO(bytes.decode("utf-8"))
        return csv.DictReader(file_fmtd)

    # Export part

    def _write_headers(self, writer):
        if self.use_description:
            writer.writerow(self._get_header(use_description=True))
        writer.writerow(self._get_header(False))

    def _write_rows(self, writer, records):
        for row in self._get_data_to_export(records):
            writer.writerow(row.values())

    @api.multi
    def _export_with_record_csv(self, records):
        self.ensure_one()
        virtual_file = io.StringIO()
        writer = csv.writer(virtual_file)
        self._write_headers(writer)
        self._write_rows(writer, records)
        return self._csv_stringio_to_bytes(virtual_file)

    # Import part

    def _check_csv_has_error_column(self, attachment):
        reader = self._read_import_data_csv(attachment)
        first_line = next(reader, None)
        if first_line[0] == _("#Error"):
            return True
        return False

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
        reader = self._bytes_to_csv_reader(datafile)
        for line in reader:
            for k, v in line.items():
                if v == "":
                    line[k] = None
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