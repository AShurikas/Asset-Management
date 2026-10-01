from odoo import fields, models, _
from odoo.exceptions import ValidationError


class HrAssetIssueWizard(models.TransientModel):
    _name = 'hr.asset.issue.wizard'
    _description = 'Issue Asset to Employee'

    equipment_id = fields.Many2one(
        'maintenance.equipment',
        string='Asset',
        required=True,
        readonly=True,
    )
    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee',
        required=True,
    )
    issue_date = fields.Date(
        required=True,
        default=fields.Date.context_today,
    )
    note = fields.Text(string='Notes')

    def action_confirm(self):
        self.ensure_one()
        if self.equipment_id.current_issue_id:
            raise ValidationError(_(
                'Asset "%(asset)s" is already issued to %(employee)s. '
                'It cannot be issued again until it is returned.',
                asset=self.equipment_id.display_name,
                employee=self.equipment_id.current_issue_id.employee_id.name,
            ))
        self.env['hr.asset.issue'].create({
            'equipment_id': self.equipment_id.id,
            'employee_id': self.employee_id.id,
            'issue_date': self.issue_date,
            'note': self.note,
        })
        return {'type': 'ir.actions.act_window_close'}
