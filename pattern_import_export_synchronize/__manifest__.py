# Copyright 2020 Akretion (http://www.akretion.com).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Attachment Synchronize using patterns",
    "version": "12.0.1.1.0",
    "author": "Akretion,Odoo Community Association (OCA)",
    "website": "https://github.com/oca/server-tools",
    "maintainers": ["kevinkhao", "sebastienbeau"],
    "license": "AGPL-3",
    "category": "Generic Modules",
    "depends": ["attachment_synchronize", "pattern_import_export"],
    "data": [
        "views/ir_exports_view.xml",
        "security/ir.model.access.csv",
        "views/pattern_export_task_view.xml",
        "views/pattern_file_view.xml",
        "views/queue_job_view.xml",
    ],
    "demo": ["demo/demo.xml"],
}
