Here is the full workflow for imports and exports in this module. In italics are the modules relevant
to that particular functionality.

Exports
=======

1. Create a filter and a pattern.config for the model to export (*pattern_import_export*)

2. Create an attachment.synchronize.task of type "export" and configure it (*attachment_synchronize*)

3. Create and configure a pattern.export.task using elements of steps 1. and 2.

4. Call pattern.export.task.run_pattern_export_scheduler()

5. Observe the following:

  - A pattern.file is created from the filter and pattern configuration from step 1.
  - The result of that export is in the storage that you configured in step 2.

This is to be used with a cron to call run_pattern_export_scheduler() for automation.


Imports
=======

1. Create a pattern.config (*pattern_import_export*)

2. Create an attachment.synchronize.task of type "Import using pattern" and configure it (*attachment_synchronize*)

3. Call pattern.synchronize.task.run_import_scheduler()

4. Observe the following:

  - Files that match the configuration of attachment_synchronize_task are run through the import procedure
  - For every file, once imported, the patterned import is executed

This is to be used with a cron to call run_import_scheduler() for automation.
