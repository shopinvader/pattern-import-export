# Copyright 2020 Akretion France (http://www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from .ir_exports import COLUMN_X2M_SEPARATOR


class IrExportsLine(models.Model):
    _inherit = "ir.exports.line"

    select_tab_id = fields.Many2one("ir.exports.select.tab", string="Select tab")
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
        compute="_compute_related_model_id",
        store=True,
    )
    required_fields = fields.Char(compute="_compute_required_fields", store=True)
    number_occurence = fields.Integer(
        string="# Occurence",
        default=1,
        help="Number of column to create to display this "
        "Many2many or One2many field.\n"
        "Value should be >= 1",
    )

    @api.multi
    @api.constrains("is_key", "export_id")
    def _constrains_one_key_per_export(self):
        """
        Constrain function to ensure there is maximum 1 field considered as key
        for an export.
        :return:
        """
        groupby = "export_id"
        domain = [(groupby, "in", self.mapped("export_id").ids), ("is_key", "=", True)]
        read = [groupby]
        # Get the read group
        read_values = self.read_group(domain, read, groupby, lazy=False)
        count_by_export = {
            v.get(groupby, [0])[0]: v.get("__count", 0) for v in read_values
        }
        exceeded_ids = {
            export_id: nb for export_id, nb in count_by_export.items() if nb > 1
        }
        if exceeded_ids:
            bad_records = self.filtered(
                lambda e: e.export_id.id in exceeded_ids
            ).mapped("export_id")
            details = "\n- ".join(bad_records.mapped("display_name"))
            message = (
                _(
                    "These export pattern are not valid because there is too "
                    "much field considered as key (1 max):\n- %s"
                )
                % details
            )
            raise ValidationError(message)

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
            if not record.name:
                record.required_fields = ""
            else:
                required = []
                field, model, level = self._get_last_relation_field(
                    record.export_id.resource, record.name
                )
                ftype = self.env[model]._fields[field].type
                if ftype in ["many2one", "many2many"]:
                    level += 1
                for idx in range(2, level + 1):
                    required.append("field{}_id".format(idx))
                if ftype in ["one2many", "many2many"]:
                    required.append("number_occurence")
                if ftype in "one2many":
                    required.append("pattern_export_id")
                record.required_fields = ",".join(required)

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
    def _compute_related_model_id(self):
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

    @api.multi
    def _get_header(self):
        """

        @return: list of str
        """
        self.ensure_one()
        headers = []
        model_obj = self.env[self.export_id.model_id.model]
        real_field = model_obj._fields.get(self.field1_id.name)
        # The current (main) field shouldn't be into the list
        real_fields = []
        previous_real_field = real_field
        if self.field2_id:
            previous_real_field = self.env[
                previous_real_field.comodel_name
            ]._fields.get(self.field2_id.name)
            real_fields.append(previous_real_field.string)
        if self.field3_id:
            previous_real_field = self.env[
                previous_real_field.comodel_name
            ]._fields.get(self.field3_id.name)
            real_fields.append(previous_real_field.string)
        if self.field4_id:
            previous_real_field = self.env[
                previous_real_field.comodel_name
            ]._fields.get(self.field4_id.name)
            real_fields.append(previous_real_field.string)

        field_name = real_field.string
        if self.is_key:
            field_name += "/key"
        if real_field.type in ("many2one", "one2many", "many2many"):
            for line_added in range(0, self.number_occurence):
                sub_name = "{sub_name}"
                if real_fields:
                    sub_name = COLUMN_X2M_SEPARATOR.join(real_fields)
                    sub_name += COLUMN_X2M_SEPARATOR + "{sub_name}"
                if real_field.type == "many2one":
                    base_name = "{field_name}{sep}{sub_name}".format(
                        field_name=field_name,
                        sep=COLUMN_X2M_SEPARATOR,
                        sub_name=sub_name,
                    )
                elif real_field.type in ("one2many", "many2many"):
                    base_name = "{field_name}{sep}{ind}{sep}{sub_name}".format(
                        field_name=field_name,
                        sep=COLUMN_X2M_SEPARATOR,
                        ind=line_added + 1,
                        sub_name=sub_name,
                    )
                if self.select_tab_id:
                    headers.extend(
                        [
                            base_name.format(sub_name=h)
                            for h in self.select_tab_id._get_header()
                        ]
                    )
                elif self.pattern_export_id:
                    for sub_line in self.pattern_export_id.export_fields:
                        headers.extend(
                            [
                                base_name.format(sub_name=h)
                                for h in sub_line._get_header()
                            ]
                        )
        else:
            headers.append(field_name)
        return headers
