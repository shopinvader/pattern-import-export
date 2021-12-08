# Copyright 2021 Akretion (https://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component


class ChunkProcessorPattern(Component):
    _inherit = "chunk.processor"
    _name = "chunk.processor.pattern"
    _usage = "pattern.import"

    def run(self):
        model = self.collection.group_id.apply_on_model
        res = (
            self.env[model]
            .with_context(pattern_config={"model": model, "record_ids": []})
            .load([], self.collection.data)
        )
        self.collection.write(self._prepare_chunk_result(res))

    def _prepare_chunk_result(self, res):
        # TODO rework this part and add specific test case
        nbr_error = len(res["messages"])
        nbr_success = max(self.collection.nbr_item - nbr_error, 0)

        # case where error are not return and record are not imported
        nbr_imported = len(res.get("ids") or [])
        if nbr_success > nbr_imported:
            nbr_success = nbr_imported
            nbr_error = self.collection.nbr_item - nbr_imported

        if nbr_error:
            state = "failed"
        else:
            state = "done"
        result = self.env["ir.qweb"]._render(
            "pattern_import_export.format_message", res
        )
        return {
            "record_ids": res.get("ids"),
            "messages": res.get("messages"),
            "result_info": result,
            "state": state,
            "nbr_success": nbr_success,
            "nbr_error": nbr_error,
        }
