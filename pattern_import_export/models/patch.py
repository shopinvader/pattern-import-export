# Copyright 2022 Akretion (https://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


import functools

from odoo import _, api, models
from odoo.tools.misc import CountingStream


# be careful we redifine the broken native code
# a pending PR is here:
# https://github.com/odoo/odoo/pull/60260
@api.model
def _convert_records(self, records, log=lambda a: None):
    """Converts records from the source iterable (recursive dicts of
    strings) into forms which can be written to the database (via
    self.create or (ir.model.data)._update)

    :returns: a list of triplets of (id, xid, record)
    :rtype: list((int|None, str|None, dict))
    """
    field_names = {name: field.string for name, field in self._fields.items()}
    if self.env.lang:
        field_names.update(self.env["ir.translation"].get_field_string(self._name))

    convert = self.env["ir.fields.converter"].for_model(self)

    def _log(base, record, field, exception):
        kind = "warning" if isinstance(exception, Warning) else "error"
        # logs the logical (not human-readable) field name for automated
        # processing of response, but injects human readable in message
        exc_vals = dict(base, record=record, field=field_names[field])
        record = dict(
            base,
            type=kind,
            record=record,
            field=field,
            message=str(exception.args[0]) % exc_vals,
        )
        if len(exception.args) > 1 and exception.args[1]:
            record.update(exception.args[1])
        log(record)

    stream = CountingStream(records)
    for record, extras in stream:
        # xid
        xid = record.get("id", False)
        # dbid
        dbid = False
        if ".id" in record:
            try:
                dbid = int(record[".id"])
            except ValueError:
                # Code changed
                if self._fields["id"].type != "integer":
                    # in case of overridden id column
                    dbid = record[".id"]
                else:
                    log(
                        dict(
                            extras,
                            type="error",
                            record=stream.index,
                            field=".id",
                            message=_("Invalid database identifier '%s'") % dbid,
                        )
                    )
                # End of code changed
            # Code changed active_test=False
            if not self.with_context(active_test=False).search([("id", "=", dbid)]):
                # End of code changed
                log(
                    dict(
                        extras,
                        type="error",
                        record=stream.index,
                        field=".id",
                        message=_("Unknown database identifier '%s'") % dbid,
                    )
                )
                dbid = False

        converted = convert(record, functools.partial(_log, extras, stream.index))

        yield dbid, xid, converted, dict(extras, record=stream.index)


models.BaseModel._convert_records = _convert_records
