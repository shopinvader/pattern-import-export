# Copyright 2020 Akretion (https://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import base64
from io import BytesIO
from os import path

# TODO FIXME somehow Travis complains that openpyxl isn't there,
# the warning shows only here and not in any other import of openpyxl?
# pylint: disable=missing-manifest-dependency
import openpyxl

from odoo.tests import SavepointCase
from odoo.tools import mute_logger

# helper to dump the result of the import into an excel file
DUMP_OUTPUT = False


PATH = path.dirname(__file__) + "/fixtures/"


class TestPatternImport(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(
            context=dict(
                cls.env.context, test_queue_job_no_delay=True  # no jobs thanks
            )
        )
        cls.ir_export_partner = cls.env["ir.exports"].create(
            {
                "name": "Partner",
                "resource": "res.partner",
                "is_pattern": True,
                "export_format": "xlsx",
            }
        )
        cls.ir_export_users = cls.env["ir.exports"].create(
            {
                "name": "User",
                "resource": "res.users",
                "is_pattern": True,
                "export_format": "xlsx",
            }
        )
        cls.user_admin = cls.env.ref("base.user_admin")
        cls.user_demo = cls.env.ref("base.user_demo")

    @classmethod
    def _load_file(cls, filename, export_id):
        data = base64.b64encode(open(PATH + filename, "rb").read())
        wizard = cls.env["import.pattern.wizard"].create(
            {
                "ir_exports_id": export_id.id,
                "import_file": data,
                "filename": "example.xlsx",
            }
        )
        wizard.action_launch_import()

        if DUMP_OUTPUT:
            attachment = cls.env["patterned.import.export"].search(
                [], limit=1, order="id desc"
            )
            output_name = filename.replace(".xlsx", ".result.xlsx")
            with open(output_name, "wb") as output:
                output.write(base64.b64decode(attachment.datas))

    def test_import_partners_ok(self):
        """
        * Lookup by email
        * Update some o2m fields
        """
        self._load_file("example.partners.ok.xlsx", self.ir_export_partner)
        # check first line
        partner = self.env.ref("base.res_partner_1")

        self.assertEqual(partner.name, "Wood Corner Updated")
        self.assertEqual(partner.email, "wood.corner26@example.com")
        self.assertEqual(partner.phone, "111111111")
        self.assertEqual(partner.country_id.code, "FR")

        # In demo data we have 3 childs
        # after the import we should still have 3 childs
        # In a long term we should have an option
        # to active/remove unwanted o2m
        self.assertEqual(len(partner.child_ids), 3)

        contact_1, contact_2, contact_3 = partner.child_ids.sorted("id")
        self.assertEqual(contact_1.id, self.env.ref("base.res_partner_address_1").id)
        self.assertEqual(contact_1.name, "Willie Burke Updated")
        self.assertEqual(contact_1.email, "willie.burke80.updated@example.com")
        self.assertEqual(contact_1.function, "Service Manager")

        self.assertEqual(contact_2.id, self.env.ref("base.res_partner_address_2").id)
        self.assertEqual(contact_2.name, "Ron Gibson Updated")
        self.assertEqual(contact_2.email, "ron.gibson76.updated@example.com")
        self.assertEqual(contact_2.function, "Store Manager")

        # check second line
        partner = self.env.ref("base.res_partner_2")

        self.assertEqual(partner.name, "Deco Addict Updated")
        self.assertEqual(partner.country_id.code, "DE")

        self.assertEqual(len(partner.child_ids), 3)

        contact_1, contact_2, contact_3 = partner.child_ids.sorted("id")
        self.assertEqual(contact_1.id, self.env.ref("base.res_partner_address_3").id)
        self.assertEqual(contact_2.id, self.env.ref("base.res_partner_address_4").id)

        # check three line creation

        partner = self.env["res.partner"].search(
            [("email", "=", "akretion-pattern@example.com")]
        )
        self.assertEqual(len(partner), 1)
        self.assertEqual(partner.name, "Akretion")
        self.assertEqual(partner.phone, "333333333")
        self.assertEqual(partner.country_id.code, "FR")
        self.assertEqual(len(partner.child_ids), 2)

        contact_1, contact_2 = partner.child_ids.sorted("id")
        self.assertEqual(contact_1.name, "Sebastien")
        self.assertEqual(contact_1.email, "seb-pattern@example.com")
        self.assertEqual(contact_1.function, "Service Manager")

        self.assertEqual(contact_2.name, "Raph")
        self.assertEqual(contact_2.email, "raph-pattern@example.com")
        self.assertEqual(contact_2.function, "Store Manager")

    @mute_logger("odoo.sql_db")
    def test_import_partners_fail(self):
        """
        * Lookup by email
        * Report error in excel file through wrong email
        """
        self._load_file("example.partners.fail.xlsx", self.ir_export_partner)
        self.env.clear()

        # check that nothong have been done
        partner = self.env.ref("base.res_partner_1")

        self.assertEqual(partner.name, "Wood Corner")

        partner = self.env.ref("base.res_partner_2")

        self.assertEqual(partner.name, "Deco Addict")

        partner = self.env["res.partner"].search(
            [("email", "=", "akretion-pattern@example.com")]
        )
        self.assertEqual(len(partner), 0)
        attachment = self.env["patterned.import.export"].search(
            [], order="id desc", limit=1
        )
        infile = BytesIO(base64.b64decode(attachment.datas))
        wb = openpyxl.load_workbook(filename=infile)
        ws = wb.worksheets[0]
        self.assertEqual(ws["A1"].value, "#Error")
        self.assertIsNone(ws["A2"].value)
        self.assertIsNone(ws["A3"].value)
        self.assertIsNone(ws["A4"].value)
        self.assertIn(
            'new row for relation "res_partner" '
            'violates check constraint "res_partner_check_name"',
            ws["A5"].value,
        )

    def test_import_users_ok(self):
        """
        * Lookup by DB ID
        * Simple update
        """
        self._load_file("example.users.ok.xlsx", self.ir_export_users)
        self.env.clear()
        self.assertEqual(self.user_admin.name, "Mitchell Admin Updated")
        self.assertEqual(self.user_demo.name, "Marc Demo Updated")

    def test_import_users_descriptive_ok(self):
        """
        * Use descriptive headers
        * Lookup by DB ID
        * Simple update
        """
        self.ir_export_users.use_description = True
        self._load_file("example.users.descriptive.ok.xlsx", self.ir_export_users)
        self.env.clear()
        self.assertEqual(self.user_admin.name, "Mitchell Admin Updated")
        self.assertEqual(self.user_demo.name, "Marc Demo Updated")

    # TODO FIXME
    @mute_logger("odoo.sql_db")
    def disable_test_import_users_fail(self):
        """
        * Lookup by external ID
        * Report error in excel file through external id not found
        """
        self._load_file("example.users.fail.xlsx", self.ir_export_users)
        self.env.clear()
        attachment = self.env["ir.attachment"].search([], order="id desc", limit=1)
        infile = BytesIO(base64.b64decode(attachment.datas))
        wb = openpyxl.load_workbook(filename=infile)
        ws = wb.worksheets[0]
        self.assertEqual(ws["A1"].value, "#Error")
        self.assertTrue(ws["A2"].value)
        self.assertTrue(ws["A3"].value)
