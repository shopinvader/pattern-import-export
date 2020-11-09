#  Copyright (c) Akretion 2020
#  License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    env.cr.execute(
        """
        UPDATE pattern_config
        SET
            export_format = ir_exports.export_format,
            csv_value_delimiter = ir_exports.csv_value_delimiter,
            csv_quote_character = ir_exports.csv_quote_character
        FROM ir_exports
        WHERE export_id = ir_exports.id
        """
    )
