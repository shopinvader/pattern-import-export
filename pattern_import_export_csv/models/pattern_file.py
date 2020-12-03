# Copyright 2020 Akretion (https://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import csv
import io

from odoo import models


class PatternFile(models.Model):
    _inherit = "pattern.file"

    def _parse_data_csv(self, datafile):
        in_file = io.StringIO(datafile.decode("utf-8"))
        config = self.pattern_config_id
        if config.use_description:
            # read the first line to skip it
            in_file.readline()
        reader = csv.DictReader(
            in_file,
            delimiter=config.csv_value_delimiter,
            quotechar=config.csv_quote_character,
        )
        for idx, line in enumerate(reader):
            for k, v in line.items():
                if v == "":
                    line[k] = None
            yield idx + 1, line


#    def _process_load_result_for_csv(self, attachment, res):
#        ids = res["ids"] or []
#        info = _("Number of record imported {} Number of error/warning {}").format(
#            len(ids), len(res.get("messages", []))
#        )
#        concatenated_msgs = "\n".join(
#            [
#                "{}: {}".format(message["type"], message["message"])
#                for message in res["messages"]
#            ]
#        )
#        info_detail = _("Details: ids: {},
#            messages: {}".format(ids, concatenated_msgs))
#        if res.get("messages"):
#            state = "fail"
#        else:
#            state = "success"
#        return info, info_detail, state
#
#    def _process_load_result(self, attachment, res):
#        if self.export_format == "csv":
#            return self._process_load_result_for_csv(attachment, res)
#        else:
#            return super()._process_load_result(attachment, res)
#
