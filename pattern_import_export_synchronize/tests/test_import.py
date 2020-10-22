# Copyright 2020 Akretion (http://www.akretion.com).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from .common import SyncCommon


class TestSyncPattimpexImport(SyncCommon):
    def setUp(self):
        super().setUp()
        # Running the attachment_queue is done in a new cursor
        self.registry.enter_test_mode(self.env.cr)

    def tearDown(self):
        self.registry.leave_test_mode()
        super().tearDown()

    def test_run_attachment_queue(self):
        # note we only test that running an attachment queue create a correct
        # pattern file. The sync feature and import feature are already tested
        vals = {
            "name": "whatever",
            "datas": b"Y292aWQxOQ==",
            "datas_fname": "whatever.csv",
            "export_id": self.export.id,
            "file_type": "import_pattern",
            "task_id": self.task_import.id,
        }
        attachment_queue = self.env["attachment.queue"].create(vals)

        attachment_queue.run()
        self.assertEqual(attachment_queue.state, "done", attachment_queue.state_message)
        pattern_file = attachment_queue.pattern_file_ids
        self.assertEqual(len(pattern_file), 1)
        self.assertEqual(pattern_file.status, "pending")
