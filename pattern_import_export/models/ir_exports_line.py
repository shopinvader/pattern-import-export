# Copyright 2020 Akretion France (http://www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import _, api, exceptions, fields, models

from .ir_exports import COLUMN_X2M_SEPARATOR


class IrExportsLine(models.Model):
    _inherit = "ir.exports.line"

    select_tab_id = fields.Many2one("ir.exports.select.tab", string="Select tab")
    is_many2x = fields.Boolean(
        string="Is Many2x field", compute="_compute_is_many2x", store=True
    )
    is_many2many = fields.Boolean(
        string="Is Many2many field", compute="_compute_is_many2many", store=True
    )
    is_one2many = fields.Boolean(
        string="Is One2many field", compute="_compute_is_one2many", store=True
    )
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
            raise exceptions.ValidationError(message)

    @api.multi
    @api.constrains("number_occurence", "is_many2many", "is_one2many")
    def _constrains_number_occurence(self):
        """
        Constrain function for the field number_occurence.
        Ensure the number_occurence is at least 1 when is_many2many or
        is_one2many is True.
        :return:
        """
        bad_records = self.filtered(
            lambda r: (r.is_many2many or r.is_one2many) and r.number_occurence < 1
        )
        if bad_records:
            details = "\n- ".join(bad_records.mapped("display_name"))
            message = (
                _(
                    "Number of occurence for Many2many or One2many fields "
                    "should be greater or equals to 1.\n"
                    "These lines have an invalid number of "
                    "occurence:\n- %s"
                )
                % details
            )
            raise exceptions.ValidationError(message)

    @api.multi
    @api.constrains("is_one2many", "pattern_export_id")
    def _constrains_is_one2many(self):
        """
        Constrain function for the field is_one2many
        :return:
        """
        if not self.env.context.get("skip_check"):
            bad_records = self.filtered(
                lambda r: r.is_one2many and not r.pattern_export_id
            )
            if bad_records:
                details = "\n- ".join(bad_records.mapped("display_name"))
                message = (
                    _(
                        "The pattern export is required for O2m fields.\n"
                        "Please check these lines:\n- %s"
                    )
                    % details
                )
                raise exceptions.ValidationError(message)

    @api.model
    def _get_last_field(self, model, path):
        if "/" not in path:
            path = path + "/"
        field, path = path.split("/", 1)
        if path:
            model = self.env[model]._fields[field]._related_comodel_name
            return self._get_last_field(model, path)
        else:
            return field, model

    @api.multi
    @api.depends("name", "export_id", "export_id.resource")
    def _compute_is_many2x(self):
        for export_line in self:
            if export_line.export_id.resource and export_line.name:
                field, model = export_line._get_last_field(
                    export_line.export_id.resource, export_line.name
                )
                if self.env[model]._fields[field].type in ["many2one", "many2many"]:
                    export_line.is_many2x = True

    @api.multi
    @api.depends("name", "export_id", "export_id.resource", "is_many2x")
    def _compute_is_many2many(self):
        for export_line in self:
            is_many2many = False
            if (
                export_line.is_many2x
                and export_line.export_id.resource
                and export_line.name
            ):
                field, model = export_line._get_last_field(
                    export_line.export_id.resource, export_line.name
                )
                if self.env[model]._fields[field].type == "many2many":
                    is_many2many = True
            export_line.is_many2many = is_many2many

    @api.multi
    @api.depends("name", "export_id", "export_id.resource", "is_many2x")
    def _compute_is_one2many(self):
        for export_line in self:
            is_one2many = False
            if (
                not export_line.is_many2x
                and export_line.export_id.resource
                and export_line.name
            ):
                field, model = export_line._get_last_field(
                    export_line.export_id.resource, export_line.name
                )
                if self.env[model]._fields[field].type == "one2many":
                    is_one2many = True
            export_line.is_one2many = is_one2many

    @api.multi
    @api.depends("name")
    def _compute_related_model_id(self):
        for export_line in self:
            if export_line.export_id.resource and export_line.name:
                field, model = export_line._get_last_field(
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
            nb_occurence = self._get_nb_occurence()
            for line_added in range(0, nb_occurence):
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

    @api.multi
    def _get_nb_occurence(self):
        """

        @return: int
        """
        self.ensure_one()
        nb_occurence = 1
        if self.is_many2many or self.is_one2many:
            nb_occurence = max(1, self.number_occurence)
        return nb_occurence
