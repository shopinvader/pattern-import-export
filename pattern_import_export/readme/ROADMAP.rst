Problems are related to UI. They are also present in base_export_manager dependency. If entering correct data the first time, the problems can be ignored.

The following issues are closely related and stem from the first one:

* Currently, base_export_manager does not support modifying a line's relational fields (a crash occurs if you try it)
* Unticking the "Use tab" boolean should clear the previously selected tab_filter_id
* Changing a line's field should clear the previously selected tab_filter_id
