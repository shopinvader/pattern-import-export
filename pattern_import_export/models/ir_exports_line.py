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
    related_model_id = fields.Many2one(
        "ir.model",
        string="Related model",
        compute="_compute_related_model_id",
        store=True,
    )
    number_occurence = fields.Integer(
        string="# Occurence",
        default=1,
        help="Number of column to create to display this Many2many field.\n"
        "Value should be >= 1",
    )

    @api.multi
    @api.constrains("number_occurence", "is_many2many")
    def _constrains_number_occurence(self):
        """
        Constrain function for the field number_occurence.
        Ensure the number_occurence is at least 1 when is_many2many is True.
        :return:
        """
        bad_records = self.filtered(lambda r: r.is_many2many and r.number_occurence < 1)
        if bad_records:
            details = "\n- ".join(bad_records.mapped("display_name"))
            message = (
                _(
                    "Number of occurence for Many2many fields should be "
                    "greater or equals to 1.\n"
                    "These lines have an invalid number of "
                    "occurence:\n- %s"
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

    def _add_xlsx_constraint(self, sheet, col, ad_sheet, ad_row):
        source = "=" + ad_sheet.name + "!$A$2:$A$" + str(ad_row + 100)
        sheet.data_validation(
            1, col, 1048576, col, {"validate": "list", "source": source}
        )
        return True
