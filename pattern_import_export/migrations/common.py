#  Copyright (c) Akretion 2020
#  License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

OBSOLETE_VIEWS = [
    "pattern_import_export_synchronize.ir_exports_form_view",
    "pattern_import_export_csv.ir_exports_form_view",
    "pattern_import_export_xlsx.ir_exports_form_view",
    "pattern_import_export.ir_exports_form_view",
    "pattern_import_export.act_open_pattern_view",
]


def delete_obsolete_views(env):
    for el in OBSOLETE_VIEWS:
        # avoid lock due to fkey constraint
        view = env.ref(el, raise_if_not_found=False)
        if view:
            view.unlink()
