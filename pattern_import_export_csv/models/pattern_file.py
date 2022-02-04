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
        if config.header_format == "description_and_tech":
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
