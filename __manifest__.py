{
    'name': "Hospital Management System",
    'author': 'odoo Mates',
    'website': 'www.odoomates.tech',
    'summary': 'odoo 16 Development',
    'depends': ['mail', 'product', ],
    'data': [
        'security/ir.model.access.csv',
        'views/menu.xml',
        'views/time_complexity.xml',
        'views/hospital_lab.xml',
        'views/hospital_patient.xml',
        'views/hospital_doctor.xml',
        'views/hospital_account_view.xml',
        'data/sequence.xml',

        'report/patient_card.xml',
        'report/lab_card.xml',
        'report/doctor_card.xml',
        'report/report.xml'

    ],
    'installable': True,

}
