# Copyright 2020 Akretion (http://www.akretion.com).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo.addons.component.tests.common import SavepointComponentCase
from odoo.addons.pattern_import_export_xlsx.tests.common import ExportPatternExcelCommon

# TODO Try to use SyncCommon, currently doesn't work with SavepointCase
#   while parent pattimpex cases need SavepointCase's cls.env in setUpClass
#   (not available in TransactionCase)


class SyncPattimpexCommon(ExportPatternExcelCommon, SavepointComponentCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = cls.env.ref("base.user_admin")
        cls.export = cls.env.ref("pattern_import_export.demo_export_m2m")
        cls.task_export = cls.env.ref(
            "attachment_synchronize_pattimpex.export_to_filestore_pattimpex"
        )
        cls.task_import = cls.env.ref(
            "attachment_synchronize_pattimpex.import_from_filestore_pattimpex"
        )
        cls.backend = cls.env.ref("storage_backend.default_storage_backend")
        cls.task_export_pattimpex = cls.env.ref(
            "attachment_synchronize_pattimpex.export_to_filestore_pattimpex"
        )
        cls.task_import_pattimpex = cls.env.ref(
            "attachment_synchronize_pattimpex.import_from_filestore_pattimpex"
        )
