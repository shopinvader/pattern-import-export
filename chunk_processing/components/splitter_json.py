# Copyright 2021 Akretion (https://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import json

from odoo.addons.component.core import Component


class ChunkSplitterJson(Component):
    _inherit = "chunk.splitter"
    _name = "chunk.splitter.json"
    _usage = "json"

    def _parse_data(self, data):
        items = json.loads(data.decode("utf-8"))
        for idx, item in enumerate(items):
            yield idx + 1, item
