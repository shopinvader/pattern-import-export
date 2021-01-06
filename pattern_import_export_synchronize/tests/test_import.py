# Copyright 2020 Akretion (http://www.akretion.com).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo.addons.attachment_synchronize.tests.common import SyncCommon


class TestImport(SyncCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.task_import = cls.env.ref(
            "pattern_import_export_synchronize.import_from_filestore"
        )
        cls.pattern_config = cls.env.ref("pattern_import_export.demo_pattern_config")

    def test_run_attachment_queue(self):
        """Test that running an attachment queue creates a correct
        pattern file"""
        # note we only test that running an attachment queue create a correct
        # pattern file. The sync feature and import feature are already tested
        vals = {
            "name": "whatever.csv",
            "datas": b"Y292aWQxOQ==",
            "file_type": "import_pattern",
            "task_id": self.task_import.id,
        }
        attachment_queue = self.env["attachment.queue"].create(vals)

        attachment_queue.run()
        self.assertEqual(attachment_queue.state, "done", attachment_queue.state_message)
        pattern_file = attachment_queue.pattern_file_ids
        self.assertEqual(len(pattern_file), 1)
        self.assertEqual(pattern_file.state, "pending")
