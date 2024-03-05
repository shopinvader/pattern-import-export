# Copyright 2023 Akretion (https://www.akretion.com).
# @author Kévin Roche <kevin.roche@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from uuid import uuid4
from odoo.tests.common import SavepointCase
from odoo.addons.pattern_import_export.tests.test_pattern_import import (
    TestPatternImport,
)


class TestPatternImportExportImportType(TestPatternImport):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def test_import_type_update_only(self):
        # simulate a record update with "create only" (fail)
        # then with "update only" (success) import type.
        unique_name = str(uuid4())
        data = [{"login#key": self.user3.login, "name": unique_name}]
        pattern_file = self.create_pattern(self.pattern_config_m2m, "import", data)
        pattern_file.pattern_config_id.import_type = "create_only"
        records = self.run_pattern_file(pattern_file)
        chunk = pattern_file.chunk_ids
        self.assertIn("Import Type not allowing updating record.", chunk.result_info)
        self.assertNotEqual(unique_name, self.user3.name)
        pattern_file.pattern_config_id.import_type = "update_only"
        records = self.run_pattern_file(pattern_file)
        chunk = pattern_file.chunk_ids
        self.assertNotIn("Import Type not allowing", chunk.result_info)
        self.assertEqual(unique_name, self.user3.name)

    def test_import_type_create(self):
        # simulate a record creation with "update only" (fail)
        # then with "update and create" (success) import type.
        unique_name = str(uuid4())
        unique_login = str(uuid4())
        data = [{"name": unique_name, "login": unique_login}]
        pattern_file = self.create_pattern(self.pattern_config_m2m, "import", data)
        pattern_file.pattern_config_id.import_type = "update_only"
        records = self.run_pattern_file(pattern_file)
        chunk = pattern_file.chunk_ids
        self.assertIn("Import Type not allowing record creation.", chunk.result_info)
        self.assertFalse(records)

        pattern_file.pattern_config_id.import_type = "update_and_creation"
        records = self.run_pattern_file(pattern_file)
        chunk = pattern_file.chunk_ids
        self.assertNotIn("Import Type not allowing", chunk.result_info)
        self.assertEqual(len(records), 1)
