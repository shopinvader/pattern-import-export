# Copyright 2020 Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Pattern Import Export XLSX",
    "summary": "Pattern for import or export from to XLSX files",
    "version": "12.0.1.4.0",
    "category": "Extra Tools",
    "author": "Akretion, Odoo Community Association (OCA)",
    "website": "http://www.akretion.com",
    "license": "AGPL-3",
    "depends": ["pattern_import_export"],
    "external_dependencies": {"python": ["openpyxl"]},
    "demo": ["demo/demo.xml"],
    "data": ["views/ir_exports.xml"],
    "installable": True,
}
