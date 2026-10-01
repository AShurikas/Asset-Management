from odoo import api, fields, models, _
from odoo.exceptions import UserError


class MaintenanceEquipment(models.Model):
    _inherit = 'maintenance.equipment'

    asset_issue_ids = fields.One2many(
        'hr.asset.issue',
        'equipment_id',
        string='Issue History',
        copy=False,
    )
    current_issue_id = fields.Many2one(
        'hr.asset.issue',
        string='Current Issue',
        compute='_compute_current_issue',
        store=True,
    )
    asset_issue_count = fields.Integer(
        string='Issue Count',
        compute='_compute_asset_issue_count',
    )
    days_issued = fields.Integer(
        compute='_compute_days_issued',
    )

    @api.depends('asset_issue_ids.return_date')
    def _compute_current_issue(self):
        for equipment in self:
            equipment.current_issue_id = equipment.asset_issue_ids.filtered(
                lambda issue: not issue.return_date)[:1]

    @api.depends('asset_issue_ids')
    def _compute_asset_issue_count(self):
        for equipment in self:
            equipment.asset_issue_count = len(equipment.asset_issue_ids)

    @api.depends('current_issue_id.issue_date')
    def _compute_days_issued(self):
        today = fields.Date.context_today(self)
        for equipment in self:
            issue = equipment.current_issue_id
            if issue and issue.issue_date:
                equipment.days_issued = (today - issue.issue_date).days
            else:
                equipment.days_issued = 0

    def action_issue(self):
        self.ensure_one()
        if self.current_issue_id:
            raise UserError(_(
                'Asset "%s" is already issued to an employee.',
                self.display_name))
        return {
            'type': 'ir.actions.act_window',
            'name': _('Issue Asset'),
            'res_model': 'hr.asset.issue.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_equipment_id': self.id},
        }

    def action_return_asset(self):
        self.ensure_one()
        if self.current_issue_id:
            self.current_issue_id.action_return()
        elif self.employee_id:
            # asset was assigned manually, without an issue record
            self.write({
                'employee_id': False,
                'assign_date': False,
            })
        return True

    def action_view_asset_issues(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id(
            'hr_asset_management.action_hr_asset_issue')
        action['domain'] = [('equipment_id', '=', self.id)]
        action['context'] = {
            'default_equipment_id': self.id,
            'default_employee_id': self.employee_id.id,
        }
        return action
