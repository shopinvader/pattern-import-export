# Copyright 2021 Akretion (https://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component


class ChunkSplitterTxt(Component):
    _inherit = "chunk.splitter"
    _name = "chunk.splitter.txt"
    _usage = "txt"
    _end_of_line = b"\n"

    def _parse_data(self, data):
        for idx, item in enumerate(data.split(self._end_of_line)):
            if item:
                yield idx + 1, item

    def _convert_items_to_data(self, items):
        return self._end_of_line.join([x[1] for x in items])
