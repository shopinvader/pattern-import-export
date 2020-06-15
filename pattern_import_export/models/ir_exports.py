# Copyright 2020 Akretion France (http://www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import base64
import csv
import re
from io import StringIO

from odoo import _, api, exceptions, fields, models, registry, tools
from odoo.tools import config

from odoo.addons.queue_job.job import job

from _collections import OrderedDict

COLUMN_X2M_SEPARATOR = "|"


class IrExports(models.Model):
    """
    Todo: description:
    To implements:
    _export_with_record_FORMAT
    _read_import_data_FORMAT
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
            column_name = base_column_name = export_line.name
            nb_occurence = export_line._get_nb_occurence()
            for line_added in range(0, nb_occurence):
                if export_line.is_many2many or export_line.is_one2many:
                    column_name = "{column_name}{separator}{nb}".format(
                        column_name=base_column_name,
                        separator=COLUMN_X2M_SEPARATOR,
                        nb=line_added + 1,
                    )
                if export_line.is_one2many:
                    sub_pattern = export_line.pattern_export_id
                    sub_headers = sub_pattern._get_header()
                    base_sub_header = column_name
                    for sub_header in sub_headers:
                        column_name = "{base}{sep}{sub_header}".format(
                            base=base_sub_header,
                            sep=COLUMN_X2M_SEPARATOR,
                            sub_header=sub_header,
                        )
                        header.append(column_name)
                    column_name = False
                if column_name:
                    header.append(column_name)
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
                    if ind.isdigit() and target_ind == int(ind):
                        to_update = True
                    # If no digits it's because header comes from a sub-pattern
                    elif not ind.isdigit():
                        sub_pattern = fields_sub_pattern.get(base_name)
                        sub_records = record[base_name]
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
                field_name = export_line.select_tab_id.field_id.name
                field = export_line.name + "/" + field_name
            else:
                field = export_line.name
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
        return getattr(self, target_function)(datafile)

    @api.multi
    def _build_data_to_import(self, main_data):
        """
        Iterator who build dict to write on a CSV compatible with
        Standard Odoo import.
        Recursive function.
        main_data is a dict who contains every information related to a
        recordset. The purpose of this function is to split values related
        to O2M into a new dict (to represents a new CSV line) and
        group M2M into a single cell (separated by ",")
        @param main_data: dict
        @return: dict
        """
        main_reg = re.compile(
            r"((\w|[_]|[/])+[^|]\d*$)|((\w|[_]|[/])+[|]{1}\d*$)", re.IGNORECASE
        )
        # Expected regex:
        # company_ids => True
        # company_ids|1 => True
        # company_ids|2 => True
        # company_ids|52 => True
        # comp4ny_ids => True
        # comp4ny_ids/id => True
        # comp4ny_ids|3 => True
        # user_ids|1|name => False
        data = {k: v for k, v in main_data.items() if COLUMN_M2M_SEPARATOR not in k}
        # Manage M2M
        to_merge_data = {
            k: v
            for k, v in main_data.items()
            if COLUMN_M2M_SEPARATOR in k and main_reg.match(k)
        }
        for key, value in to_merge_data.items():
            # Todo: depending on the field exported, sometimes
            #  we don't have to add the ID!
            # Add the /id only if it's an external id!
            field_name, ind = key.split(COLUMN_M2M_SEPARATOR, 1)
            if ind.isdigit():
                field_name += "/id"
            else:
                field_name += "/" + ind
            m2m_value = data.setdefault(field_name, "")
            if m2m_value:
                m2m_value = ",".join([m2m_value, value])
            else:
                m2m_value = value
            data.update({field_name: m2m_value})
        if data:
            yield data
        others_data = {
            k: v
            for k, v in main_data.items()
            if COLUMN_M2M_SEPARATOR in k and not main_reg.match(k)
        }
        keys_to_ignore = []
        for key in others_data.keys():
            if key not in keys_to_ignore:
                field_name, sub_key = key.split(COLUMN_M2M_SEPARATOR, 1)
                sub_startswith = field_name + COLUMN_M2M_SEPARATOR
                # The else case (when sub_key.isdigit() is True) should never
                # happens because already managed by the first part
                if COLUMN_M2M_SEPARATOR in sub_key:
                    ind, sub_key = sub_key.split(COLUMN_M2M_SEPARATOR, 1)
                    sub_startswith += ind
                    field_name += "/"
                keys_to_ignore.extend(
                    [k for k in others_data.keys() if k.startswith(sub_startswith)]
                )
                # Now we have to work on item starting with
                # startwith + the separator
                # Can not do if separator in k and k.startswith(...)
                # because this example could match:
                # startswith = "company_id"
                # field1 = "company_id|1"
                # field2 = "company_id_name|1"
                # But the expected result is every field who
                # starts with "company_id|..."
                sub_data = {
                    k.replace(sub_startswith, field_name): v
                    for k, v in others_data.items()
                    if k.startswith(sub_startswith)
                }
                yield from self._build_data_to_import(sub_data)

    @api.multi
    def _get_target_fields_import(self, columns):
        """
        Get list of fields to import
        @param columns: list of str
        @return: list of str
        """
        fields = []
        for column in columns:
            field_name = column
            if COLUMN_M2M_SEPARATOR in column:
                field_name, sub_column = column.split(COLUMN_M2M_SEPARATOR, 1)
                if COLUMN_M2M_SEPARATOR in sub_column:
                    _ind, sub_column = sub_column.split(COLUMN_M2M_SEPARATOR, 1)
                    field_name += "/" + sub_column
                else:
                    field_name += "/id"
            if field_name not in fields:
                fields.append(field_name)
        return fields

    @api.multi
    @job(default_channel="root.importwithpattern")
    def _generate_import_with_pattern_job(self, attachment):
        """

        @param datafile:
        @return: bool
        """
        self.ensure_one()
        if not attachment.exists():
            raise exceptions.UserError(_("The file to import doesn't exist anymore!"))
        filename = attachment.name
        separator = config.get("csv_internal_sep", ",")
        quoting = '"'
        header, header_set = [], set()
        with StringIO() as data_content:
            # The CSV file create now doesn't contain headers.
            # Because content returned by _build_data_to_import(...) doesn't
            # contains full keys at each iteration.
            csv_writer = csv.writer(
                data_content,
                delimiter=separator,
                quotechar=quoting,
                quoting=csv.QUOTE_NONNUMERIC,
            )
            csv_writer.writerow("")  # place holder for header
            for raw_data in self._read_import_data(
                base64.b64decode(attachment.datas.decode("utf-8"))
            ):
                for data in self._build_data_to_import(raw_data):
                    for key in data:
                        if key not in header_set:
                            header_set.add(key)
                            header.append(key)
                    if data:
                        csv_writer.writerow(data.get(col, "") for col in header)
            # Reset to the beginning of the file
            data_content.seek(0)
            reader = csv.DictReader(
                data_content,
                fieldnames=header,
                delimiter=separator,
                quotechar=quoting,
                quoting=csv.QUOTE_NONNUMERIC,
            )
            # Now create the final CSV file with headers
            with StringIO() as data_content_with_header:
                csv_writer = csv.DictWriter(
                    data_content_with_header,
                    header,
                    delimiter=separator,
                    quotechar=quoting,
                    quoting=csv.QUOTE_NONNUMERIC,
                )
                csv_writer.writeheader()
                csv_writer.writerows(reader)
                filename = filename + ".csv"
                import_record = self.env["base_import.import"].create(
                    {
                        "res_model": self.model_id.model,
                        # Memo: we don't have to encode in b64
                        "file": data_content_with_header.getvalue().encode("utf-8"),
                        "file_type": "text/csv",
                        "file_name": filename,
                    }
                )
        self._attach_file_to_current_job(import_record.file, import_record.file_name)
        options = {"quoting": quoting, "separator": separator, "headers": True}
        result = import_record.do(header, header, options, dryrun=False)
        messages = result.get("messages")
        if messages:
            self._attach_message_to_current_job(messages)
        return True

    @api.multi
    def _get_current_job(self):
        job_uuid = self.env.context.get("job_uuid")
        if job_uuid:
            return (
                self.env["queue.job"].sudo().search([("uuid", "=", job_uuid)], limit=1)
            )
        return self.env["queue.job"].browse()

    @api.multi
    def _attach_message_to_current_job(self, messages):
        """

        @param messages: list of dict
        @return:
        """
        decoded_msg = []
        for error_nb, message in enumerate(messages, start=1):
            details = "Error #{nb}: {msg}".format(
                nb=error_nb, msg=message.get("message")
            )
            decoded_msg.append(details)
        final_error_msg = _(
            "Errors happens during import.\n"
            "Please open the generated file related to "
            "the job.\n- {details}"
        ).format(details="\n- ".join(decoded_msg))
        raise exceptions.UserError(final_error_msg)

    @api.multi
    def _attach_file_to_current_job(self, data, filename):
        job = self._get_current_job()
        if job:
            # We have to create a new env otherwise the attachment
            # is rollbacked in case of exception!
            cr = registry(self._cr.dbname).cursor()
            self = self.with_env(self.env(cr=cr))
            attachment = self.env["ir.attachment"].create(
                {
                    "name": filename,
                    "datas": base64.b64encode(data),
                    "datas_fname": filename,
                    "res_model": job._name,
                    "res_id": job.id,
                }
            )
            attachment.env.cr.commit()
            return attachment
