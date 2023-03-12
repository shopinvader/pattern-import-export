# Copyright 2020 Akretion France (http://www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
# pylint: disable=missing-manifest-dependency


# pylint: disable=odoo-addons-relative-import
from odoo.addons.pattern_import_export.tests.test_pattern_export import (
    PatternCaseExport,
)

from .common import CommonPatternExportExcel

CELL_VALUE_EMPTY = None


class TestPatternExportExcel(CommonPatternExportExcel, PatternCaseExport):
    def test_export_tabs(self):
        wb = self._helper_get_resulting_wb(self.pattern_config, self.partners)
        sheets_name = [x.title for x in wb.worksheets]
        sheet_tab_2 = wb[self.tab_name_countries_1]
        sheet_tab_3 = wb["Tags"]
        self.assertEqual(sheets_name, ["Partner", self.tab_name_countries_1, "Tags"])
        expected_values_tab_2 = [["BE"], ["FR"], ["US"], [CELL_VALUE_EMPTY]]
        expected_values_tab_3 = [
            ["Consulting Services"],
            ["Desk Manufacturers"],
            ["Employees"],
            ["Office Supplies"],
            ["Prospects"],
            ["Services"],
            ["Vendor"],
            [CELL_VALUE_EMPTY],
        ]
        self._helper_check_cell_values(sheet_tab_2, expected_values_tab_2)
        self._helper_check_cell_values(sheet_tab_3, expected_values_tab_3)

    def test_export_tabs_name_no_filter(self):
        self.pattern_config.export_fields[3].tab_filter_id = self.env["ir.filters"]
        wb = self._helper_get_resulting_wb(self.pattern_config, self.partners)
        expected_tab_name = "Country"
        self.assertTrue(wb[expected_tab_name])

    def test_export_tabs_name_long_name(self):
        # 32 - 4 = 28 characters, plus "(id) " = 32 characters, the limit
        self.pattern_config.export_fields[
            3
        ].tab_filter_id.name = "CIOIOIOIOIOIOIOIOIOIOIOIOIOI"
        wb = self._helper_get_resulting_wb(self.pattern_config, self.partners)
        expected_tab_name = "({}) " "CIOIOIOIOIOIOIOIOIOIOIOI...".format(
            self.filter_countries_1.id
        )
        self.assertTrue(wb[expected_tab_name])

    def test_export_tabs_with_subpattern(self):
        wb = self._helper_get_resulting_wb(self.pattern_config_o2m, self.partners)
        sheets_name = [x.title for x in wb.worksheets]
        self.assertEqual(len(sheets_name), 3)
        sheet_tab_2 = wb[self.tab_name_countries_1]
        sheet_tab_3 = wb["Tags"]
        self.assertEqual(
            sheets_name, ["Partner with contact", self.tab_name_countries_1, "Tags"]
        )
        expected_values_tab_2 = [["BE"], ["FR"], ["US"], [CELL_VALUE_EMPTY]]
        expected_values_tab_3 = [
            ["Consulting Services"],
            ["Desk Manufacturers"],
            ["Employees"],
            ["Office Supplies"],
            ["Prospects"],
            ["Services"],
            ["Vendor"],
            [CELL_VALUE_EMPTY],
        ]
        self._helper_check_cell_values(sheet_tab_2, expected_values_tab_2)
        self._helper_check_cell_values(sheet_tab_3, expected_values_tab_3)

    def test_export_validators_simple(self):
        wb = self._helper_get_resulting_wb(self.pattern_config, self.partners)
        sheet_base = wb["Partner"]
        self.assertEqual(
            sheet_base.data_validations.dataValidation[0].formula1,
            "='{}'!$A$2:$A$1003".format(self.tab_name_countries_1),
        )
        self.assertEqual(
            str(sheet_base.data_validations.dataValidation[0].cells), "D2:D1003"
        )
        self.assertEqual(
            sheet_base.data_validations.dataValidation[1].formula1,
            "='Tags'!$A$2:$A$1007",
        )
        self.assertEqual(
            str(sheet_base.data_validations.dataValidation[1].cells), "E2:E1003"
        )

    def test_export_validators_simple_with_subpattern(self):
        wb = self._helper_get_resulting_wb(self.pattern_config_o2m, self.partners)
        sheet_base = wb["Partner with contact"]
        self.assertEqual(
            sheet_base.data_validations.dataValidation[0].formula1,
            "='{}'!$A$2:$A$1003".format(self.tab_name_countries_1),
        )
        self.assertEqual(
            str(sheet_base.data_validations.dataValidation[0].cells),
            "F2:F1003 K2:K1003 P2:P1003 R2:R1003",
        )
        self.assertEqual(
            sheet_base.data_validations.dataValidation[1].formula1,
            "='Tags'!$A$2:$A$1007",
        )
        self.assertEqual(
            str(sheet_base.data_validations.dataValidation[1].cells),
            "G2:G1003 L2:L1003 Q2:Q1003",
        )

    def test_export_validators_many2many(self):
        self.pattern_config_m2m.export_fields[2].number_occurence = 3
        wb = self._helper_get_resulting_wb(self.pattern_config_m2m, self.users)
        sheet_base = wb["Users list - M2M"]
        validation = sheet_base.data_validations.dataValidation
        self.assertEqual(len(validation), 1)
        validation = validation[0]
        self.assertEqual(
            validation.formula1,
            "='{}'!$A$2:$A$1003".format(self.tab_name_ignore_one),
        )
        cells_validated = {str(x) for x in validation.cells.ranges}
        self.assertEqual(cells_validated, {"C2:C1003", "D2:D1003", "E2:E1003"})

    def test_export_m2m_tabs(self):
        wb = self._helper_get_resulting_wb(self.pattern_config_m2m, self.users)
        sheet_tab_2 = wb[self.tab_name_ignore_one]
        expected_values_tab_2 = [
            ["Awesome company"],
            ["Bad company"],
            ["YourCompany"],
            [CELL_VALUE_EMPTY],
        ]
        self._helper_check_cell_values(sheet_tab_2, expected_values_tab_2)

    def test_export_m2m_validators(self):
        wb = self._helper_get_resulting_wb(self.pattern_config_m2m, self.users)
        sheet_base = wb["Users list - M2M"]
        self.assertEqual(
            sheet_base.data_validations.dataValidation[0].formula1,
            "='{}'!$A$2:$A$1003".format(self.tab_name_ignore_one),
        )
        self.assertEqual(
            str(sheet_base.data_validations.dataValidation[0].cells), "C2:C1003"
        )
