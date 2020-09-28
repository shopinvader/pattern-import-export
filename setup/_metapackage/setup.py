import setuptools

with open("VERSION.txt", "r") as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo12-addons-shopinvader-pattern-import-export",
    description="Meta package for shopinvader-pattern-import-export Odoo addons",
    version=version,
    install_requires=[
        "odoo12-addon-pattern_import_export",
        "odoo12-addon-pattern_import_export_xlsx",
    ],
    classifiers=["Programming Language :: Python", "Framework :: Odoo",],
)
