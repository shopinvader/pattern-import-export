# Copyright 2023 Akretion (https://www.akretion.com).
# @author Kévin Roche <kevin.roche@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import copy
from odoo import _, models
from odoo.exceptions import ValidationError


class Base(models.AbstractModel):
    _inherit = "base"

    def _load_records_write(self, values):
        import_type = self._context.get("pattern_import_type")
        if values and import_type and import_type not in ("update_and_creation", "update_only"):
                raise ValidationError(_("Import Type not allowing updating record."))
        else:
            return super()._load_records_write(values)

    def _load_records_create(self, values):
        import_type = self._context.get("pattern_import_type")
        if values and import_type  and import_type not in ("update_and_creation", "create_only"):
                raise ValidationError(_("Import Type not allowing record creation."))
        else:
            return super()._load_records_create(values)
