# Copyright 2020 Akretion France (http://www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import copy

from odoo import _, api, models
from odoo.exceptions import ValidationError
from odoo.osv import expression

from odoo.addons.queue_job.job import job

from .common import IDENTIFIER_SUFFIX


class Base(models.AbstractModel):
    _inherit = "base"

    @api.multi
    @job(default_channel="root.exportwithpattern")
    def _generate_export_with_pattern_job(self, export_pattern):
        export_pattern._export_with_record(self)
        return True

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

    def _flatty2json(self, row):
        res = {}
        items = [(k, v) for k, v in row.items()]
        items.sort()
        for header, vals in items:
            current = res
            previous_key = None
            keys = header.split("|")
            for key in keys:
                if not previous_key:
                    previous_key = key
                elif key.isdigit():
                    if previous_key not in current:
                        current[previous_key] = []
                    key_idx = int(key)
                    if len(current[previous_key]) < int(key_idx):
                        current[previous_key].append({})
                    try:
                        current = current[previous_key][key_idx - 1]
                    except IndexError:
                        raise
                elif not previous_key.isdigit():
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

    def _get_domain_from_identifier_key(self, res):
        ident_keys = []
        domain = []
        for key in list(res.keys()):
            if key.endswith(IDENTIFIER_SUFFIX):
                field_name = key.replace(IDENTIFIER_SUFFIX, "")
                domain.append((field_name, "=", res[key]))
                ident_keys.append(key)
        return domain, ident_keys

    def _post_process_o2m_fields(self, res, parent_do_not_exist):
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
                    subdomain.append((field.inverse_name, "=", parent_id))

                for subitem in res[key]:
                    self.env[field._related_comodel_name]._post_process_key(
                        subitem, subdomain, not bool(parent_id)
                    )

    def _set_record_id_from_domain(self, res, ident_keys, domain):
        record = self.search(domain)
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
        if domain is None:
            domain = []
        domain_key, ident_keys = self._get_domain_from_identifier_key(res)

        if domain_key and not parent_do_not_exist:
            full_domain = expression.AND([domain, domain_key])
            self._set_record_id_from_domain(res, ident_keys, full_domain)

        self._post_process_o2m_fields(res, parent_do_not_exist=parent_do_not_exist)
        self._clean_identifier_key(res, ident_keys)
        return res

    @api.model
    def _extract_records(self, fields_, data, log=lambda a: None):
        if self._context.get("load_format") == "flatty":
            for idx, row in enumerate(data):
                yield self._flatty2json(row), {"rows": {"from": idx + 1, "to": idx + 1}}
        else:
            yield from super()._extract_records(fields_, data, log=log)
