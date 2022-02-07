# Copyright 2021 Akretion (https://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


{
    "name": "Chunk Processing",
    "summary": "Base module for processing chunk",
    "version": "14.0.1.0.0",
    "category": "Uncategorized",
    "website": "https://github.com/shopinvader/pattern-import-export",
    "author": " Akretion",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "external_dependencies": {
        "python": [],
        "bin": [],
    },
    "depends": [
        "queue_job",
        "component",
        "web_refresher",
    ],
    "data": [
        "views/chunk_item_view.xml",
        "views/chunk_group_view.xml",
        "views/templates.xml",
    ],
    "demo": [],
}
