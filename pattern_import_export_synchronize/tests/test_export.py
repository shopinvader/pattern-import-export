# Copyright 2020 Akretion (http://www.akretion.com).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
# pylint: disable=missing-manifest-dependency
import mock

from odoo.tests import SavepointCase


class TestExport(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.task_export = cls.env.ref(
            "pattern_import_export_synchronize.pattern_export_task"
        )

    def test_run_task_export(self):
        # Mock the file generation
        pattern_file = self.env["pattern.file"].create(
            {
                "name": "foo.csv",
                "datas_fname": "foo.csv",
                "state": "done",
                "pattern_config_id": self.task_export.pattern_config_id.id,
                "kind": "export",
            }
        )
        with mock.patch.object(
            type(self.task_export.pattern_config_id),
            "_export_with_record",
            return_value=pattern_file,
        ):
            self.task_export.with_context(test_queue_job_no_delay=True).run()
        attachment_queue = self.env["attachment.queue"].search(
            [("attachment_id", "=", pattern_file.attachment_id.id)]
        )
        self.assertEqual(len(attachment_queue), 1)
        self.assertEqual(attachment_queue.state, "pending")
        self.assertEqual(attachment_queue.file_type, "export")
        self.assertEqual(attachment_queue.task_id, self.task_export.sync_task_id)

    def test_domain(self):
        user = self.env.ref("base.user_admin")
        self.task_export.filter_id = self.env["ir.filters"].create(
            {
                "name": "Foo",
                "model_id": "res.users",
                "domain": "[('id', '=', {})]".format(user.id),
            }
        )
        exported_user = self.task_export._get_records_to_export()
        self.assertEqual(exported_user, user)

    def test_count_pending_job(self):
        self.assertEqual(self.task_export.count_pending_job, 0)
        self.task_export.run()
        self.task_export.refresh()
        self.assertEqual(self.task_export.count_pending_job, 1)
