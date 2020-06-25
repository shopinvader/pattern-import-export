# Copyright 2020 Akretion France (http://www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import _, api, exceptions, fields, models


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
    def _get_nb_occurence(self):
        """

        @return: int
        """
        self.ensure_one()
        nb_occurence = 1
        if self.is_many2many or self.is_one2many:
            nb_occurence = max(1, self.number_occurence)
        return nb_occurence
