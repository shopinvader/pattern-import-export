# Copyright 2020 Akretion France (http://www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models


class IrExportsLine(models.Model):
    _inherit = "ir.exports.line"

    def _add_xlsx_constraint(self, sheet, col, ad_sheet, ad_row):
        source = "=" + ad_sheet.name + "!$A$2:$A$" + str(ad_row + 100)
        sheet.data_validation(
            1, col, 1048576, col, {"validate": "list", "source": source}
        )
        return True
