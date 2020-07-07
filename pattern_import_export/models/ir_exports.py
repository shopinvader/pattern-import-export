# Copyright 2020 Akretion France (http://www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import base64
import re

from numpy import isnan
from psycopg2 import IntegrityError

from odoo import _, api, exceptions, fields, models

from odoo.addons.queue_job.job import job

from _collections import OrderedDict

COLUMN_X2M_SEPARATOR = "|"


class IrExports(models.Model):
    """
    Todo: description:
    Add selection options on field export_format
    To implements:
    _export_with_record_FORMAT (should use an iterator)
    _read_import_data_FORMAT (should return an iterator)
    """

    _inherit = "ir.exports"

    pattern_file = fields.Binary(string="Pattern file", readonly=True)
    pattern_last_generation_date = fields.Datetime(
        string="Pattern last generation date", readonly=True
    )
    export_format = fields.Selection(selection=[])

    @api.multi
    def _get_header(self):
        """
        Build header of data-structure.
        Could be recursive in case of lines with pattern_export_id.
        @return: list of string
        """
        self.ensure_one()
        header = []
        for export_line in self.export_fields:
            header.extend(export_line._get_header())
        return header

    @api.multi
    def generate_pattern(self):
        """
        Allows you to generate an (empty) file to be used a
        pattern for the export.
        @return: bool
        """
        for export in self:
            records = self.env[export.model_id.model].browse()
            data = export._generate_with_records(records)
            if data:
                data = data[0]
            export.write(
                {
                    "pattern_file": data,
                    "pattern_last_generation_date": fields.Datetime.now(),
                }
            )
        return True

    @api.multi
    def _get_data_to_export(self, records):
        """
        Iterator who built data dict record by record.
        This function could be recursive in case of sub-pattern
        @param records: recordset
        @return: dict
        """
        self.ensure_one()
        for record in records:
            yield self._get_data_to_export_by_record(record)

    @api.multi
    def _get_data_to_export_by_record(self, record):
        """
        Use the ORM cache to re-use already exported data and
        could also prevent infinite recursion
        @param record: recordset
        @return: dict
        """
        self.ensure_one()
        record.ensure_one()
        fields_to_export = self._get_fields_to_export()
        # The data-structure returned by export_data is different
        # that the one used to export.
        # export_data(...) return a dict with a keys named 'datas'
        # and it contains a list of list.
        # Each list item is a line (for M2M) but for the export,
        # we want to display these lines as column.
        # So we have to convert
        res = record.export_data(fields_to_export, raw_data=False)
        data = self._built_record_values(res.get("datas", []), record)
        return data

    @api.multi
    def _built_record_values(self, raw_data, record):
        """

        @param raw_data: list
        @param record: recordset
        @return: dict
        """
        self.ensure_one()
        data = OrderedDict()
        fields_sub_pattern = self._get_sub_patterns()
        for target_ind, record_data in enumerate(raw_data, start=1):
            for header, value in zip(self._get_header(), record_data):
                # In case of sub-pattern, it's possible that the
                # header has been already added
                if header in data:
                    continue
                to_update = True
                if COLUMN_X2M_SEPARATOR in header:
                    to_update = False
                    base_name, ind = header.split(COLUMN_X2M_SEPARATOR, 1)
                    sub_pattern = fields_sub_pattern.get(header)
                    reg_result = re.findall(r"^\D*(\d+)", ind)
                    if ind.isdigit() and target_ind == int(ind):
                        to_update = True
                    # If no digits it's because header comes from a sub-pattern
                    elif not ind.isdigit() and sub_pattern:
                        real_field = [
                            f for f in record._fields.values() if f.string == base_name
                        ]
                        if real_field:
                            real_field = real_field[0]
                        sub_records = record[real_field.name]
                        # Update current data with data from
                        # sub-pattern (and extend the key)
                        # This part cause the recursion
                        for sub_data in sub_pattern._get_data_to_export(sub_records):
                            base_key = "{base}{sep}{target_ind}{sep}{sub_key}"
                            sub_data_replaced = {
                                base_key.format(
                                    base=base_name,
                                    sub_key=k,
                                    target_ind=target_ind,
                                    sep=COLUMN_X2M_SEPARATOR,
                                ): v
                                for k, v in sub_data.items()
                            }
                            data.update(sub_data_replaced)
                    # If there is a digit and the digit match with the target
                    # do the update
                    elif not ind.isdigit() and reg_result:
                        to_update = target_ind == int(reg_result[0])
                    # If no digit, do the update (field is not enumerated)
                    elif not ind.isdigit() and not reg_result:
                        to_update = True
                if to_update:
                    data.update({header: value})
        return data

    @api.multi
    def _get_fields_to_export(self):
        """

        @return: list of str
        """
        self.ensure_one()
        fields_to_export = []
        for export_line in self.export_fields:
            nb_column = 1
            if export_line.is_many2x and export_line.select_tab_id:
                field_name = export_line.select_tab_id.field_id.name
                field = export_line.name + "/" + field_name
                if export_line.is_many2many:
                    nb_column = max(1, export_line.number_occurence)
            else:
                field = export_line.name
            for _i in range(0, nb_column):
                fields_to_export.append(field)
        return fields_to_export

    def _get_sub_patterns(self):
        """

        @return: dict
        """
        fields_sub_pattern = {}
        for export_line in self.export_fields:
            if export_line.is_many2x and export_line.select_tab_id:
                field_name = export_line.select_tab_id._get_field_label()
                field = export_line.name + "/" + field_name
            else:
                field = export_line._get_header()[0]
            if export_line.is_one2many and export_line.pattern_export_id:
                fields_sub_pattern.update({field: export_line.pattern_export_id})
        return fields_sub_pattern

    @api.multi
    def _generate_with_records(self, records):
        """
        Export given recordset
        @param records: recordset
        @return: list of base64 encoded
        """
        all_data = []
        for export in self:
            target_function = "_export_with_record_{format}".format(
                format=export.export_format or ""
            )
            if not export.export_format or not hasattr(export, target_function):
                msg = "The export with the format {format} doesn't exist!".format(
                    format=export.export_format or "Undefined"
                )
                raise NotImplementedError(msg)
            attachment_data = getattr(export, target_function)(records)
            if attachment_data:
                all_data.append(base64.b64encode(attachment_data))
        return all_data

    @api.multi
    def _export_with_record(self, records):
        """
        Export given recordset
        @param records: recordset
        @return: ir.attachment recordset
        """
        attachments = self.env["ir.attachment"].browse()
        all_data = self._generate_with_records(records)
        if all_data and self.env.context.get("export_as_attachment", True):
            for export, attachment_data in zip(self, all_data):
                attachments |= export._attachment_document(attachment_data)
        return attachments

    @api.multi
    def _attachment_document(self, attachment_datas):
        """
        Attach given parameter (b64 encoded) to the current export.
        @param attachment_datas: base64 encoded data
        @return: ir.attachment recordset
        """
        self.ensure_one()
        return self.env["ir.attachment"].create(
            {
                "name": "{name}.{format}".format(
                    name=self.name, format=self.export_format
                ),
                "type": "binary",
                "res_id": self.id,
                "res_model": "ir.exports",
                "datas": attachment_datas,
            }
        )

    @api.multi
    def _get_select_tab(self):
        """
        Get every export select tab related to current recordset.
        Recursive
        @return: ir.exports.select.tab recordset
        """
        export_fields = self.mapped("export_fields")
        export_tabs = export_fields.mapped("select_tab_id")
        sub_patterns = export_fields.filtered(
            lambda l: l.is_one2many and l.pattern_export_id
        ).mapped("pattern_export_id")
        if sub_patterns:
            export_tabs |= sub_patterns._get_select_tab()
        return export_tabs

    # Import part

    @api.multi
    def _read_import_data(self, datafile):
        """

        @param datafile:
        @return: list of str
        """
        target_function = "_read_import_data_{format}".format(
            format=self.export_format or ""
        )
        if not hasattr(self, target_function):
            raise NotImplementedError()
        yield from getattr(self, target_function)(datafile)

    @api.multi
    def _import_load_record(self, data_line, model, raise_if_not_found=True):
        """
        Load the record in given data_line dict by extracting the
        id key (or empty key)
        @param data_line: dict
        @param model: str
        @param raise_if_not_found: bool
        @return: recordset
        """
        record = self.env[model].browse()
        self._import_replace_keys(
            data_line, model, raise_if_not_found=raise_if_not_found
        )
        # First, looking for ID into the given dict (
        id_keys = ["", "id", "id/key"]
        id_keys.extend([i.upper() for i in id_keys])
        data_id = False
        for id_key in id_keys:
            if id_key in data_line:
                data_id = data_line.pop(id_key)
                break
        # Easy part: data_line contains ID
        if data_id:
            if isinstance(data_id, (int, float)) or data_id.isdigit():
                record = record.browse(int(data_id))
            else:
                # add 'or record' to avoid None
                record = self.env.ref(data_id, raise_if_not_found=False) or record
        if record:
            record = record.exists()
        return record

    def _import_replace_keys(self, data_line, model, raise_if_not_found=True):
        """
        Replace keys values by the ID of the target record.
        Ex:
        {"default_code/key": "test123"} => should load the current product
        with default_code = "test123";
        {"product_id/key": 4} => should load the current sale order line
        where product_id is 4.
        @param data_line: dict
        @param model: str
        @param raise_if_not_found: bool
        @return: None
        """
        # Load keys with:
        # - No separator
        # - With only 1 "/"
        # - With text before and after the "/"
        record = self.env[model].browse()
        # Build a dict where the key is the field's label and the
        # value is the field object.
        all_fields = {field.string: field for field in record._fields.values()}
        regex_key_fields = re.compile(
            r"[" + COLUMN_X2M_SEPARATOR + r"]{0}((\w|[_ ])+([/]{1})(\w|[_ ])+)",
            re.IGNORECASE,
        )
        target_keys = [
            k for k in data_line.keys() if regex_key_fields.match(k) and "/key" in k
        ]
        if len(target_keys) > 1:
            details = "\n- ".join(target_keys)
            error_message = _(
                "There is too many keys on the same level into your import.\n"
                "- {details}"
            ).format(details=details)
            raise exceptions.UserError(error_message)
        if target_keys:
            target_key = target_keys[0]
            field_name = target_key.replace("/key", "")
            raw_value = data_line.pop(target_key)
            if COLUMN_X2M_SEPARATOR in field_name:
                field_name, sub_field_name = field_name.split(COLUMN_X2M_SEPARATOR, 1)
                sub_data = {sub_field_name: raw_value}
                real_field = all_fields.get(field_name)
                raw_value = self._import_load_record(
                    sub_data, model=real_field.comodel_name
                )
            else:
                real_field = all_fields.get(field_name)
            if isinstance(raw_value, float) and isnan(raw_value):
                if real_field.type in ("float", "integer", "monetary"):
                    raw_value = 0
                elif real_field.type in ("char", "text"):
                    raw_value = ""
                else:
                    raw_value = False
            target_value = real_field.convert_to_write(raw_value, record)
            domain = [(real_field.name, "=", target_value)]
            record = record.search(domain, limit=1)
            # If the record is not found, raise an exception.
            # Because not coherent to create a record if the user
            # expect to have a result
            if not record:
                # Update the dict with False value for target record.
                data_line.update({field_name: raw_value})
                # In case of the caller catch the exception
                if raise_if_not_found:
                    error_message = _(
                        "The value '{raw_value}' on model {model_name} and "
                        "field {field_name} couldn't be found.\n"
                        "Please ensure the record exists and you have "
                        "correct access rights!"
                    ).format(
                        raw_value=raw_value, model_name=model, field_name=field_name
                    )
                    raise exceptions.UserError(error_message)
            data_line.update({"id": record.id})

    @api.multi
    def _get_max_occurrence(self):
        """
        Get the number of occurrence to manage.
        Value should be > 1 otherwise it's disabled
        @return: int
        """
        return 20

    @api.multi
    def _parse_import_data(self, data_line, model=""):
        """
        Recursive function used to read given data_line and build a dict
        used to do create/write.
        Recursive only for O2M, M2M and M2O fields.
        @param data_line: dict
        @param model: str
        @return: dict
        """
        data_line = dict(data_line)
        model = model or self.model_id.model
        model_obj = self.env[model]
        # Build a dict where the key is the field's label and the
        # value is the field object.
        all_fields = {field.string: field for field in model_obj._fields.values()}
        complex_fields_types = ("many2one", "one2many", "many2many")
        ignore_fields = models.MAGIC_COLUMNS + [self.CONCURRENCY_CHECK_FIELD]
        ignore_fields.remove("id")
        # Remove these fields to ignore if there are into the data_line
        # But we should keep ID if set
        data_line = {k: v for k, v in data_line.items() if k not in ignore_fields}
        simple_fields = [
            all_fields.get(f).string
            for f in all_fields
            if all_fields.get(f)
            and all_fields.get(f).type not in complex_fields_types
            and all_fields.get(f).name not in ignore_fields
        ]
        complex_fields = [
            all_fields.get(f).string
            for f in all_fields
            if all_fields.get(f)
            and all_fields.get(f).type in complex_fields_types
            and all_fields.get(f).name not in ignore_fields
        ]
        self._import_replace_keys(data_line, model)
        values = self._manage_import_simple_fields(data_line, simple_fields, model)
        values.update(
            self._manage_import_complex_fields(complex_fields, data_line, model)
        )
        return values

    def _manage_import_simple_fields(self, data_line, target_fields, model):
        """
        Manage simple fields to import (char, int etc)
        @param data_line: dict
        @param target_fields: list of str
        @param model: str
        @return: dict
        """
        values = {
            self._get_real_field(k, model).name: data_line.pop(k)
            for k in list(data_line.keys())
            if COLUMN_X2M_SEPARATOR not in k and k in target_fields
        }
        return values

    @api.model
    def _get_real_field(self, field_label, model):
        """
        Get the real field of the given model based on the field label
        @param field_label: str
        @param model: str
        @return: odoo.fields or None
        """
        model_obj = self.env[model]
        all_fields = {field.string: field for field in model_obj._fields.values()}
        return all_fields.get(field_label)

    def _manage_import_complex_fields(self, target_fields, data_line, model):
        """
        Manage complex fields to import (M2M, O2M and M2O)
        @param target_fields: list of str
        @param data_line: dict
        @param model: str
        @return:
        """
        values = {}
        for target_field in target_fields:
            # break the loop if nothing to manage
            if not data_line:
                break
            real_field = self._get_real_field(target_field, model)
            if real_field.type in ("one2many", "many2many"):
                template_starter = "{field_name}{sep}{nb}{sep}"
                for nb in range(1, self._get_max_occurrence()):
                    starter = template_starter.format(
                        field_name=target_field, sep=COLUMN_X2M_SEPARATOR, nb=nb
                    )
                    sub_values = {
                        k.replace(starter, ""): data_line.pop(k)
                        for k in list(data_line.keys())
                        if k.startswith(starter)
                    }
                    if sub_values:
                        sub_values = self._parse_import_data(
                            sub_values, model=real_field.comodel_name
                        )
                    if sub_values:
                        write_code = 0
                        record = self._import_load_record(
                            sub_values, model=real_field.comodel_name
                        )
                        if real_field.type == "one2many":
                            field_list = values.setdefault(
                                real_field.name, [(6, False, [])]
                            )
                        else:  # M2M
                            field_list = values.setdefault(
                                real_field.name, [(5, False, False)]
                            )
                        if record:
                            field_list.append((4, record.id, False))
                            write_code = 1
                        if sub_values:
                            # In case of O2M, sub_values should contains
                            # every required fields as previous values are deleted
                            field_list.append((write_code, record.id, sub_values))
                    else:
                        # If no more sub-values found,
                        # suppose no others values will be found for this field
                        break
            else:  # Is M2O
                template_starter = "{field_name}{sep}"
                starter = template_starter.format(
                    field_name=target_field, sep=COLUMN_X2M_SEPARATOR
                )
                sub_values = {
                    k.replace(starter, ""): data_line.pop(k)
                    for k in list(data_line.keys())
                    if k.startswith(starter) and COLUMN_X2M_SEPARATOR in k
                }
                if sub_values:
                    sub_values = self._parse_import_data(
                        sub_values, model=real_field.comodel_name
                    )
                if sub_values:
                    record = self._import_load_record(
                        sub_values, model=real_field.comodel_name
                    )
                    if record and sub_values:
                        record.write(sub_values)
                    elif not record and sub_values:
                        record = record.create(sub_values)
                    values.update({real_field.name: record.id})
        return values

    @api.multi
    @job(default_channel="root.importwithpattern")
    def _generate_import_with_pattern_job(self, attachment):
        attachment_data = base64.b64decode(attachment.datas.decode("utf-8"))
        for line_nb, raw_data in enumerate(
            self._read_import_data(attachment_data), start=1
        ):
            error_message = ""
            try:
                record = self._import_load_record(
                    raw_data, model=self.model_id.model, raise_if_not_found=False
                )
                values = self._parse_import_data(raw_data)
                if record and values:
                    record.write(values)
                elif values and not record:
                    record.create(values)
            except IntegrityError as e:
                error_message = _(
                    "Error to write/create line {line_nb}: {ex_msg}"
                ).format(line_nb=line_nb, ex_msg=e)
            except exceptions.except_orm as e:
                error_message = _(
                    "Error to write/create line {line_nb}: {ex_msg}"
                ).format(line_nb=line_nb, ex_msg=e)
            if error_message:
                raise exceptions.UserError(error_message)
