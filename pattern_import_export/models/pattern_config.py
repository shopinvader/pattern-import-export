# Copyright 2020 Akretion France (http://www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import ast
import base64

from odoo import _, api, fields, models
from odoo.osv import expression

from .common import COLUMN_X2M_SEPARATOR, IDENTIFIER_SUFFIX


class PatternConfig(models.Model):
    """
    Add selection options on field export_format
    To implements:
    _export_with_record_FORMAT (should use an iterator)
    _read_import_data_FORMAT (should return an iterator)
    """

    _inherits = {"ir.exports": "export_id"}
    _name = "pattern.config"
    _description = "Pattern Config"

    export_id = fields.Many2one("ir.exports", required=True, ondelete="cascade")
    header_format = fields.Selection(
        selection=[
            ("technical", "Technical"),
            ("description_and_tech", "Description + Technical"),
        ],
        default="technical",
        required=True,
    )
    purge_one2many = fields.Boolean(
        help=(
            "When importing One2many relation like the line of 'sale order line'\n"
            "or contacts of partner. Tick this option if you want to remove\n"
            "record that are not present in you file"
        )
    )
    pattern_file = fields.Binary(string="Pattern file", readonly=True)
    pattern_file_name = fields.Char(readonly=True)
    pattern_last_generation_date = fields.Datetime(
        string="Pattern last generation date", readonly=True
    )
    export_format = fields.Selection(selection=[("json", "Json")])
    chunk_size = fields.Integer(default=500, help="Define the size of the chunk")
    count_pattern_file_failed = fields.Integer(compute="_compute_pattern_file_counts")
    count_pattern_file_pending = fields.Integer(compute="_compute_pattern_file_counts")
    count_pattern_file_done = fields.Integer(compute="_compute_pattern_file_counts")
    pattern_file_ids = fields.One2many("pattern.file", "pattern_config_id")
    process_multi = fields.Boolean()
    job_priority = fields.Integer(default=20)

    # we redefine previous onchanges since delegation inheritance breaks
    # onchanges on ir.exports

    @api.onchange("model_id")
    def _inverse_model_id(self):
        """Get the resource from the model."""
        for s in self:
            s.resource = s.model_id.model

    @api.onchange("resource")
    def _onchange_resource(self):
        """Void fields if model is changed in a view."""
        for s in self:
            s.export_fields = False

    def _compute_pattern_file_counts(self):
        for rec in self:
            for state in ("failed", "pending", "done"):
                field_name = "count_pattern_file_" + state
                count = len(
                    rec.pattern_file_ids.filtered(
                        lambda r, state=state: r.state == state
                    ).ids
                )
                setattr(rec, field_name, count)

    def _open_pattern_file(self, domain=None):
        if domain is None:
            domain = []
        domain = expression.AND([[("pattern_config_id", "=", self.id)], domain])
        return {
            "name": _("Pattern files"),
            "view_mode": "tree,form",
            "res_model": "pattern.file",
            "type": "ir.actions.act_window",
            "domain": domain,
        }

    def button_open_pattern_file_failed(self):
        return self._open_pattern_file([("state", "=", "failed")])

    def button_open_pattern_file_pending(self):
        return self._open_pattern_file([("state", "=", "pending")])

    def button_open_pattern_file_done(self):
        return self._open_pattern_file([("state", "=", "done")])

    @property
    def row_start_records(self):
        return self.nr_of_header_rows + 1

    @property
    def nr_of_header_rows(self):
        if self.header_format == "description_and_tech":
            return 2
        else:
            return 1

    def _get_output_headers(self):
        """Return one or multiheader with key:value"""
        tech_header = self._get_header()
        headers = []
        if self.header_format == "description_and_tech":
            headers.append(
                dict(zip(tech_header, self._get_header(use_description=True)))
            )
        headers.append(dict(zip(tech_header, tech_header)))
        return headers

    def _get_header(self, use_description=False):
        """
        Build header of data-structure.
        Could be recursive in case of lines with pattern_config_id.
        @return: list of string
        """
        self.ensure_one()
        header = []
        for export_line in self.export_fields:
            header.extend(export_line._get_header(use_description))
        return header

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
            filename = self.name + "." + self.export_format
            export.write(
                {
                    "pattern_file": data,
                    "pattern_last_generation_date": fields.Datetime.now(),
                    "pattern_file_name": filename,
                }
            )
        return True

    def _get_data_to_export(self, records):
        """
        Iterator who built data dict record by record.
        This function could be recursive in case of sub-pattern
        """
        self.ensure_one()
        json_parser = self.export_fields._get_json_parser_for_pattern()
        for record in records:
            yield self._get_data_to_export_by_record(record, json_parser)

    def json2pattern_format(self, data):
        res = {}
        for header in self._get_header():
            try:
                val = data
                for key in header.split(COLUMN_X2M_SEPARATOR):
                    if key.isdigit():
                        key = int(key) - 1
                    elif IDENTIFIER_SUFFIX in key:
                        key = key.replace(IDENTIFIER_SUFFIX, "")
                    if key == ".id":
                        key = "id"
                    val = val[key]
                    if val is None:
                        break
            except IndexError:
                val = None
            res[header] = val
        return res

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
        return self.json2pattern_format(data)

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
            export_data = getattr(export, target_function)(records)
            if export_data:
                all_data.append(base64.b64encode(export_data))
        return all_data

    def _export_with_record(self, records):
        """
        Export given recordset
        @param records: recordset
        @return: ir.attachment recordset
        """
        pattern_file_exports = self.env["pattern.file"]
        all_data = self._generate_with_records(records)
        if all_data and self.env.context.get("export_as_attachment", True):
            for export, attachment_data in zip(self, all_data):
                pattern_file_exports |= export._create_pattern_file_export(
                    attachment_data
                )
        return pattern_file_exports

    def _create_pattern_file_export(self, attachment_datas):
        """
        Attach given parameter (b64 encoded) to the current export.
        @param attachment_datas: base64 encoded data
        @return: ir.attachment recordset
        """
        self.ensure_one()
        name = "{name}.{format}".format(name=self.name, format=self.export_format)
        return self.env["pattern.file"].create(
            {
                "name": name,
                "type": "binary",
                "res_id": self.id,
                "res_model": "pattern.config",
                "datas": attachment_datas,
                "kind": "export",
                "state": "done",
                "pattern_config_id": self.id,
            }
        )

    def _add_update_tabs(self, result, tab_name, tab_vals):
        if tab_name in result["tabs"]:
            result["tabs"][tab_name]["idx_col_validator"] += tab_vals[
                "idx_col_validator"
            ]
        else:
            result["tabs"][tab_name] = tab_vals

    def _get_metadata(self):
        """
        :return: an dict with {"tabs": {}, "total_columns": X}
        tabs have the following fields
        name: sheet name
        headers: list of strings, each element mapping to one header cell
        data: list of lists, each element mapping to one row/cells
        idx_col_validator: position of the column on the main sheet
        """
        result = {
            "tabs": {},
            "total_columns": 0,
        }
        offset = 0
        for rec in self.export_fields:
            if rec.sub_pattern_config_id:
                metadata = rec.sub_pattern_config_id._get_metadata()
                for tab_name, tab_vals in metadata["tabs"].items():
                    idx_col_validator = []
                    for idx in range(rec.number_occurence or 1):
                        for idx_col in tab_vals["idx_col_validator"]:
                            idx_col_validator.append(
                                idx_col + offset + idx * metadata["total_columns"]
                            )
                    tab_vals["idx_col_validator"] = idx_col_validator
                    self._add_update_tabs(result, tab_name, tab_vals)
                offset += metadata["total_columns"] * rec.number_occurence
                continue
            elif not rec.add_select_tab:
                offset += rec.number_occurence or 1
                continue

            permitted_records = []
            model_name = rec.related_model_id.model
            domain = (
                rec.tab_filter_id and ast.literal_eval(rec.tab_filter_id.domain)
            ) or []
            records_matching_constraint = self.env[model_name].search(domain)
            permitted_records += records_matching_constraint
            data = rec._format_tab_records(permitted_records)
            headers = rec._get_tab_headers()
            tab_name = rec._get_tab_name()
            idx_col_validator = []
            for __ in range(rec.number_occurence or 1):
                offset += 1
                idx_col_validator += [offset]
            self._add_update_tabs(
                result,
                tab_name,
                {
                    "headers": headers,
                    "data": data,
                    "idx_col_validator": idx_col_validator,
                },
            )
        result["total_columns"] = offset
        return result
