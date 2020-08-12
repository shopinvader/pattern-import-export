# Copyright 2020 Akretion France (http://www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import base64

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from odoo.addons.queue_job.job import job

from .common import COLUMN_X2M_SEPARATOR, IDENTIFIER_SUFFIX


class IrExports(models.Model):
    """
    Todo: description:
    Add selection options on field export_format
    To implements:
    _export_with_record_FORMAT (should use an iterator)
    _read_import_data_FORMAT (should return an iterator)
    """

    _inherit = "ir.exports"

    is_pattern = fields.Boolean(default=False)
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
        """
        self.ensure_one()
        json_parser = self.export_fields._get_json_parser_for_pattern()
        for record in records:
            yield self._get_data_to_export_by_record(record, json_parser)

    def json2flatty(self, data):
        res = {}
        for header in self._get_header():
            try:
                val = data
                for key in header.split(COLUMN_X2M_SEPARATOR):
                    if key.isdigit():
                        key = int(key) - 1
                    elif IDENTIFIER_SUFFIX in key:
                        key = key.replace(IDENTIFIER_SUFFIX, "")
                    val = val[key]
                    if val is None:
                        break
            except IndexError:
                val = None
            res[header] = val
        return res

    @api.multi
    def _get_data_to_export_by_record(self, record, parser):
        """
        Use the ORM cache to re-use already exported data and
        could also prevent infinite recursion
        @param record: recordset
        @return: dict
        """
        self.ensure_one()
        record.ensure_one()
        data = record.jsonify(parser)[0]
        return self.json2flatty(data)

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
        return getattr(self, target_function)(datafile)

    def _process_load_message(self, messages):
        count_errors = 0
        count_warnings = 0
        error_message = _(
            "\n Several error have been found "
            "number of errors: {}, number of warnings: {}"
            "\nDetail:\n {}"
        )
        error_details = []
        for message in messages:
            error_details.append(
                _("Line {} : {}, {}").format(
                    message["rows"]["to"], message["type"], message["message"]
                )
            )
            if message["type"] == "error":
                count_errors += 1
            elif message["type"] == "warning":
                count_warnings += 1
            else:
                raise UserError(
                    _("Message type {} is not supported").format(message["type"])
                )
        if count_errors or count_warnings:
            return (
                True,
                error_message.format(
                    count_errors, count_warnings, "\n".join(error_details)
                ),
            )
        return False, ""

    def _process_load_result(self, attachment, res):
        ids = res["ids"] or []
        info = _("Number of record imported {}\ndetails {}").format(len(ids), ids)
        raise_error = False
        if res.get("messages"):
            raise_error, message = self._process_load_message(res["messages"])
            info += message
        if raise_error:
            raise UserError(message)
        return info

    @job(default_channel="root.importwithpattern")
    def _generate_import_with_pattern_job(self, attachment):
        attachment_data = base64.b64decode(attachment.datas.decode("utf-8"))
        datas = self._read_import_data(attachment_data)
        res = (
            self.with_context(load_format="flatty")
            .env[self.model_id.model]
            .load([], datas)
        )
        return self._process_load_result(attachment, res)
