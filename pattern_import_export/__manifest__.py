# Copyright 2020 Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Pattern Import Export",
    "summary": "Pattern for import or export",
    "version": "12.0.2.2.0",
    "category": "Extra Tools",
    "author": "Akretion, Odoo Community Association (OCA)",
    "website": "http://www.akretion.com",
    "license": "AGPL-3",
    "depends": [
        "base_jsonify",
        "queue_job",
        "document",
        "base_export_manager",
        "web_notify",
    ],
    "data": [
        "security/ir.model.access.csv",
        "wizard/export_with_pattern.xml",
        "wizard/import_pattern_wizard.xml",
        "views/ir_exports.xml",
        "views/patterned_import_export.xml",
        "views/menuitems.xml",
    ],
    "demo": ["demo/demo.xml"],
    "external_dependencies": {"python": ["numpy"]},
    "installable": True,
}
