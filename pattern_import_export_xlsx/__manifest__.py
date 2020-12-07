# Copyright 2020 Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Pattern Import Export XLSX",
    "summary": "Pattern for import or export from to XLSX files",
    "version": "12.0.5.0.0",
    "category": "Extra Tools",
    "author": "Akretion, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/pattern-import-export",
    "license": "AGPL-3",
    "depends": ["pattern_import_export"],
    "external_dependencies": {"python": ["openpyxl"]},
    "demo": ["demo/demo.xml"],
    "data": ["views/pattern_config.xml"],
    "installable": True,
}
