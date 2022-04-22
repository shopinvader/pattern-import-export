# Copyright 2021 Akretion (https://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64

from lxml import objectify

from odoo.addons.component.core import AbstractComponent


class ChunkProcessorXml(AbstractComponent):
    _name = "chunk.importer.xml"
    _inherit = "chunk.processor"
    _collection = "chunk.item"

    def _parse_data(self):
        return objectify.fromstring(
            base64.b64decode(self.collection.data)
        ).iterchildren()
