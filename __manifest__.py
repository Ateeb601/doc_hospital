# -*- coding: utf‑8 -*-
{
    "name": "Hospital Management System",
    "version": "16.0.1.0.0",          # 🔑  version string zaroor raho
    "author": "Odoo Mates",
    "website": "https://www.odoomates.tech",
    "license": "LGPL-3",              # 🔑  open‑source license
    "summary": "End‑to‑end Hospital management on Odoo 16",
    "category": "Healthcare",
    "application": True,              # 🔑  Apps dashboard par main tile banata hai
    "depends": ["mail", "product", "purchase"],
    "data": [
        # ‑‑ SECURITY (groups/access) pehle
        "security/security.xml",
        "security/ir.model.access.csv",

        # ‑‑ MENUS & VIEWS
        "views/menu.xml",
        "views/time_complexity.xml",
        "views/hospital_patient.xml",
        "views/hospital_doctor.xml",
        "views/hospital_lab.xml",
        "views/hospital_specialization.xml",
        "views/hospital_teacher.xml",
        "views/hospital_account_view.xml",
        "views/my_wizard_views.xml",

        # ‑‑ DEMO / DEFAULT DATA
        "data/sequence.xml",

        # ‑‑ QWEB / REPORTS
        "report/report.xml",               # master report action definitions
        "report/patient_card.xml",
        "report/lab_card.xml",
        "report/doctor_card.xml",
        "report/report_hospital_teacher.xml",
    ],
    "installable": True,
    "auto_install": False,
}
