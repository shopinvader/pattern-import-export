# Copyright 2020 Akretion (http://www.akretion.com).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
from os import path

from .common import SyncPattimpexCommon

PATH_BASE = path.dirname(__file__)


class TestSyncPattimpexImport(SyncPattimpexCommon):
    def setUp(self):
        super().setUp()
        self.registry.enter_test_mode(self.env.cr)
        self._clean_testing_directory()
        self._inject_attachment("/fixtures/example.users.xlsx")

    def tearDown(self):
        self.registry.leave_test_mode()
        super().tearDown()

    def _clean_testing_directory(self):
        for file in self.backend._list("test_import_pattimpex/"):
            self.backend._delete(path.join("test_import_pattimpex/", file))

    def _inject_attachment(self, path):
        data = open(PATH_BASE + path, "rb").read()
        attachment_data = base64.b64encode(data)
        vals = {
            "name": "whatever",
            "datas": attachment_data,
            "datas_fname": "example.users.xlsx",
            "export_id": self.export.id,
            "file_type": "import_pattern",
            "task_id": self.task_import_pattimpex.id,
        }
        return self.env["attachment.queue"].create(vals)

    def test_import_pattimpex_created(self):
        """ Test the patterned.import.export is created and state is correctly
        changed"""
        self._inject_attachment("/fixtures/example.users.xlsx")
        pattimpex_before = self.env["patterned.import.export"].search([])
        self.task_import.run_task_import_using_patterns_scheduler_step_2()
        pattimpex_after = self.env["patterned.import.export"].search(
            [("id", "not in", pattimpex_before.ids)]
        )
        self.assertTrue(pattimpex_after)

    def test_import_effective(self):
        self._inject_attachment("/fixtures/example.users.xlsx")
        self.task_import.run_task_import_using_patterns_scheduler_step_2()
        self.assertEqual(self.user.name, "Mitchell Admin Updated")

    def test_import_state_correct(self):
        """ Test the tasks type, attachment.queue type/methods are correctly
        chained and put in context for correct final result """
        attachment = self._inject_attachment("/fixtures/example.users.xlsx")
        self.task_import.run_task_import_using_patterns_scheduler_step_2()
        self.assertEqual(attachment.state, "done")
