This module uses the pattern_import_export and attachment_synchronize modules to automate imports and exports.

The flows work as follows :

Imports
=======

1. A cron calls run_task_import_pattimpex_scheduler() on all synchronization tasks

2. attachment.queue of the appropriate type is generated, file is imported

3. attachment.queue is executed -> pattern.file is generated

4. A job is generated that actually imports the synced file into Odoo, using the appropriate pattern file

Exports
=======

1. A cron triggers service_trigger_exports() for a specific task

2. pattern.import.export is created, exporting records using domain specified in task -> xlsx

3. Another cron triggers run() on the same task (i.e the export of the xlsx to the storage space)
