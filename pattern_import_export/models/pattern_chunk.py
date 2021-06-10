# Copyright 2020 Akretion (https://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class PatternChunk(models.Model):
    _name = "pattern.chunk"
    _description = "Pattern Chunk"
    _order = "start_idx"
    _rec_name = "start_idx"

    pattern_file_id = fields.Many2one(
        "pattern.file", "Pattern File", required=True, ondelete="cascade"
    )
    start_idx = fields.Integer()
    stop_idx = fields.Integer()
    data = fields.Serialized()
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

    def run(self):
        """Process Import of Pattern Chunk"""
        cr = self.env.cr
        try:
            self.state = "started"
            cr.commit()  # pylint: disable=invalid-commit
            with cr.savepoint():
                model = self.pattern_file_id.pattern_config_id.model_id.model
                res = (
                    self.with_context(pattern_config={"model": model, "record_ids": []})
                    .env[model]
                    .load([], self.data)
                )
                self.write(self._prepare_chunk_result(res))
                config = self.pattern_file_id.pattern_config_id
                priority = config.job_priority
                if not config.process_multi:
                    next_chunk = self.get_next_chunk()
                    if next_chunk:
                        next_chunk.with_delay(priority=priority).run()
                    else:
                        self.with_delay(priority=5).check_last()
                else:
                    self.with_delay(priority=5).check_last()

        except Exception as e:
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

        # case where error are not return and record are not imported
        nbr_imported = len(res.get("ids") or [])
        if nbr_success > nbr_imported:
            nbr_success = nbr_imported
            nbr_error = self.nbr_item - nbr_imported

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

    def get_next_chunk(self):
        return self.search(
            [
                ("pattern_file_id", "=", self.pattern_file_id.id),
                ("state", "=", "pending"),
            ],
            limit=1,
        )

    def is_last_job(self):
        return not self.pattern_file_id.chunk_ids.filtered(
            lambda s: s.state in ("pending", "started")
        )

    def check_last(self):
        """Check if all chunk have been processed"""
        if self.is_last_job():
            self.pattern_file_id.set_import_done()
            return "Pattern file is done"
        else:
            return "There is still some running chunk"
