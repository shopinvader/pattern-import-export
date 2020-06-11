# Copyright 2020 Akretion France (http://www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64

from odoo import api, fields, models

COLUMN_M2M_SEPARATOR = "|"


class IrExports(models.Model):
    _inherit = "ir.exports"

    pattern_file = fields.Binary(string="Pattern file", readonly=True)
    pattern_last_generation_date = fields.Datetime(
        string="Pattern last generation date", readonly=True
    )
    export_format = fields.Selection(selection=[])

    @api.multi
    def _get_header(self):
        """
        Build header of datastructure
        @return: list of string
        """
        self.ensure_one()
        header = []
        for export_line in self.export_fields:
            column_name = base_column_name = export_line.name
            nb_occurence = 1
            if export_line.is_many2many:
                nb_occurence = max(1, export_line.number_occurence)
            for line_added in range(0, nb_occurence):
                if export_line.is_many2many:
                    column_name = "{column_name}{separator}{nb}".format(
                        column_name=base_column_name,
                        separator=COLUMN_M2M_SEPARATOR,
                        nb=line_added + 1,
                    )
                header.append(column_name)
        return header

    @api.multi
    def generate_pattern(self):
        """
        Allows you to generate an (empty) xlsx file to be used a
        pattern for the export.
        @return: bool
        """
        for export in self:
            records = self.env[export.model_id.model].browse()
            attachment = export._export_with_record(records)
            export.write(
                {
                    "pattern_file": attachment.datas,
                    "pattern_last_generation_date": fields.Datetime.now(),
                }
            )
            attachment.unlink()
        return True

    @api.multi
    def _get_data_to_export(self, records):
        """
        Iterator who built data dict record by record
        @param records: recordset
        @return: dict
        """
        self.ensure_one()
        headers = self._get_header()
        for record in records:
            data = {}
            fields_to_export = []
            column_headers = {}
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
                column_headers.update({field: nb_column})
            # The data-structure returned by export_data is different
            # that the one used to export.
            # export_data(...) return a dict with a keys named 'datas'
            # and it contains a list of list.
            # Each list item is a line (for M2M) but for the export,
            # we want to display these lines as column.
            # So we have to convert
            res = record.export_data(fields_to_export, raw_data=False)
            for target_ind, record_data in enumerate(res.get("datas", []), start=1):
                for header, value in zip(headers, record_data):
                    to_update = True
                    if COLUMN_M2M_SEPARATOR in header:
                        to_update = False
                        _name, ind = header.split(COLUMN_M2M_SEPARATOR, 1)
                        if ind.isdigit() and target_ind == int(ind):
                            to_update = True
                    if to_update and header not in data:
                        data.update({header: value})
            yield data

    @api.multi
    def _export_with_record(self, records):
        """
        Export given recordset
        @param records: recordset
        @return: ir.attachment recordset
        """
        attachments = self.env["ir.attachment"].browse()
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
            if attachment_data and self.env.context.get("export_as_attachment", True):
                attachment_data = base64.b64encode(attachment_data)
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
