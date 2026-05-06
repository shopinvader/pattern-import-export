Configuring a pattern
~~~~~~~~~~~~~~~~~~~~~
First you have to define a pattern:

1. Go on the Import/Export->Patterns menu
2. Create your pattern with fields to export

You can refer to the examples in demo data.


Exporting
---------
* Open the tree view of any model and tick some record selection boxes.
* In the sidebar, click on the "Export with Pattern" button
* Select the pattern that you wish to use, click export and download the generated file.
* A "Pattern file" is created, and its job along with it. Depending on the success or failure of the job,
  you will receive a red/green notification on your window.


Importing
---------
You have two options:

* Open the tree view of any model and tick some record selection boxes (for this step, these don't matter, we only just want to show the sidebar).
* In the sidebar, click on the "Import with Pattern" button
* Select a pattern, upload your file and click import.
* A "Pattern file" is created, and its job along with it. Depending on the success or failure of the job, you
  will receive a red/green notification on your window. You can check the details in the appropriate Import/Export menu.

Or:

* Access the Import wizard through the Import/Export menu
* Select a pattern
* Click on the "Import" button


Import syntax
-------------

One of the strength of pattern_import_export module is the ability to
reference records by natural keys (business keys) instead of technical keys (xmlid or database id).

One or more columns can be the natural key of the record to find and update or to create a new record.
Each column in the natural key has to be suffixed by "#key".

One or more columns can be used as foreign keys can be accessed with "|" syntax.  (for instance on partner: country_id|code )


Example
-------

Here is an example of a simple update on ``product.product``:
Existing record:

- id: 10
- name: "Product 1"
- default_code: "PRD1"

The generated export will look like:

+---------------------+-----------+--------------+
| id                  | name      | default_code |
+=====================+===========+==============+
| 10                  | Product 1 | PRD1         |
+---------------------+-----------+--------------+

Updated file

+---------------------+---------------+--------------+
| id                  | name          | default_code |
+=====================+===============+==============+
| 10                  | Product 1-bis | PRD1B        |
+---------------------+---------------+--------------+

After import, our record will have been updated:

- xml id: "__export__.product1"
- name: "Product 1-bis"
- default_code: "PRD1B"

Now, let's update some relational fields. Here is some more of our starting data:

- seller_ids:

 - id (of the seller_id which is a res.partner): 22
 - name (seller): Partner 1
 - price: 10

The generated export should be like

+---------------------+-----------+--------------+----------------------+--------------------+
| id                  | name      | default_code | seller_ids|1|id      | seller_ids|1|price |
+=====================+===========+==============+======================+====================+
| 10                  | Product 1 | PRD1         | 22                   | 10                 |
+---------------------+-----------+--------------+----------------------+--------------------+

Let's say "ref" is a unique-constrained Char field. For the seller, instead of using its id, let's use its ref.

+---------------------+-----------+--------------+---------------------------+--------------------+
| id                  | name      | default_code | seller_ids|1|ref#key      | seller_ids|1|price |
+=====================+===========+==============+===========================+====================+
| 10                  | Product 1 | PRD1         | partner1-ref              | 10                 |
+---------------------+-----------+--------------+---------------------------+--------------------+

So this ``#key`` means that Odoo should search for a ``res.partner`` where the ref matches the cell value.

Lets take another example, instead of using the id, we want to use the product's default_code as key.

+---------------------+-----------+------------------+---------------------------+--------------------+
| id                  | name      | default_code#key | seller_ids|1|ref#key      | seller_ids|1|price |
+=====================+===========+==================+===========================+====================+
|                     | Product 1 | PRD1             | partner1-ref              | 10                 |
+---------------------+-----------+------------------+---------------------------+--------------------+

Odoo will search the product with the matching ``default_code`` and update it.


Technically
~~~~~~~~~~~
Add a new export format
-----------------------
1. Inherit the ``ir.exports`` model.
2. Add your new file format in the selection field ``export_format``;
3. Implements functions ``_export_with_record_<format>`` and ``_read_import_data_<format>``.

Please take care of iterators (``yield``) to avoid loading full file into the system memory.
