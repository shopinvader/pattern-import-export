# Copyright 2021 Akretion (https://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64

from odoo import fields, models


class ChunkGroup(models.Model):
    _inherit = "chunk.group"

    # We use a O2M but as there is a sql constraint we can have only
    # one pattern file, this is why the fieldname end with "id"
    pattern_file_id = fields.One2many("pattern.file", "chunk_group_id", "Pattern File")

    def _get_data(self):
        self.ensure_one()
        if self.pattern_file_id:
            return base64.b64decode(self.pattern_file_id.datas.decode("utf-8"))
        else:
            return super()._get_data()
