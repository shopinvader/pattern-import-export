# Copyright 2020 Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Pattern Import Export",
    "summary": "Pattern for import or export from or to excel files",
    "version": "12.0.1.0.0",
    "category": "Extra Tools",
    "author": "Akretion, Odoo Community Association (OCA)",
    "website": "http://www.akretion.com",
    "license": "AGPL-3",
    "depends": ["base", "queue_job", "document", "base_export_manager"],
    "external_dependencies": {"python": ["xlsxwriter", "xlrd"]},
    "data": [
        "security/ir.model.access.csv",
        "wizard/export_with_pattern.xml",
        "views/pattern_import_export.xml",
    ],
    "installable": True,
}
