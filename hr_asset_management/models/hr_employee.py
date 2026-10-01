from odoo import api, fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    asset_issue_ids = fields.One2many(
        'hr.asset.issue',
        'employee_id',
        string='Asset Issues',
        copy=False,
    )
    asset_issue_count = fields.Integer(
        string='Asset Count',
        compute='_compute_asset_issue_count',
    )

    @api.depends('asset_issue_ids')
    def _compute_asset_issue_count(self):
        for employee in self:
            employee.asset_issue_count = len(employee.asset_issue_ids)

    def action_view_asset_issues(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id(
            'hr_asset_management.action_hr_asset_issue')
        action['domain'] = [('employee_id', '=', self.id)]
        action['context'] = {'default_employee_id': self.id}
        return action
