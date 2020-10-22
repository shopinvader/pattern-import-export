# Copyright 2020 Akretion (http://www.akretion.com).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from .common import SyncCommon

_logger = logging.getLogger(__name__)


class TestSyncPattimpexExport(SyncCommon):
    def setUp(self):
        super().setUp()
        self.registry.enter_test_mode(self.env.cr)

    def tearDown(self):
        self.registry.leave_test_mode()
        super().tearDown()

    def test_exports_triggered(self):
        """ Test the two steps are triggered:
        1. Export the records in correct format (excel)
        2. Create an attachment.queue type with the correct file (attachment)
           and file_type (simple export) """
        pattimpex_before = self.env["patterned.import.export"].search([])
        att_queue_before = self.env["attachment.queue"].search([])
        self.task_export.service_trigger_exports()
        pattimpex_after = self.env["patterned.import.export"].search(
            [("id", "not in", pattimpex_before.ids)]
        )
        att_queue_after = self.env["attachment.queue"].search(
            [("id", "not in", att_queue_before.ids)]
        )
        self.assertEqual(pattimpex_after.attachment_id, att_queue_after.attachment_id)
        self.assertEqual(att_queue_after.file_type, "export")

    def test_domain_works(self):
        """ Test we get the correct records by specifying export domain
        on the export sync task """
        user = self.task_export._get_records_to_export()
        self.assertEqual(user.name, "Mitchell Admin")
