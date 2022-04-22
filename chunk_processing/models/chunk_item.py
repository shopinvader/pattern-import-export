# Copyright 2020 Akretion (https://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ChunkItem(models.Model):
    _inherit = "collection.base"
    _name = "chunk.item"
    _description = "Chunk Item"
    _order = "start_idx"
    _rec_name = "start_idx"

    group_id = fields.Many2one(
        "chunk.group", "Chunk Group", required=True, ondelete="cascade"
    )
    start_idx = fields.Integer()
    stop_idx = fields.Integer()
    data = fields.Binary()
    record_ids = fields.Serialized()
    messages = fields.Serialized()
    result_info = fields.Html()
    nbr_error = fields.Integer()
    nbr_success = fields.Integer()
    nbr_item = fields.Integer()
    state = fields.Selection(
        selection=[
            ("pending", "Pending"),
            ("started", "Started"),
            ("done", "Done"),
            ("failed", "Failed"),
        ]
    )
    filename = fields.Char(compute="_compute_filename")

    def _compute_filename(self):
        for record in self:
            record.filename = (
                f"{record.start_idx}-{record.stop_idx}.{record.group_id.data_format}"
            )

    def manual_run(self):
        """ Run the import without try/except, easier for debug """
        return self._run()

    def _run(self):
        with self.work_on(self.group_id.apply_on_model) as work:
            processor = work.component(usage=self.group_id.usage)
            res = processor.run()
            vals = self._prepare_chunk_result(res)
            self.write(vals)

        if not self.group_id.process_multi:
            next_chunk = self.get_next_chunk()
            if next_chunk:
                next_chunk.with_delay(priority=self.group_id.job_priority).run()
            else:
                self.with_delay(priority=5).check_last()
        else:
            self.with_delay(priority=5).check_last()
        return True

    def run(self):
        """Process Chunk Item in a savepoint"""
        cr = self.env.cr
        try:
            self.state = "started"
            cr.commit()  # pylint: disable=invalid-commit
            with cr.savepoint():
                self._run()
        except Exception as e:
            if self._context.get("chunk_raise_if_exception"):
                raise
            else:
                self.write(
                    {
                        "result_info": "Fail to process chunk %s" % e,
                        "nbr_error": self.nbr_item,
                        "state": "failed",
                    }
                )
                self.with_delay().check_last()
        return "OK"

    def _prepare_chunk_result(self, res):
        # TODO rework this part and add specific test case
        nbr_error = len(res["messages"])
        nbr_success = max(self.nbr_item - nbr_error, 0)

        # TODO move this in pattern-import
        # case where error are not return and record are not imported
        nbr_imported = len(res.get("ids") or [])
        if nbr_success > nbr_imported:
            nbr_success = nbr_imported
            nbr_error = self.nbr_item - nbr_imported

        if nbr_error:
            state = "failed"
        else:
            state = "done"
        result = self.env["ir.qweb"]._render("chunk_processing.format_message", res)
        return {
            "record_ids": res.get("ids"),
            "messages": res.get("messages"),
            "result_info": result,
            "state": state,
            "nbr_success": nbr_success,
            "nbr_error": nbr_error,
        }

    def get_next_chunk(self):
        return fields.first(
            self.group_id.item_ids.filtered(lambda s: s.state == "pending")
        )

    def is_last_job(self):
        return not self.group_id.item_ids.filtered(
            lambda s: s.state in ("pending", "started")
        )

    def check_last(self):
        """Check if all chunk have been processed"""
        if self.is_last_job():
            self.group_id.set_done()
            return "Chunk group is done"
        else:
            return "There is still some running chunk"
