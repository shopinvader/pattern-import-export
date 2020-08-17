# Copyright 2020 Akretion France (http://www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from base64 import b64encode
from contextlib import contextmanager

from odoo.tests import new_test_user

from odoo.addons.queue_job.tests.common import JobMixin

from ..models.ir_exports import COLUMN_X2M_SEPARATOR


class ExportPatternCommon(JobMixin):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
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
        cls.industry1 = cls.env.ref("base.res_partner_industry_A")
        cls.industry2 = cls.env.ref("base.res_partner_industry_B")
        cls.industries = cls.industry1 | cls.industry2
        cls.partner_cat1 = cls.env.ref("base.res_partner_category_3")
        cls.partner_cat2 = cls.env.ref("base.res_partner_category_11")
        cls.partner_catgs = cls.partner_cat1 | cls.partner_cat2
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
        # generate xmlid
        cls.users.export_data(["id"])
        cls.partners = cls.partner_1 | cls.partner_2 | cls.partner_3
        cls.company1 = cls.env.ref("base.main_company")
        cls.company2 = cls.env["res.company"].create(
            {
                "name": "Awesome company",
                "user_ids": [
                    (
                        6,
                        0,
                        [cls.user1.id, cls.user2.id, cls.env.ref("base.user_admin").id],
                    )
                ],
            }
        )
        cls.company3 = cls.env["res.company"].create(
            {
                "name": "Bad company",
                "user_ids": [(6, 0, [cls.user1.id, cls.env.ref("base.user_admin").id])],
            }
        )
        cls.company4 = cls.env["res.company"].create({"name": "Ignored company"})
        cls.companies = cls.company1 | cls.company2 | cls.company3
        cls.separator = COLUMN_X2M_SEPARATOR
        cls.ir_exports = cls.env.ref("pattern_import_export.demo_export")
        cls.ir_exports_m2m = cls.env.ref("pattern_import_export.demo_export_m2m")
        cls.ir_exports_o2m = cls.env.ref("pattern_import_export.demo_export_o2m")
        cls.empty_attachment = cls.env["ir.attachment"].create(
            {
                "datas": b64encode(b"a"),
                "datas_fname": "a_file_name",
                "name": "a_file_name",
            }
        )

    def _get_attachment(self, record):
        """
        Get the first attachment from given recordset
        @param record: recordset
        @return: ir.attachment
        """
        return self.env["ir.attachment"].search(
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

        self.env["ir.exports"]._patch_method("_read_import_data", _read_import_data)
        yield
        self.env["ir.exports"]._revert_method("_read_import_data")
