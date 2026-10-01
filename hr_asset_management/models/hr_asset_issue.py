from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class HrAssetIssue(models.Model):
    _name = 'hr.asset.issue'
    _description = 'Asset Issue'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'issue_date desc, id desc'

    name = fields.Char(
        string='Reference',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New'),
    )
    equipment_id = fields.Many2one(
        'maintenance.equipment',
        string='Asset',
        required=True,
        index=True,
        tracking=True,
        ondelete='cascade',
    )
    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee',
        required=True,
        index=True,
        tracking=True,
    )
    department_id = fields.Many2one(
        'hr.department',
        string='Department',
        related='employee_id.department_id',
        store=True,
    )
    company_id = fields.Many2one(
        'res.company',
        related='equipment_id.company_id',
        store=True,
    )
    issue_date = fields.Date(
        required=True,
        tracking=True,
        default=fields.Date.context_today,
    )
    return_date = fields.Date(
        tracking=True,
    )
    state = fields.Selection(
        selection=[
            ('issued', 'Issued'),
            ('returned', 'Returned'),
        ],
        string='Status',
        compute='_compute_state',
        store=True,
    )
    days_issued = fields.Integer(
        compute='_compute_days_issued',
    )
    user_id = fields.Many2one(
        'res.users',
        string='Issued By',
        tracking=True,
        default=lambda self: self.env.user,
    )
    note = fields.Text(string='Notes')

    @api.depends('return_date')
    def _compute_state(self):
        for issue in self:
            issue.state = 'returned' if issue.return_date else 'issued'

    @api.depends('issue_date', 'return_date')
    def _compute_days_issued(self):
        today = fields.Date.context_today(self)
        for issue in self:
            end_date = issue.return_date or today
            if issue.issue_date:
                issue.days_issued = (end_date - issue.issue_date).days
            else:
                issue.days_issued = 0

    @api.constrains('equipment_id', 'return_date')
    def _check_open_issue(self):
        for issue in self.filtered(lambda rec: not rec.return_date):
            duplicate = self.search([
                ('id', '!=', issue.id),
                ('equipment_id', '=', issue.equipment_id.id),
                ('return_date', '=', False),
            ], limit=1)
            if duplicate:
                raise ValidationError(_(
                    'Asset "%(asset)s" is already issued to %(employee)s. '
                    'It cannot be issued again until it is returned.',
                    asset=issue.equipment_id.display_name,
                    employee=duplicate.employee_id.name,
                ))

    @api.constrains('issue_date', 'return_date')
    def _check_dates(self):
        for issue in self:
            if (issue.issue_date and issue.return_date
                    and issue.return_date < issue.issue_date):
                raise ValidationError(_(
                    'Return date cannot be earlier than the issue date.'))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = (
                    self.env['ir.sequence'].next_by_code('hr.asset.issue')
                    or _('New'))
        issues = super().create(vals_list)
        for issue in issues:
            issue._sync_equipment()
        return issues

    def write(self, vals):
        res = super().write(vals)
        if {'return_date', 'employee_id', 'equipment_id'} & set(vals):
            for issue in self:
                issue._sync_equipment()
        return res

    def _sync_equipment(self):
        self.ensure_one()
        equipment = self.equipment_id
        if not self.return_date:
            equipment.write({
                'equipment_assign_to': 'employee',
                'employee_id': self.employee_id.id,
                'department_id': False,
            })
            # set assign_date after write, because changing
            # equipment_assign_to triggers a compute that resets it to today
            equipment.assign_date = self.issue_date
        elif not equipment.asset_issue_ids.filtered(
                lambda rec: not rec.return_date and rec.id != self.id):
            equipment.write({
                'employee_id': False,
                'assign_date': False,
            })

    def action_return(self):
        for issue in self.filtered(lambda rec: not rec.return_date):
            issue.return_date = fields.Date.context_today(self)
            issue.equipment_id.message_post(
                body=_('Asset returned by %s', issue.employee_id.name))
        return True
