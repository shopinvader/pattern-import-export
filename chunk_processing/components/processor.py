# Copyright 2021 Akretion (https://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo.addons.component.core import AbstractComponent


class ChunkProcessor(AbstractComponent):
    _name = "chunk.processor"
    _collection = "chunk.item"

    def _import_item(self):
        raise NotImplementedError

    def _prepare_error_message(self, idx, item, error):
        return {
            "rows": {"from": idx, "to": idx},
            "type": type(error).__name__,
            "message": str(error),
        }

    def run(self):
        res = {"ids": [], "messages": []}
        for idx, item in enumerate(self._parse_data()):
            try:
                with self.env.cr.savepoint():
                    res["ids"] += self._import_item(item)
            except Exception as e:
                if self.env.context.get("chunk_raise_if_exception"):
                    raise
                res["messages"].append(self._prepare_error_message(idx, item, e))
        return res
