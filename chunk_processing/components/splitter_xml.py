# Copyright 2021 Akretion (https://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from lxml import etree

from odoo.addons.component.core import Component


class ChunkSplitterXml(Component):
    _inherit = "chunk.splitter"
    _name = "chunk.splitter.xml"
    _usage = "xml"

    def _parse_data(self, data):
        tree = etree.fromstring(data)
        items = tree.xpath(self.collection.xml_split_xpath)
        for idx, item in enumerate(items):
            yield idx + 1, item

    def _convert_items_to_data(self, items):
        data = etree.Element("data")
        for item in items:
            data.append(item[1])
        return etree.tostring(data)
