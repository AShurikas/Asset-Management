{
    'name': 'HR Asset Management',

    'summary': 'Issue and track company assets assigned to employees',

    'category': 'Human Resources',
    'author': 'Oleksandr Nechyporenko',
    'license': 'Other proprietary',

    'version': '18.0.0.1.0',

    'depends': [
        'hr',
        'hr_maintenance',
        'mail',
    ],

    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/hr_asset_issue_views.xml',
        'views/maintenance_equipment_views.xml',
        'views/hr_employee_views.xml',
        'wizard/hr_asset_issue_wizard_views.xml',
        'report/hr_asset_issue_report.xml',
        'views/hr_asset_management_menus.xml',
    ],

    'installable': True,
    'auto_install': False,
    'application': False,
}
