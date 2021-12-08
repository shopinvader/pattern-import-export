# Copyright 2021 Akretion (https://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo.addons.component.core import AbstractComponent


class ChunkProcessor(AbstractComponent):
    _name = "chunk.processor"
    _collection = "chunk.item"

    def run(self):
        raise NotImplementedError
