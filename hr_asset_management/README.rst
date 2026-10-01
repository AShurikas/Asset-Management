HR Asset Management
===================

This module allows a company to keep track of assets (equipment: laptops,
tools, devices) issued to employees.

Features
--------

* Assets are based on the standard ``maintenance.equipment`` model
  (``hr_maintenance`` provides the employee assignment).
* Issue an asset to an employee with the **Issue** button on the asset form.
  A wizard lets you pick the employee, the issue date and optional notes.
* Return an asset back to stock with the **Return** button.
* Every issue/return operation is stored in the *Issue History*
  (``hr.asset.issue``) model with a unique reference number.
* An asset cannot be issued to two employees at the same time —
  the constraint is enforced both in the wizard and on the model level.
* Number of days an asset is issued is computed automatically on the issue
  record and on the asset itself.
* Issue history kanban is grouped by asset; grouping by employee,
  department and issue month is available in the search view.
* Printable PDF report **Asset Issue Act** for each issue record
  (available under the *Print* menu of the issue form and list).
* Smart buttons on the asset and employee forms show related issue records.
* Issuing and returning assets is restricted to the *Equipment Manager*
  group (``maintenance.group_equipment_manager``); other users can only
  view the issue history.
