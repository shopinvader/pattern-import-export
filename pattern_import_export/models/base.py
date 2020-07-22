# Copyright 2020 Akretion France (http://www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, models
from odoo.exceptions import ValidationError

from odoo.addons.queue_job.job import job

from .ir_fields import IDENTIFIER_SURFIXE


class Base(models.AbstractModel):
    _inherit = "base"

    @api.multi
    @job(default_channel="root.exportwithpattern")
    def _generate_export_with_pattern_job(self, export_pattern):
        export_pattern._export_with_record(self)
        return True

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

    def _post_process_key(self, res, domain=None):
        o2m_fields = []
        domain = []

        for key in list(res.keys()):
            if key.endswith(IDENTIFIER_SURFIXE):
                field_name = key.replace(IDENTIFIER_SURFIXE, "")
                record = self.search([(field_name, "=", res[key])])
                if len(record) > 1:
                    raise ValidationError(
                        _("Too many {} found for the key {} with the value {}").format(
                            _(record._description), key, res[key]
                        )
                    )
                elif record:
                    res[".id"] = record.id
                    res.pop(key)
            else:
                field = self._fields.get(key)
                if field and field.type == "one2many":
                    o2m_fields.append([key, field])
        for key, field in o2m_fields:
            domain = []
            if ".id" in res:
                domain.append(("id", "=", res[".id"]))
            elif "id" in res:
                record = self.env.ref(res["id"])
                domain.append(("id", "=", record.id))
            for subitem in res[key]:
                self.env[field._related_comodel_name]._post_process_key(subitem, domain)
        return res

    @api.model
    def _extract_records(self, fields_, data, log=lambda a: None):
        if self._context.get("load_format") == "flatty":
            for idx, row in enumerate(data):
                yield self._flatty2json(row), {"rows": {"from": idx, "to": idx}}
        else:
            yield from super()._extract_records(fields_, data, log=log)
