Overview
~~~~~~~~

This module extends the import/export capabilities of Odoo.

Patterns are simply a type of ir.exports model, so you can define them with the native Odoo widget to define export lists.

This module only create a common data structure. Other modules will be used to add specific file type support like excel and csv.


Features
--------

* Key matching: instead of always using IDs, match keys to unique-constrained fields, for example update a product by
  specifying its product_code instead of its database ID or external ID

* One2many and Many2many support: create or update for example invoice lines with a syntax that is very readable and easy to update

* As long as you respect the appropriate format and field names, you are free to add/remove/rename columns, even if they
  are not in the initial Pattern used for the export
