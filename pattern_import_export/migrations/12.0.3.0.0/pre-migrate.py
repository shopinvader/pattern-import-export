import logging

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)


@openupgrade.migrate()
def migrate(env, version):
    cr = env.cr
    openupgrade.rename_models(cr, [("patterned.import.export", "pattern.file")])
    openupgrade.rename_tables(cr, [("patterned_import_export", "pattern_file")])
    openupgrade.rename_columns(cr, {"pattern_file": [("status", "state")]})
