# Copyright 2021 Akretion (https://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import AbstractComponent


class ChunkSplitter(AbstractComponent):
    _name = "chunk.splitter"
    _collection = "chunk.group"

    def _parse_data(self, data):
        raise NotImplementedError

    def _prepare_chunk(self, start_idx, stop_idx, data):
        return {
            "start_idx": start_idx,
            "stop_idx": stop_idx,
            "data": data,
            "nbr_item": len(data),
            "state": "pending",
            "group_id": self.collection.id,
        }

    def _should_create_chunk(self, items, next_item):
        """Customise this code if you want to add some additionnal
        item after reaching the limit"""
        return len(items) > self.collection.chunk_size

    def _create_chunk(self, start_idx, stop_idx, data):
        vals = self._prepare_chunk(start_idx, stop_idx, data)
        chunk = self.env["chunk.item"].create(vals)
        # we enqueue the chunk in case of multi process of if it's the first chunk
        if self.collection.process_multi or len(self.collection.item_ids) == 1:
            chunk.with_delay(priority=self.collection.job_priority).run()
        return chunk

    def run(self, data):
        items = []
        start_idx = 1
        previous_idx = None
        for idx, item in self._parse_data(data):
            if self._should_create_chunk(items, item):
                self._create_chunk(start_idx, previous_idx, items)
                items = []
                start_idx = idx
            items.append((idx, item))
            previous_idx = idx
        if items:
            self._create_chunk(start_idx, idx, items)
