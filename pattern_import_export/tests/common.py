# Copyright 2020 Akretion France (http://www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from ..models.ir_exports import COLUMN_M2M_SEPARATOR
from odoo.addons.queue_job.tests.common import JobMixin


class ExportPatternCommon(JobMixin):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.Exports = cls.env['ir.exports']
        cls.ExportsLine = cls.env['ir.exports.line']
        cls.ExportsTab = cls.env['ir.exports.select.tab']
        cls.Company = cls.env['res.company']
        cls.Attachment = cls.env['ir.attachment']
        cls.ExportPatternWizard = cls.env['export.pattern.wizard']
        cls.Users = cls.env['res.users']
        cls.Partner = cls.env['res.partner']
        country_code_field = cls.env.ref("base.field_res_country__code")
        country_model = cls.env.ref("base.model_res_country")
        company_model = cls.env.ref("base.model_res_company")
        cls.company1 = cls.env.ref('base.main_company')
        company_name_field = cls.env.ref("base.field_res_company__name")
        exports_vals = {"name": "Partner list", "resource": "res.partner"}
        cls.separator = COLUMN_M2M_SEPARATOR
        cls.ir_exports = cls.Exports.create(exports_vals)
        select_tab_vals = {
            "name": "Country list",
            "model_id": country_model.id,
            "field_id": country_code_field.id,
            "domain": "[('code', 'in', ['FR', 'BE', 'US'])]",
        }
        cls.select_tab = cls.ExportsTab.create(select_tab_vals)
        exports_line_vals = [
            {"name": "id", "export_id": cls.ir_exports.id},
            {"name": "name", "export_id": cls.ir_exports.id},
            {"name": "street", "export_id": cls.ir_exports.id},
            {
                "name": "country_id",
                "export_id": cls.ir_exports.id,
                "select_tab_id": cls.select_tab.id,
            },
            {
                "name": "child_ids/country_id",
                "export_id": cls.ir_exports.id,
                "select_tab_id": cls.select_tab.id,
            },
        ]
        cls.ExportsLine.create(exports_line_vals)
        # M2M part
        select_tab_vals = {
            "name": "Company list",
            "model_id": company_model.id,
            "field_id": company_name_field.id,
        }
        cls.select_tab_company = cls.ExportsTab.create(
            select_tab_vals
        )
        cls.ir_exports_m2m = cls.Exports.create(
            {
                "name": "Users list - M2M",
                "resource": "res.users",
                "export_fields": [
                    (0, False, {"name": "id"}),
                    (0, False, {"name": "name"}),
                    (
                        0,
                        False,
                        {
                            "name": "company_ids",
                            "number_occurence": 1,
                            "select_tab_id": cls.select_tab_company.id,
                        },
                    ),
                ],
            }
        )
        cls.partner_1 = cls.env.ref("base.res_partner_1")
        cls.partner_2 = cls.env.ref("base.res_partner_2")
        cls.partner_3 = cls.env.ref("base.res_partner_3")
        cls.partners = cls.partner_1 | cls.partner_2 | cls.partner_3
        cls.company2 = cls.Company.create(
            {"name": "Awesome company", "user_ids": [(4, cls.env.user.id)]}
        )
        cls.company3 = cls.Company.create(
            {"name": "Bad company", "user_ids": [(4, cls.env.user.id)]}
        )
        cls.companies = cls.company1 | cls.company2 |cls.company3

    def _get_header_from_export(self, export):
        """
        Get the header of given export
        @param export: ir.exports recordset
        @return: list of str
        """
        header = []
        for export_line in export.export_fields:
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

    def _get_attachment(self, record):
        """
        Get the first attachment from given recordset
        @param record: recordset
        @return: ir.attachment
        """
        return self.Attachment.search([
            ("res_model", "=", record._name),
            ("res_id", "=", record.id),
        ], limit=1)
