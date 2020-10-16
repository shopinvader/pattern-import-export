# Copyright 2020 Akretion France (http://www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import safe_eval

from odoo.addons.base_jsonify.models.ir_export import convert_dict, update_dict

from _collections import OrderedDict

from .common import COLUMN_X2M_SEPARATOR, IDENTIFIER_SUFFIX


class IrExportsLine(models.Model):
    _inherit = "ir.exports.line"

    add_select_tab = fields.Boolean()
    tab_filter_id = fields.Many2one("ir.filters")
    is_key = fields.Boolean(
        default=False,
        help="Determine if this field is considered as key to update "
        "existing record.\n"
        "Please note that the field should have a unique constraint.",
    )
    pattern_export_id = fields.Many2one(
        comodel_name="ir.exports",
        ondelete="restrict",
        help="Sub-pattern used to export O2M fields",
    )
    related_model_id = fields.Many2one(
        "ir.model",
        string="Related model",
        compute="_compute_related_level_field",
        store=True,
    )
    related_model_name = fields.Char(related="related_model_id.model")
    last_field_id = fields.Many2one(
        "ir.model.fields",
        string="Last Field",
        compute="_compute_related_level_field",
        store=True,
    )
    level = fields.Integer(compute="_compute_related_level_field", store=True)
    required_fields = fields.Char(compute="_compute_required_fields", store=True)
    hidden_fields = fields.Char(compute="_compute_required_fields", store=True)
    number_occurence = fields.Integer(
        string="# Occurence",
        default=1,
        help="Number of column to create to display this "
        "Many2many or One2many field.\n"
        "Value should be >= 1",
    )

    @api.model
    def _get_last_relation_field(self, model, path, level=1):
        if "/" not in path:
            path = path + "/"
        field, path = path.split("/", 1)
        if path:
            next_model = self.env[model]._fields[field]._related_comodel_name
            next_field = path.split("/", 1)[0]
            if self.env[next_model]._fields[next_field]._related_comodel_name:
                return self._get_last_relation_field(next_model, path, level=level + 1)
        return field, model, level

    @api.depends("name")
    def _compute_required_fields(self):
        for record in self:
            hidden_fields = [
                "field1_id",
                "field2_id",
                "field3_id",
                "field4_id",
                "number_occurence",
                "pattern_export_id",
                "tab_filter_id",
                "add_select_tab",
            ]
            if not record.name:
                record.required_fields = ""
                record.hidden_fields = ""
            else:
                required = []
                field, model, level = self._get_last_relation_field(
                    record.export_id.resource, record.name
                )
                ftype = self.env[model]._fields[field].type
                if ftype in ["many2one", "many2many"]:
                    level += 1
                    hidden_fields.remove("add_select_tab")
                for idx in range(2, level + 1):
                    required.append("field{}_id".format(idx))
                if ftype in ["one2many", "many2many"]:
                    required.append("number_occurence")
                if ftype in "one2many":
                    required.append("pattern_export_id")
                if record.add_select_tab:
                    required.append("tab_filter_id")
                record.required_fields = ",".join(required)
                hidden_fields = list(set(hidden_fields) - set(required))
                record.hidden_fields = ",".join(hidden_fields)

    def _inverse_name(self):
        super()._inverse_name()
        self._check_required_fields()

    @api.constrains(
        "export_id.is_pattern", "name", "number_occurence", "pattern_export_id"
    )
    def _check_required_fields(self):
        for record in self:
            if record._context.get("skip_check") or not record.field1_id:
                return True
            if record.export_id.is_pattern and record.required_fields:
                required_fields = record.required_fields.split(",")
                if (
                    "number_occurence" in required_fields
                    and record.number_occurence < 1
                ):
                    message = _(
                        "Number of occurence for Many2many or One2many fields "
                        "should be greater or equals to 1.\n"
                        "The line {} have an invalid number of "
                        "occurence:\n"
                    ).format(record.name)
                    raise ValidationError(message)

                for key in record.required_fields.split(","):
                    if not record[key]:
                        raise ValidationError(
                            _("The field {} is empty for the line {}").format(
                                key, record.name
                            )
                        )

    @api.multi
    @api.depends("name")
    def _compute_related_level_field(self):
        for export_line in self:
            if export_line.export_id.resource and export_line.name:
                field, model, level = export_line._get_last_relation_field(
                    export_line.export_id.resource, export_line.name
                )
                related_comodel = self.env[model]._fields[field]._related_comodel_name
                if related_comodel:
                    comodel = self.env["ir.model"].search(
                        [("model", "=", related_comodel)], limit=1
                    )
                    export_line.related_model_id = comodel.id
                    export_line.level = level
                fields = export_line.name.split("/")
                if len(fields) > level:
                    last_field = fields[-1]
                    last_model = related_comodel
                else:
                    last_field = field
                    last_model = model
                export_line.last_field_id = self.env["ir.model.fields"].search(
                    [("name", "=", last_field), ("model_id.model", "=", last_model)]
                )

    def _build_header(self, level, use_description):
        base_header = []
        for idx in range(1, level + 1):
            field = self["field{}_id".format(idx)]
            if use_description:
                base_header.append(field.field_description)
            else:
                field_name = field.name
                if idx == 1 and self.is_key:
                    field_name += IDENTIFIER_SUFFIX
                base_header.append(field_name)
        return COLUMN_X2M_SEPARATOR.join(base_header)

    @api.multi
    def _get_header(self, use_description=False):
        """
        @return: list of str
        """
        headers = []
        for record in self:
            if record.level == 0:
                if use_description:
                    header = record.field1_id.field_description
                else:
                    header = record.field1_id.name
                if record.is_key:
                    header += IDENTIFIER_SUFFIX
                headers.append(header)
            else:
                last_relation_field = record["field{}_id".format(record.level)]
                if last_relation_field.ttype == "many2one":
                    headers.append(
                        record._build_header(self.level + 1, use_description)
                    )
                else:
                    base_header = record._build_header(record.level, use_description)
                    sub_pattern = record.pattern_export_id
                    if sub_pattern:
                        sub_headers = sub_pattern.export_fields._get_header(
                            use_description
                        )
                        for idx in range(1, record.number_occurence + 1):
                            headers.extend(
                                [
                                    COLUMN_X2M_SEPARATOR.join(
                                        [base_header, str(idx), h]
                                    )
                                    for h in sub_headers
                                ]
                            )
                    else:
                        field = record["field{}_id".format(record.level + 1)]
                        if use_description:
                            field_name = field.field_description
                        else:
                            field_name = field.name
                        for idx in range(1, record.number_occurence + 1):
                            headers.append(
                                COLUMN_X2M_SEPARATOR.join(
                                    [base_header, str(idx), field_name]
                                )
                            )
        return headers

    def _get_tab_headers(self):
        self.ensure_one()
        return [self.last_field_id.name]

    def _format_tab_records(self, permitted_records):
        return [
            [getattr(record, self.last_field_id.name)] for record in permitted_records
        ]

    def _get_tab_name(self):
        tab_filter = self.tab_filter_id
        if tab_filter:
            name = "({}) {}".format(str(tab_filter.id), tab_filter.name)
        else:
            name = self.field1_id.field_description
        if len(name) > 31:
            name = name[0:28] + "..."
        return name

    def _get_tab_data(self):
        """
        :return: iterable of 4-tuples of format:
        (name, headers, data, origin_col)
        one tuple for each tab
        name: sheet name
        headers: list of strings, each element mapping to one header cell
        data: list of lists, each element mapping to one row/cells
        origin_col: position of the column on the main sheet
        """
        result = []
        for itr, rec in enumerate(self, start=1):
            if not rec.add_select_tab:
                continue
            permitted_records = []
            model_name = rec.related_model_id.model
            domain = (rec.tab_filter_id and safe_eval(rec.tab_filter_id.domain)) or []
            records_matching_constraint = self.env[model_name].search(domain)
            permitted_records += records_matching_constraint
            data = rec._format_tab_records(permitted_records)
            headers = rec._get_tab_headers()
            tab_name = rec._get_tab_name()
            result.append((tab_name, headers, data, itr))
        return result

    def _get_dict_parser_for_pattern(self):
        parser = OrderedDict()
        for rec in self:
            names = rec.name.split("/")
            update_dict(parser, names)
            if rec.pattern_export_id:
                last_item = parser
                last_field = names[0]
                for field in names[:-1]:
                    last_item = last_item[field]
                    last_field = field
                last_item[
                    last_field
                ] = rec.pattern_export_id.export_fields._get_dict_parser_for_pattern()
        return parser

    def _get_json_parser_for_pattern(self):
        return convert_dict(self._get_dict_parser_for_pattern())
