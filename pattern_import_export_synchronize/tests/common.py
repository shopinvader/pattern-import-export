# Copyright 2020 Akretion (http://www.akretion.com).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo.tests import SavepointCase


class SyncCommon(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = cls.env.ref("base.user_admin")
        cls.export = cls.env.ref("pattern_import_export.demo_export_m2m")
        cls.backend = cls.env.ref("storage_backend.default_storage_backend")
        # cls.task_export_pattimpex = cls.env.ref(
        #    "attachment_synchronize_pattimpex.export_to_filestore_pattimpex"
        # )
        cls.task_import = cls.env.ref(
            "pattern_import_export_synchronize.import_from_filestore_pattimpex"
        )
