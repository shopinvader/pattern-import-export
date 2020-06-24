# Copyright 2020 Akretion France (http://www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import base64
from contextlib import contextmanager

from odoo.tests import new_test_user

from odoo.addons.queue_job.tests.common import JobMixin

from ..models.ir_exports import COLUMN_X2M_SEPARATOR


class ExportPatternCommon(JobMixin):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.Exports = cls.env["ir.exports"]
        cls.ExportsLine = cls.env["ir.exports.line"]
        cls.ExportsTab = cls.env["ir.exports.select.tab"]
        cls.Company = cls.env["res.company"]
        cls.Attachment = cls.env["ir.attachment"]
        cls.ExportPatternWizard = cls.env["export.pattern.wizard"]
        cls.Users = cls.env["res.users"]
        cls.Partner = cls.env["res.partner"]
        cls.PartnerIndustry = cls.env["res.partner.industry"]
        cls.PartnerCategory = cls.env["res.partner.category"]
        country_code_field = cls.env.ref("base.field_res_country__code")
        country_model = cls.env.ref("base.model_res_country")
        company_model = cls.env.ref("base.model_res_company")
        cls.partner_1 = cls.env.ref("base.res_partner_1")
        cls.partner_2 = cls.env.ref("base.res_partner_2")
        cls.partner_3 = cls.env.ref("base.res_partner_3")
        cls.country_be = cls.env.ref("base.be")
        cls.country_us = cls.env.ref("base.us")
        cls.group_manager = cls.env.ref("base.group_erp_manager")
        cls.group_no_one = cls.env.ref("base.group_no_one")
        cls.group_job = cls.env.ref("queue_job.group_queue_job_manager")
        cls.field_user_name = cls.env.ref("base.field_res_users__name")
        cls.field_user_id = cls.env.ref("base.field_res_users__id")
        cls.field_user_login = cls.env.ref("base.field_res_users__login")
        cls.industry1 = cls.PartnerIndustry.search([], limit=1)
        cls.industry2 = cls.PartnerIndustry.search([], limit=1, offset=1)
        cls.industries = cls.industry1 | cls.industry2
        # Used to generate XML id automatically
        cls.industries.export_data(["id"])
        cls.partner_cat1 = cls.PartnerCategory.search([], limit=1)
        cls.partner_cat2 = cls.PartnerCategory.search([], limit=1, offset=1)
        cls.partner_catgs = cls.partner_cat1 | cls.partner_cat2
        # Used to generate XML id automatically
        cls.partner_catgs.export_data(["id"])
        cls.user1 = new_test_user(
            cls.env, login="tonic", name=cls.partner_1.name, partner_id=cls.partner_1.id
        )
        cls.user2 = new_test_user(
            cls.env, login="tazz", name=cls.partner_1.name, partner_id=cls.partner_1.id
        )
        cls.user3 = new_test_user(
            cls.env,
            login="tenebre",
            name=cls.partner_2.name,
            partner_id=cls.partner_2.id,
        )
        cls.users = cls.user1 | cls.user2 | cls.user3
        # Used to generate XML id automatically
        cls.users.export_data(["id"])
        cls.partners = cls.partner_1 | cls.partner_2 | cls.partner_3
        cls.company1 = cls.env.ref("base.main_company")
        cls.company2 = cls.Company.create(
            {
                "name": "Awesome company",
                "user_ids": [
                    (4, cls.env.user.id),
                    (4, cls.user1.id),
                    (4, cls.user2.id),
                ],
            }
        )
        cls.company3 = cls.Company.create(
            {
                "name": "Bad company",
                "user_ids": [(4, cls.env.user.id), (4, cls.user1.id)],
            }
        )
        cls.companies = cls.company1 | cls.company2 | cls.company3
        # Used to generate XML id automatically
        cls.companies.export_data(["id"])
        company_name_field = cls.env.ref("base.field_res_company__name")
        exports_vals = {"name": "Partner list", "resource": "res.partner"}
        cls.separator = COLUMN_X2M_SEPARATOR
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
        cls.select_tab_company = cls.ExportsTab.create(select_tab_vals)
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
        cls.ir_exports_o2m = cls.Exports.create(
            {
                "name": "Partner - O2M",
                "resource": "res.partner",
                "export_fields": [
                    (0, False, {"name": "id"}),
                    (0, False, {"name": "name"}),
                    (
                        0,
                        False,
                        {
                            "name": "user_ids",
                            "number_occurence": 3,
                            "pattern_export_id": cls.ir_exports_m2m.id,
                        },
                    ),
                ],
            }
        )
        cls.empty_attachment = cls.Attachment.create(
            {
                "name": "a_file_name",
                "datas": base64.b64encode(b"a"),
                "datas_fname": "a_file_name",
            }
        )

    def _get_attachment(self, record):
        """
        Get the first attachment from given recordset
        @param record: recordset
        @return: ir.attachment
        """
        return self.Attachment.search(
            [("res_model", "=", record._name), ("res_id", "=", record.id)], limit=1
        )

    @contextmanager
    def _mock_read_import_data(self, main_data):
        """
        Mock the _read_import_data from Exports to return directly
        received datafile
        @return:
        """

        def _read_import_data(self, datafile):
            return main_data

        self.Exports._patch_method("_read_import_data", _read_import_data)
        yield
        self.Exports._revert_method("_read_import_data")
