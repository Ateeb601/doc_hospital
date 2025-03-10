

from odoo import api, fields, models
import xlwt  # For generating Excel files
import base64  # For encoding Excel file to attach it in Odoo
from io import BytesIO  # To create file in memory
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

    mobile = fields.Char(string="Mobile")
    email = fields.Char(string='Email', required=True, tracking=True)

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

    # ================================
    # Print Excel
    # ================================

    def print_excel(self):
        self.ensure_one()

        workbook = xlwt.Workbook(encoding='utf-8')
        sheet = workbook.add_sheet('Doctor Data')

        # Define a style for the header with a custom background color
        header_style = xlwt.easyxf('pattern: pattern solid, fore_colour green; font: bold on; align: horiz center;')

        # Define a center-aligned style for normal cells
        center_style = xlwt.easyxf('align: horiz center;')

        headers = ['Name', 'Full Name', 'Gender', 'Mobile', 'Email', 'Specialization', 'Age', 'Doctor Type',
                   'Supervisor', 'Supervised Doctors', 'Currency', 'Charges']

        # Apply the header style with color
        for col, header in enumerate(headers):
            sheet.write(0, col, header, header_style)  # Apply yellow header background

        data = [
            self.name or '',
            self.full_name or '',
            self.gender or '',
            self.mobile or '',
            self.email or '',
            self.specialization.name if self.specialization else '',  # Fixing Many2one field
            str(self.age) or '',
            self.doctor_type or '',
            self.parent_id.name if self.parent_id else '',  # Fixing Many2one field
            ", ".join(self.child_ids.mapped('name')) if self.child_ids else '',  # Fixing One2many field
            self.currency_id.name if self.currency_id else '',  # Fixing Many2one field
            str(self.retail_price) if self.retail_price else '0.00',  # Ensure retail_price is string
        ]

        # Write data with center alignment
        for col, value in enumerate(data):
            sheet.write(1, col, value, center_style)

        buffer = BytesIO()
        workbook.save(buffer)
        buffer.seek(0)

        attachment = self.env['ir.attachment'].create({
            'name': f'Doctor_{self.name}.xls',
            'type': 'binary',
            'datas': base64.b64encode(buffer.getvalue()),
            'res_model': 'hospital.doctor',
            'res_id': self.id,
        })
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }

    # ================================
    # Override Create
    # ================================
    @api.model
    def create(self, vals):
        if not vals.get('ref'):
            vals['ref'] = self.env['ir.sequence'].next_by_code('hospital.doctor') or 'New'
        return super(HospitalDoctor, self).create(vals)
