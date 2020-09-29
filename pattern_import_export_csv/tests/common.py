# Copyright 2020 Akretion France (http://www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
# pylint: disable=missing-manifest-dependency

import io
import base64
from os import path
import csv
# pylint: disable=odoo-addons-relative-import
from odoo.addons.pattern_import_export.tests.common import ExportPatternCommon
from odoo.tests.common import SavepointCase
DEBUG_SAVE_EXPORTS = True
PATH = path.dirname(__file__)
CELL_VALUE_EMPTY = ""
from ..constants import CSV_LINE_DELIMITER, CSV_VAL_DELIMITER
from odoo.addons.queue_job.tests.common import JobMixin


class ExportPatternCsvCommon(JobMixin, SavepointCase):

    def _split_csv_str(self, astring):
        result = []
        virtual_file = io.StringIO(astring)
        for line in csv.reader(virtual_file):
            result.append(line)
        return result

    def _helper_get_resulting_csv(self, export, records):
        export._export_with_record(records)
        attachment = self._get_attachment(export)
        self.assertEqual(attachment.name, export.name + ".csv")
        decoded_data = base64.b64decode(attachment.datas).decode("utf-8")
        if DEBUG_SAVE_EXPORTS:
            full_path = PATH + export.name + ".csv"
            with open(full_path, "wt") as out:
                out.write(decoded_data)
        result = []
        for line in decoded_data.split("\r\n"):
            result.append([val for val in line.split(",")])
        return result
