This module allows to create some patterns to export records.
A pattern is defined by a list of fields to export.
This module only create a common data structure used to do the real export into the expected format.

The import is also implemented to create or update records.
Fields to update (or create) shouldn't be necessarily into the pattern (but the base model should match).
That means if your pattern only contains the name field, you can also update others fields without updating your pattern.
