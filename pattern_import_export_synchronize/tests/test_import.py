# Copyright 2020 Akretion (http://www.akretion.com).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo.tests import SavepointCase


class TestImport(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Running the attachment_queue is done in a new cursor
        cls.registry.enter_test_mode(cls.env.cr)
        cls.task_import = cls.env.ref(
            "pattern_import_export_synchronize.import_from_filestore"
        )
        cls.pattern_config = cls.env.ref(
            "pattern_import_export.demo_pattern_config_m2m"
        )

    @classmethod
    def tearDownClass(cls):
        cls.registry.leave_test_mode()
        super().tearDownClass()

    def test_run_attachment_queue(self):
        # note we only test that running an attachment queue create a correct
        # pattern file. The sync feature and import feature are already tested
        vals = {
            "name": "whatever.csv",
            "datas": b"Y292aWQxOQ==",
            "datas_fname": "whatever.csv",
            "pattern_config_id": self.pattern_config.id,
            "file_type": "import_pattern",
            "task_id": self.task_import.id,
        }
        attachment_queue = self.env["attachment.queue"].create(vals)

        attachment_queue.run()
        self.assertEqual(attachment_queue.state, "done", attachment_queue.state_message)
        pattern_file = attachment_queue.pattern_file_ids
        self.assertEqual(len(pattern_file), 1)
        self.assertEqual(pattern_file.state, "pending")
