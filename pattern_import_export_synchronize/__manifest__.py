# Copyright 2020 Akretion (http://www.akretion.com).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Attachment Synchronize using patterns",
    "version": "14.0.0.0.0",
    "author": "Akretion",
    "website": "https://github.com/shopinvader/pattern-import-export",
    "maintainers": ["kevinkhao", "sebastienbeau"],
    "license": "AGPL-3",
    "category": "Generic Modules",
    "depends": ["attachment_synchronize", "pattern_import_export"],
    "data": [
        "views/pattern_config_view.xml",
        "security/ir.model.access.csv",
        "views/pattern_export_task_view.xml",
        "views/pattern_file_view.xml",
        "data/queue_job_function_data.xml",
    ],
    "external_dependencies": {"python": ["mock"]},
    "demo": ["demo/demo.xml"],
    "installable": True,
}
