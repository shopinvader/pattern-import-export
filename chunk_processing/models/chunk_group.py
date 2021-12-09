# Copyright 2021 Akretion (https://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo import _, api, fields, models


class ChunkGroup(models.Model):
    _inherit = "collection.base"
    _name = "chunk.group"

    item_ids = fields.One2many("chunk.item", "group_id", "Item")
    process_multi = fields.Boolean()
    job_priority = fields.Integer(default=20)
    chunk_size = fields.Integer(default=500, help="Define the size of the chunk")
    progress = fields.Float(compute="_compute_stat")
    date_done = fields.Datetime()
    data_format = fields.Selection(
        [
            ("json", "Json"),
            ("xml", "XML"),
        ]
    )
    xml_split_xpath = fields.Char()
    state = fields.Selection(
        [("pending", "Pending"), ("failed", "Failed"), ("done", "Done")],
        default="pending",
    )
    info = fields.Char()
    nbr_error = fields.Integer(compute="_compute_stat")
    nbr_success = fields.Integer(compute="_compute_stat")
    apply_on_model = fields.Char()
    usage = fields.Char()

    @api.depends("item_ids.nbr_error", "item_ids.nbr_success")
    def _compute_stat(self):
        for record in self:
            record.nbr_error = sum(record.mapped("item_ids.nbr_error"))
            record.nbr_success = sum(record.mapped("item_ids.nbr_success"))
            todo = sum(record.mapped("item_ids.nbr_item"))
            if todo:
                record.progress = (record.nbr_error + record.nbr_success) * 100.0 / todo
            else:
                record.progress = 0

    def _get_data(self):
        raise NotImplementedError

    def split_in_chunk(self):
        """Split Group into Chunk"""
        # purge chunk in case of retring a job
        self.item_ids.unlink()
        try:
            data = self._get_data()
            with self.work_on(self._name) as work:
                splitter = work.component(usage=self.data_format)
                splitter.run(data)
        except Exception as e:
            self.state = "failed"
            self.info = _("Failed to create the chunk: %s") % e
        return True

    def set_done(self):
        for record in self:
            if record.nbr_error:
                record.state = "failed"
            else:
                record.state = "done"
            record.date_done = fields.Datetime.now()
