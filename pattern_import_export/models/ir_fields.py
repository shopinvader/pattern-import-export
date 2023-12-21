# Copyright 2020 Akretion (https://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import ast

from odoo import _, api, models
from odoo.osv import expression

from odoo.addons.base.models import ir_fields

from .common import IDENTIFIER_SUFFIX


class IrFieldsConverter(models.AbstractModel):
    _inherit = "ir.fields.converter"

    @api.model
    def for_model(self, model, fromtype=str):
        fn = super().for_model(model, fromtype=fromtype)

        def fn_with_key_support(record, log):
            cleanned = {}
            keyfields = []
            for field, vals in record.items():
                if field.endswith(IDENTIFIER_SUFFIX):
                    field = field.replace(IDENTIFIER_SUFFIX, "")
                    keyfields.append(field)
                cleanned[field] = vals
            converted = fn(cleanned, log)
            for field in keyfields:
                converted["{}{}".format(field, IDENTIFIER_SUFFIX)] = converted.pop(
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
        # We alway search on all record even inactive one as we may want to use
        # import feature to active record
        self = self.with_context(active_test=False)
        if subfield in [".id", "id", None]:
            return super().db_id_for(model, field, subfield, value)
        else:
            if value:
                # Only list domain and server-side evaluable are supported
                # as they can be apply on server-side
                if isinstance(field.domain, list):
                    domain = field.domain
                else:
                    try:
                        domain = ast.literal_eval(field.domain)
                    except ValueError:
                        domain = []
                domain = expression.AND([domain, [(subfield, "=", value)]])
                if (
                    self.env.context.get("pattern_config", {}).get("model")
                    == field._related_comodel_name
                ):
                    self._context["import_flush"]()
                record = self.env[field._related_comodel_name].search(domain)
                if len(record) > 1:
                    raise self._format_import_error(
                        ValueError,
                        _(
                            "Fail to process field '%%(field)s'.\n"
                            "Too many records found for '%s' "
                            "with the field '%s' and the value '%s'"
                        ),
                        (_(record._description), subfield, value),
                    )
                elif len(record) == 0:
                    raise self._format_import_error(
                        ValueError,
                        _(
                            "Fail to process field '%%(field)s'.\n"
                            "No value found for model '%s' with the field '%s' "
                            "and the value '%s'"
                        ),
                        (_(record._description), subfield, value),
                    )
            else:
                record = self.env[field._related_comodel_name].browse()
            return record.id, subfield, []

    @api.model
    def _list_to_many2many(self, model, field, value):
        ids = []
        for item in value:
            [record] = item

            subfield, warnings = self._referencing_subfield(item)
            if item[subfield]:
                rec_id, _, ws = self.db_id_for(model, field, subfield, item[subfield])
                ids.append(rec_id)
                warnings.extend(ws)

        if self._context.get("update_many2many"):
            return [ir_fields.LINK_TO(id) for id in ids], warnings
        else:
            return [ir_fields.REPLACE_WITH(ids)], warnings

    @api.model
    def _str_to_many2many(self, model, field, value):
        if isinstance(value, list) and self._context.get("pattern_config"):
            # TODO it will be great if we can modify odoo to directy call this method
            # odoo/addons/base/models/ir_fields.py:136
            return self._list_to_many2many(model, field, value)
        else:
            return super()._str_to_many2many(model, field, value)

    @api.model
    def _str_to_many2one(self, model, field, value):
        if isinstance(value, dict):
            # odoo expect a list with one item
            if len(value) == 1:
                one_value = [value]
                return super()._str_to_many2one(model, field, one_value)
            else:
                domain = model._convert_value_to_domain(None, value)
                tosearch = field._related_comodel_name
                record = self.env[tosearch].search(domain)
                if len(record) > 1:
                    # TODO improve here
                    raise self._format_import_error(
                        ValueError,
                        _("%s Too many records found for %s in field '%s'"),
                        (_(record._description), domain, tosearch),
                    )
                if len(record) == 0:
                    raise self._format_import_error(
                        ValueError,
                        _("%s No matching record found for %s in field '%s'"),
                        (_(record._description), domain, tosearch),
                    )

                # call core function to be sure not to miss something
                an_id, donotcare, w2 = self.db_id_for(model, field, ".id", record.id)
                return an_id, [] + w2
        return super()._str_to_many2one(model, field, value)

    @api.model
    def _str_to_boolean(self, model, field, value):
        if isinstance(value, (int, float)):
            return bool(value), []
        if isinstance(value, bool):
            return value, []
        elif value == "=TRUE()":
            return True, []
        elif value == "=FALSE()":
            return False, []
        elif value is None:
            return False, []
        return super()._str_to_boolean(model, field, value)

    @api.model
    def _str_to_one2many(self, model, field, records):
        if len(records) == 1 and list(records[0].keys()) == [".id"]:
            # In case of import if the len is 1 and there is no
            # other field then id, .id
            # Odoo will considers that the field is a string with
            # a list of ids like "1,3,5"
            # so we have to convert it to a string to avoid
            # raising an error with the split
            # see original method called by super
            records[0][".id"] = str(records[0][".id"])
        commands, warnings = super()._str_to_one2many(model, field, records)
        if self._context.get("pattern_config", {}).get("purge_one2many"):
            commands.insert(0, (5, 0, 0))
        return commands, warnings
