from odoo import api, fields, models

from datetime import date


class HospitalDoctor(models.Model):
    _name = "hospital.doctor"
    _inherit = "mail.thread"
    _description = "Hospital Doctor"



    name = fields.Char(string="Doctor Name", required=True)
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
        ('others', 'Others')
    ], string="Gender", tracking=True)

    currency_id = fields.Many2one('res.currency', string='Currency')
    retail_price = fields.Monetary('Charges')

    ref = fields.Char(string="Reference Number", default=lambda self: 'New', copy=False)

    # Date of Birth for Age Calculation
    dob = fields.Date(string='Date of Birth')

    # Computed Fields
    age = fields.Integer(string='Age', compute='_compute_age', store=True)
    doctor_type = fields.Char(string='Doctor Type', compute='_compute_doctor_type', store=True)
    full_name = fields.Char(string='Full Name', compute='_compute_full_name', store=True)

    # Hierarchy Fields (optional if you want hierarchy feature)
    parent_id = fields.Many2one('hospital.doctor', string='Supervisor', index=True)
    child_ids = fields.One2many('hospital.doctor', 'parent_id', string='Supervised Doctors')
    parent_path = fields.Char(index=True)

    # ================================
       # SQL Constraints
    # ================================
    _sql_constraints = [
        ('name_uniq', 'UNIQUE (name)', 'Doctor name must be unique.'),
        ('valid_mobile', 'CHECK (char_length(mobile) > 0)', 'Mobile number must not be empty.')
    ]

    # ================================
    # Computed Fields Methods
    # ================================
    @api.depends('name')
    def _compute_doctor_type(self):
        for doctor in self:
            doctor.doctor_type = 'Senior' if doctor.name and len(doctor.name) > 10 else 'Junior'

    @api.depends('dob')
    def _compute_age(self):
        today = date.today()
        for doctor in self:
            if doctor.dob:
                age = today.year - doctor.dob.year - ((today.month, today.day) < (doctor.dob.month, doctor.dob.day))
                doctor.age = age
            else:
                doctor.age = 0

    @api.depends('name')
    def _compute_full_name(self):
        for doctor in self:
            doctor.full_name = f"Dr. {doctor.name}" if doctor.name else ''
