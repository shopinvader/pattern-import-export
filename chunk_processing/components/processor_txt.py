# Copyright 2021 Akretion (https://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64

from odoo.addons.component.core import AbstractComponent


class ChunkProcessorTxt(AbstractComponent):
    _name = "chunk.importer.txt"
    _inherit = "chunk.processor"
    _collection = "chunk.item"
    _end_of_line = b"\n"

    def _parse_data(self):
        return base64.b64decode(self.collection.data).split(self._end_of_line)
