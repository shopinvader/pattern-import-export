# Copyright 2020 Akretion France (http://www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64

from odoo import api, fields, models, tools

COLUMN_X2M_SEPARATOR = "|"


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
        data = {}
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
            export_tabs |= sub_patterns._get_additionnal_info()
        return export_tabs
