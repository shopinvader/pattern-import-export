#  Copyright (c) Akretion 2020
#  License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

from openupgradelib import openupgrade

FIELDS_SRC = [
    "use_description",
    "pattern_file",
    "pattern_file_name",
    "pattern_last_generation_date",
    "export_format",
    "partial_commit",
    "flush_step",
    "id",
]

FIELDS_DST = [
    "use_description",
    "pattern_file",
    "pattern_file_name",
    "pattern_last_generation_date",
    "export_format",
    "partial_commit",
    "flush_step",
    "export_id",
]


@openupgrade.migrate()
def migrate(env, version):
    def migrate_ir_exports_misc_fields():
        fields_src = ",".join(FIELDS_SRC)
        fields_dst = ",".join(FIELDS_DST)
        env.cr.execute(
            """
            INSERT INTO pattern_config ({fields_dst})
            SELECT {fields_src}
            FROM ir_exports WHERE is_pattern IS TRUE
            """.format(
                fields_src=fields_src, fields_dst=fields_dst
            )
        )

    def migrate_ir_exports_line_subpattern():
        env.cr.execute(
            """
            UPDATE ir_exports_line l
            SET sub_pattern_config_id = p.id
            FROM pattern_config p
            WHERE
                l.pattern_export_id = p.export_id
            """
        )

    migrate_ir_exports_misc_fields()
    migrate_ir_exports_line_subpattern()
