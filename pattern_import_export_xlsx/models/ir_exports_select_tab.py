# Copyright 2020 Akretion France (http://www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, models


class IrExportsSelectTab(models.Model):
    _inherit = "ir.exports.select.tab"

    @api.multi
    def _generate_additional_sheet(self, book, style):
        for select_tab in self:
            field = select_tab.field_id.name
            sheet_name = "{record_name} ({field})".format(
                record_name=select_tab.name, field=field
            )
            sheet = book.add_worksheet(sheet_name)
            for col, header in enumerate(select_tab._get_header()):
                sheet.write(0, col, header, style)
            row = 1
            for row, values in enumerate(select_tab._get_data_to_export(), start=1):
                for col, value in enumerate(values.values()):
                    sheet.write(row, col, value)
        return sheet, row

    def _add_xlsx_constraint(self, sheet, col, ad_sheet, ad_row):
        source = "=" + ad_sheet.name + "!$A$2:$A$" + str(ad_row + 100)
        sheet.data_validation(
            1, col, 1048576, col, {"validate": "list", "source": source}
        )
        return True
