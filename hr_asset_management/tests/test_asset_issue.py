from datetime import timedelta

from odoo import fields
from odoo.exceptions import UserError, ValidationError
from odoo.tests import Form, TransactionCase


class TestHrAssetIssue(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Equipment = cls.env['maintenance.equipment']
        cls.Issue = cls.env['hr.asset.issue']
        cls.IssueWizard = cls.env['hr.asset.issue.wizard']

        cls.employee_1 = cls.env['hr.employee'].create({'name': 'John Doe'})
        cls.employee_2 = cls.env['hr.employee'].create({'name': 'Jane Smith'})
        cls.category = cls.env['maintenance.equipment.category'].create(
            {'name': 'Computers'})
        cls.equipment = cls.Equipment.create({
            'name': 'Test Laptop',
            'category_id': cls.category.id,
            'serial_no': 'SN-001',
            'model': 'Latitude 5540',
        })

    def _issue_via_wizard(self, equipment, employee, issue_date=None):
        wizard_form = Form(
            self.IssueWizard.with_context(default_equipment_id=equipment.id))
        wizard_form.employee_id = employee
        if issue_date:
            wizard_form.issue_date = issue_date
        wizard = wizard_form.save()
        wizard.action_confirm()
        return equipment.current_issue_id

    def test_01_issue_asset_via_wizard(self):
        issue = self._issue_via_wizard(self.equipment, self.employee_1)
        self.assertTrue(issue)
        self.assertEqual(issue.equipment_id, self.equipment)
        self.assertEqual(issue.employee_id, self.employee_1)
        self.assertEqual(issue.issue_date, fields.Date.context_today(issue))
        self.assertFalse(issue.return_date)
        self.assertEqual(issue.state, 'issued')
        self.assertNotEqual(issue.name, 'New')
        # asset must be assigned to the employee
        self.assertEqual(self.equipment.employee_id, self.employee_1)
        self.assertEqual(self.equipment.equipment_assign_to, 'employee')
        self.assertEqual(self.equipment.assign_date, issue.issue_date)

    def test_02_double_issue_same_asset(self):
        self._issue_via_wizard(self.equipment, self.employee_1)
        # direct creation of a second open issue must fail
        with self.assertRaises(ValidationError):
            self.Issue.create({
                'equipment_id': self.equipment.id,
                'employee_id': self.employee_2.id,
            })
        # wizard must refuse as well
        with self.assertRaises(UserError):
            self.equipment.action_issue()

    def test_03_return_asset(self):
        issue = self._issue_via_wizard(self.equipment, self.employee_1)
        self.equipment.action_return_asset()
        self.assertTrue(issue.return_date)
        self.assertEqual(issue.state, 'returned')
        # asset must be back in stock
        self.assertFalse(self.equipment.employee_id)
        self.assertFalse(self.equipment.current_issue_id)
        # the asset can be issued again after return
        issue2 = self._issue_via_wizard(self.equipment, self.employee_2)
        self.assertTrue(issue2)
        self.assertEqual(self.equipment.employee_id, self.employee_2)

    def test_04_days_issued_computation(self):
        issue = self._issue_via_wizard(
            self.equipment, self.employee_1,
            issue_date=fields.Date.context_today(self.equipment)
            - timedelta(days=10))
        self.assertEqual(issue.days_issued, 10)
        self.assertEqual(self.equipment.days_issued, 10)
        issue.return_date = issue.issue_date + timedelta(days=4)
        self.assertEqual(issue.days_issued, 4)

    def test_05_return_date_before_issue_date(self):
        issue = self._issue_via_wizard(self.equipment, self.employee_1)
        with self.assertRaises(ValidationError):
            issue.return_date = issue.issue_date - timedelta(days=1)

    def test_06_employee_asset_count_and_action(self):
        self._issue_via_wizard(self.equipment, self.employee_1)
        self.assertEqual(self.employee_1.asset_issue_count, 1)
        self.assertEqual(self.equipment.asset_issue_count, 1)
        action = self.employee_1.action_view_asset_issues()
        self.assertEqual(
            action['domain'], [('employee_id', '=', self.employee_1.id)])

    def test_07_report_asset_issue_act(self):
        issue = self._issue_via_wizard(self.equipment, self.employee_1)
        report = self.env.ref(
            'hr_asset_management.action_report_asset_issue_act')
        self.assertEqual(report.model, 'hr.asset.issue')
        html = report._render_qweb_html(
            report.report_name, issue.ids)[0]
        self.assertIn(b'Asset Issue Act', html)
        self.assertIn(self.equipment.name.encode(), html)
        self.assertIn(self.employee_1.name.encode(), html)
