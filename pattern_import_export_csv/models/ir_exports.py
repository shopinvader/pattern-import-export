# Copyright 2020 Akretion France (http://www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
# pylint: disable=missing-manifest-dependency
import base64
import csv
import io
from collections import OrderedDict
from copy import deepcopy

from odoo import _, api, fields, models

from ..constants import CSV_LINE_DELIMITER


def replace_key_in_ordered_dict(a_dict, a_key_to_delete, replacement_key):
    result = OrderedDict(
        [
            (replacement_key, a_dict[a_key_to_delete])
            if k == a_key_to_delete
            else (k, v)
            for k, v in a_dict.items()
        ]
    )
    return result


class IrExports(models.Model):
    _inherit = "ir.exports"

    export_format = fields.Selection(selection_add=[("csv", "CSV")])
    csv_value_delimiter = fields.Char(default=",")
    csv_quote_character = fields.Char(default='"')

    # CSV Helpers

    def _bytes_to_csv_writer(self, bytes_content):
        file_fmtd = io.StringIO(bytes_content.decode("utf-8"))
        return (
            csv.DictWriter(
                file_fmtd,
                delimiter=self.csv_value_delimiter,
                quotechar=self.csv_quote_character,
            ),
            file_fmtd,
        )

    def _csv_stringio_to_bytes(self, stringio):
        stringio.seek(0)
        return stringio.getvalue().encode("utf_8")

    def _attachment_to_csv_writer(self, attachment):
        # Convention for editing CSV file is to slurp it into memory then
        #   modify it, then save it into a new file
        bytes_content = base64.b64decode(attachment.datas)
        return self._bytes_to_csv_writer(bytes_content)

    def _bytes_to_csv_reader(self, bytes_content):
        file_fmtd = io.StringIO(bytes_content.decode("utf-8"))
        return csv.DictReader(
            file_fmtd,
            delimiter=self.csv_value_delimiter,
            quotechar=self.csv_quote_character,
        )

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
        virtual_file = io.StringIO()
        writer = csv.DictWriter(
            virtual_file,
            delimiter=self.csv_value_delimiter,
            quotechar=self.csv_quote_character,
            fieldnames=self._get_header(),
        )
        self._csv_write_headers(writer)
        self._csv_write_rows(writer, records)
        return self._csv_stringio_to_bytes(virtual_file)

    # Import part

    def _csv_make_nondescriptive(self, datafile):
        contents = datafile.decode("utf-8")
        # manually delete first line
        idx_second_line = contents.find(CSV_LINE_DELIMITER) + 1
        contents_no_first_line = contents[idx_second_line:]
        return contents_no_first_line.encode("utf-8")

    def _process_csv_preimport(self, line):
        # TODO see _read_import_data() comment
        # TODO optimizable
        processed = deepcopy(line)
        for k, v in line.items():
            if v == "":
                processed[k] = None
            if k == "id":
                processed = replace_key_in_ordered_dict(processed, "id", ".id")
        return processed

    @api.multi
    def _read_import_data_csv(self, datafile):
        if self.use_description:
            datafile = self._csv_make_nondescriptive(datafile)
        reader = self._bytes_to_csv_reader(datafile)
        for line in reader:
            yield self._process_csv_preimport(line)

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
