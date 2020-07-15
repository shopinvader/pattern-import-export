Functionally
~~~~~~~~~~~~
To use this module, you only have to install it (please check python dependencies).

First you have to define a pattern:

1. Go on the Import/Export->Patterns menu;
2. Create your pattern with fields to export.


Do export
---------
On a Tree view, select records to export (or into the Form view) and on the
"action" options, pick the "Export with pattern".
On the new wizard, fill the Export pattern to use and click on the "Export button".

A job is now created and your export will be executed as soon as possible (depending on system charge).

Do import
---------
Once your file is edited, you can upload it to create or update related records.

On a Tree view, select at least one record (not necessarily ones to update) and on the "action" button, select "Import with pattern".
A new wizard is open and select a pattern to do the import.

Into your file, you can add/remove/rename column as you want (with specific format and with existing field's name).

You can also add some fields wo aren't into the pattern and these fields' will be updated.

To be more user-friendly, it's not mandatory to work with ID or XML ID to update existing record.
You can just add "/key" at the end of the column name (without spaces) and the column will become the key (please ensure the field used as key as necessary constraints).

Example of simple update on ``product.product``:
Existing record:

- xml id: "__export__.product1"
- name: "Product 1"
- default_code: "PRD1"

The generated export should be like

+---------------------+-----------+--------------+
| id                  | name      | default_code |
+=====================+===========+==============+
| __export__.product1 | Product 1 | PRD1         |
+---------------------+-----------+--------------+

Updated file

+---------------------+---------------+--------------+
| id                  | name          | default_code |
+=====================+===============+==============+
| __export__.product1 | Product 1-bis | PRD1B        |
+---------------------+---------------+--------------+

Then your record will be updated:

- xml id: "__export__.product1"
- name: "Product 1-bis"
- default_code: "PRD1B"

On the same example, you can also edit more complex fields like relational fields:

- seller_ids:

 - xml id (of the seller/partner): "__export__.partner1"
 - name (seller): Partner 1
 - price: 10

The generated export should be like

+---------------------+-----------+--------------+----------------------+--------------------+
| id                  | name      | default_code | seller_ids|1|name|id | seller_ids|1|price |
+=====================+===========+==============+======================+====================+
| __export__.product1 | Product 1 | PRD1         | __export__.partner1  | 10                 |
+---------------------+-----------+--------------+----------------------+--------------------+

The name (seller) is into this format because seller_ids is a reference to many sellers (so specify the ``|1|``) and the name (seller) is itself a reference to a partner. So we have to specify his ID.

You can also specify a partner reference (who is considered as unique) like this:

+---------------------+-----------+--------------+---------------------------+--------------------+
| id                  | name      | default_code | seller_ids|1|name|ref/key | seller_ids|1|price |
+=====================+===========+==============+===========================+====================+
| __export__.product1 | Product 1 | PRD1         | partner1-ref              | 10                 |
+---------------------+-----------+--------------+---------------------------+--------------------+

So this ``/key`` say that Odoo should search for a ``res.partner`` where the ref is the cell's value.


It's also possible to update a product (for this example) based on the default_code instead of the ID.

+---------------------+-----------+------------------+---------------------------+--------------------+
| id                  | name      | default_code/key | seller_ids|1|name|ref/key | seller_ids|1|price |
+=====================+===========+==================+===========================+====================+
|                     | Product 1 | PRD1             | partner1-ref              | 10                 |
+---------------------+-----------+------------------+---------------------------+--------------------+

So Odoo will search the product with the ``default_code`` and update it.


Technically
~~~~~~~~~~~
Add a new export format
-----------------------
1. Inherit the ``ir.exports`` model.
2. Add your new file format in the selection field ``export_format``;
3. Implements functions ``_export_with_record_<format>`` and ``_read_import_data_<format>``.

Please take care of iterators (``yield``) to avoid loading full file into the system memory.
