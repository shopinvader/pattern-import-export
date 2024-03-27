# Copyright 2020 Akretion France (http://www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import copy
import logging

from odoo import _, api, models
from odoo.exceptions import ValidationError
from odoo.osv import expression

from .common import IDENTIFIER_SUFFIX

_logger = logging.getLogger(__name__)

FLOAT_INF = float("inf")


def is_not_empty(item):
    if not item:
        return False
    elif isinstance(item, dict):
        for key in item:
            if is_not_empty(item[key]):
                return True
    elif isinstance(item, list):
        for subitem in item:
            if is_not_empty(subitem):
                return True
    else:
        return True


class Base(models.AbstractModel):
    _inherit = "base"

    def generate_export_with_pattern_job(self, export_pattern):
        export = export_pattern._export_with_record(self)
        return export

    # There is a native bug in odoo
    # when load records if it fail odoo will rollback and try to load them one by one
    # in order to have explicit error
    # The issue is if the create/write method modify the dict vals
    # the modification will be kept and this can generate issue when loading one by one
    # Do a deepcopy to avoid this issue
    # TODO try to reproduce it on native odoo and open a ticket

    def _load_records_write(self, values):
        return super()._load_records_write(copy.deepcopy(values))

    def _load_records_create(self, values):
        return super()._load_records_create(copy.deepcopy(values))

    def _load_records(self, data_list, update=False):
        records = super()._load_records(data_list, update=update)
        if self._context.get("pattern_config"):
            self._context["pattern_config"]["record_ids"] += records.ids
        return records

    def load(self, fields, data):
        result = super().load(fields, data)
        if not result["ids"] and self._context.get("pattern_config", {}).get(
            "record_ids"
        ):
            result["ids"] = self._context["pattern_config"]["record_ids"]
        return result

    def _pattern_format2json(self, row):
        def convert_header_key(key):
            return [int(k) if k.isdigit() else k for k in key.split("|")]

        for key in ["id", ".id"]:
            if key in row and row[key] is None:
                row.pop(key)
        res = {}
        items = [(convert_header_key(k), v) for k, v in row.items()]
        items.sort()
        for keys, vals in items:
            current = res
            previous_key = None
            for key in keys:
                if not previous_key:
                    previous_key = key
                elif isinstance(key, int):
                    if previous_key not in current:
                        current[previous_key] = []
                    if len(current[previous_key]) < key:
                        current[previous_key].append({})
                    try:
                        current = current[previous_key][key - 1]
                    except IndexError:
                        raise
                elif not isinstance(previous_key, int):
                    if previous_key not in current:
                        current[previous_key] = {}
                    current = current[previous_key]
                previous_key = key
            current[keys[-1]] = vals
        return self._post_process_key(res)

    def _clean_identifier_key(self, res, ident_keys):
        for key in ident_keys:
            if key in res:
                res[key.replace(IDENTIFIER_SUFFIX, "")] = res.pop(key)

    def _convert_value_to_domain(self, field_name, value):
        # fieldname may be None
        # todo: rename field_name to prefix
        if isinstance(value, dict):
            domain = []
            subdom = []
            for key, val in value.items():
                if key == ".id":
                    # .id is internal db id, so we rename it
                    key = "id"
                # field_name may be None
                # then key = value directly
                dom_key = f"{field_name}.{key}" if field_name else key
                subdom += self._convert_value_to_domain(dom_key, val)
            domain = subdom
        else:
            domain = [[field_name, "=", value]]
        return domain

    def _get_domain_from_identifier_key(self, res):
        ident_keys = []
        domain = []
        for key in list(res.keys()):
            if key.endswith(IDENTIFIER_SUFFIX):
                field_name = key.replace(IDENTIFIER_SUFFIX, "")
                domain += self._convert_value_to_domain(field_name, res[key])
                ident_keys.append(key)
        return domain, ident_keys

    # TODO add test with FakeModel
    # Case of use
    # If you try to import a One2many on the product.product model and this
    # o2m is define on the product.template
    # in that case we need to found the right left domain
    #  "product_tmpl_id.product_variant_ids"
    # So we need to recurcively build this domain
    # if the o2m is not inherited, we get the left domain by just reading
    # the inverse_name
    def _get_subdomain_field(self, field):
        if field.inherited:
            inherited_field = field.inherited_field
            model_name = inherited_field.model_name
            fieldname = self.env[model_name]._get_subdomain_field(inherited_field)
            related_field = self._field_inverses[
                self._fields[self._inherits[model_name]]
            ][0]
            return f"{fieldname}.{related_field.name}"
        else:
            return field.inverse_name
        return None

    def _post_process_o2m_fields(self, res, parent_do_not_exist):
        """Post process one2many field
        - remove all empty item
        - post process key on each valid item (with the parent_id in domain)
        """
        if ".id" in res:
            parent_id = res[".id"]
        elif "id" in res:
            parent_id = self.env.ref(res["id"]).id
        else:
            parent_id = None

        for key in res:
            field = self._fields.get(key)
            if field and field.type == "one2many":
                subdomain = []
                if parent_id:
                    subdomain.append((self._get_subdomain_field(field), "=", parent_id))
                # empty subitem are removed
                valid_subitems = []
                for subitem in res[key]:
                    if is_not_empty(subitem):
                        valid_subitems.append(subitem)
                        self.env[field._related_comodel_name]._post_process_key(
                            subitem, subdomain, not bool(parent_id)
                        )
                res[key] = valid_subitems

    def _set_record_id_from_domain(self, res, ident_keys, domain):
        record = self.with_context(active_test=False).search(domain)
        if len(record) > 1:
            raise ValidationError(
                _("Too many {} found for the key/value : {}").format(
                    _(record._description), {k: res[k] for k in ident_keys}
                )
            )
        elif record:
            res[".id"] = record.id
            # we remove the key as rewriting the same value is useless
            for key in ident_keys:
                res.pop(key)

    def _post_process_key(self, res, domain=None, parent_do_not_exist=False):
        """Process identifier key
        - search existing record and inject id
        - remove #key for dict key
        """
        if domain is None:
            domain = []
        domain_key, ident_keys = self._get_domain_from_identifier_key(res)

        if domain_key and not parent_do_not_exist:
            full_domain = expression.AND([domain, domain_key])
            self._set_record_id_from_domain(res, ident_keys, full_domain)

        self._post_process_o2m_fields(res, parent_do_not_exist=parent_do_not_exist)
        self._clean_identifier_key(res, ident_keys)
        return res

    def _remove_commented_and_empty_columns(self, row):
        for key in list(row.keys()):
            if key is None:
                row.pop(None)
            elif key.startswith("#"):
                row.pop(key)

    def _strip_string(self, row):
        for key in row:
            if isinstance(row[key], str):
                row[key] = row[key].strip()

    @api.model
    def _extract_records(self, fields_, data, log=lambda a: None, limit=FLOAT_INF):
        pattern_config = self._context.get("pattern_config")
        if pattern_config:
            for idx, row in data:
                self._strip_string(row)
                self._remove_commented_and_empty_columns(row)
                if not any(row.values()):
                    continue

                yield self._pattern_format2json(row), {"rows": {"from": idx, "to": idx}}

                # WARNING: complex code
                # As we are in an generator the following code is executed
                # after the "for id, xid, record, info in converted:" in model.py:1090
                # the idea is to call the flush manually for the last line
                # and set new savepoint so the rollback in case of error
                # "if any(message['type'] == 'error' for message in messages):"
                # in model.py:1100
                # will do nothing
                # this is a crazy hack but there is no better solution
                # in V15 we should propose a refactor of load method
                if data[-1][0] == idx:
                    self._context["import_flush"]()
                    self._cr.execute("RELEASE SAVEPOINT model_load")
                    self._cr.execute("SAVEPOINT model_load")
        else:
            yield from super()._extract_records(fields_, data, log=log, limit=limit)

    @api.model
    def _convert_records(self, records, log=lambda a: None):
        for dbid, xid, record, info in super()._convert_records(records, log=log):
            # Note the log method is equal to messages.append
            # so log.__self__ return the messages list
            if self._context.get("pattern_config"):
                messages = log.__self__
                if messages and messages[-1]["rows"] == info["rows"]:
                    # we have a message for this item so we skip it from conversion
                    # so the record will be not imported
                    continue
            yield dbid, xid, record, info
