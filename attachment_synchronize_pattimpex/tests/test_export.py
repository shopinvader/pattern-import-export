# Copyright 2020 Akretion (http://www.akretion.com).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from .common import SyncPattimpexCommon

_logger = logging.getLogger(__name__)


class TestSyncPattimpexExport(SyncPattimpexCommon):
    def setUp(self):
        super().setUp()
        self.registry.enter_test_mode(self.env.cr)

    def tearDown(self):
        self.registry.leave_test_mode()
        super().tearDown()

    def test_exports_triggered(self):
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

    def test_domain_works(self):
        user = self.task_export._get_records_to_export()
        self.assertEqual(user.name, "Mitchell Admin")
