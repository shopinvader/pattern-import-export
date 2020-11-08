#  Copyright (c) Akretion 2020
#  License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

from openupgradelib import openupgrade

# relative imports don't work here
from odoo.addons.pattern_import_export.migrations.common import delete_obsolete_views


@openupgrade.migrate()
def migrate(env, version):
    delete_obsolete_views(env)
