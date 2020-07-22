# Copyright 2020 Akretion (https://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo import api, models

from odoo.addons.base.models import ir_fields

IDENTIFIER_SURFIXE = "#key"


class IrFieldsConverter(models.AbstractModel):
    _inherit = "ir.fields.converter"

    @api.model
    def for_model(self, model, fromtype=str):
        fn = super().for_model(model, fromtype=fromtype)

        def fn_with_key_support(record, log):
            cleanned = {}
            keyfields = []
            for field, vals in record.items():
                if field.endswith(IDENTIFIER_SURFIXE):
                    field = field.replace(IDENTIFIER_SURFIXE, "")
                    keyfields.append(field)
                cleanned[field] = vals
            converted = fn(cleanned, log)
            for field in keyfields:
                converted["{}{}".format(field, IDENTIFIER_SURFIXE)] = converted.pop(
                    field
                )
            return converted

        return fn_with_key_support

    def _referencing_subfield(self, record):
        try:
            return super()._referencing_subfield(record)
        except ValueError:
            # we allow to match specific field
            fieldset = set(record)
            if len(fieldset) > 1:
                raise
            else:
                [subfield] = fieldset
                return subfield, []

    @api.model
    def db_id_for(self, model, field, subfield, value):
        if subfield in [".id", "id", None]:
            return super().db_id_for(model, field, subfield, value)
        else:
            # TODO finish
            # simple implementation for now
            # we should add warning, manage when having multiple result...
            record = model.search([(subfield, "=", value)])
            return record.id, subfield, []

    @api.model
    def _list_to_many2many(self, model, field, value):
        ids = []
        for item in value:
            [record] = item

            subfield, warnings = self._referencing_subfield(item)

            id, _, ws = self.db_id_for(model, field, subfield, item[subfield])
            ids.append(id)
            warnings.extend(ws)

        if self._context.get("update_many2many"):
            return [ir_fields.LINK_TO(id) for id in ids], warnings
        else:
            return [ir_fields.REPLACE_WITH(ids)], warnings

    @api.model
    def _str_to_many2many(self, model, field, value):
        if isinstance(value, list):
            # TODO it will be great if we can modify odoo to directy call this method
            # odoo/addons/base/models/ir_fields.py:136
            return self._list_to_many2many(model, field, value)
        else:
            return super()._str_to_many2many(model, field, value)

    @api.model
    def _str_to_many2one(self, model, field, value):
        if isinstance(value, dict):
            # odoo expect a list with one item
            value = [value]
        return super()._str_to_many2one(model, field, value)
