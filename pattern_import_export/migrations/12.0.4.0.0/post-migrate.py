#  Copyright (c) Akretion 2020
#  License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    params = {}
    for field, default_value in [
        ("pattern_file", "NULL"),
        ("pattern_file_name", "NULL"),
        ("pattern_last_generation_date", "NULL"),
        ("partial_commit", "True"),
        ("flush_step", "500"),
        ("export_format", "NULL"),
    ]:
        if openupgrade.column_exists(env.cr, "ir_exports", field):
            params[field] = f'"{field}"'
        else:
            params[field] = default_value

    env.cr.execute(
        f"""
        INSERT INTO pattern_config (
             use_description,
             pattern_file,
             pattern_file_name,
             pattern_last_generation_date,
             export_format,
             partial_commit,
             flush_step,
             export_id
        )
        SELECT
             use_description,
             {params["pattern_file"]},
             {params["pattern_file_name"]},
             {params["pattern_last_generation_date"]},
             {params["export_format"]},
             {params["partial_commit"]},
             {params["flush_step"]},
             id
        FROM ir_exports WHERE is_pattern IS TRUE
        """
    )

    env.cr.execute(
        """
        UPDATE ir_exports_line l
        SET sub_pattern_config_id = p.id
        FROM pattern_config p
        WHERE
            l.pattern_export_id = p.export_id
        """
    )
