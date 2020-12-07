# Copyright 2020 Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Pattern Import Export",
    "summary": "Pattern for import or export",
    "version": "12.0.6.2.0",
    "category": "Extra Tools",
    "author": "Akretion, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/pattern-import-export",
    "license": "AGPL-3",
    "depends": [
        "base_jsonify",
        "queue_job",
        "document",
        "base_export_manager",
        "web_notify",
    ],
    "data": [
        "security/pattern_security.xml",
        "security/ir.model.access.csv",
        "wizard/export_with_pattern.xml",
        "wizard/import_pattern_wizard.xml",
        "views/pattern_config.xml",
        "views/pattern_file.xml",
        "views/pattern_chunk.xml",
        "views/menuitems.xml",
        "views/templates.xml",
    ],
    "demo": ["demo/demo.xml"],
    "external_dependencies": {"python": ["numpy", "openupgradelib"]},
    "installable": True,
}
