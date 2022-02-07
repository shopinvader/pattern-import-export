# Copyright 2020 Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Pattern Import Export",
    "summary": "Pattern for import or export",
    "version": "14.0.2.2.1",
    "category": "Extra Tools",
    "author": "Akretion",
    "website": "https://github.com/shopinvader/pattern-import-export",
    "license": "AGPL-3",
    "depends": [
        "base_jsonify",
        "queue_job",
        "base_export_manager",
        "web_notify",
        "base_sparse_field_list_support",
        "base_sparse_field",
        "chunk_processing",
    ],
    "data": [
        "security/pattern_security.xml",
        "security/ir.model.access.csv",
        "wizard/export_with_pattern.xml",
        "wizard/import_pattern_wizard.xml",
        "views/pattern_config.xml",
        "views/pattern_file.xml",
        "views/menuitems.xml",
        "data/queue_job_channel_data.xml",
        # "data/queue_job_function_data.xml",
    ],
    "demo": ["demo/demo.xml"],
    "installable": True,
}
