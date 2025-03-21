from odoo import api, fields, models
import xlwt  # Library for generating Excel files
import base64  # For encoding Excel files to attach in Odoo
from io import BytesIO  # To create file in memory
from datetime import date  # To handle date calculations
import re  # <-- Import regex module

class HospitalPatient(models.Model):
    _name = "hospital.patient"  # Defines the model name
    _inherit = "mail.thread"  # Enables tracking messages in the chatter
    _description = "Patient Records"  # Model description

    # ========== Patient Basic Information ==========
    name = fields.Char(string='Name', required=True, tracking=True)  # Patient name (tracked)
    age = fields.Integer(string="Age", compute='_compute_age', store=True, tracking=True)  # Auto-calculated age
    is_child = fields.Boolean(string="Is Child?", compute='_compute_is_child', store=True,
                              tracking=True)  # Auto-check if the patient is a child
    notes = fields.Text(string="Notes")  # Free-text notes

    # Gender selection field with predefined choices
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
        ('others', 'Others')],
        string="Gender", tracking=True
    )

    capitalized_name = fields.Char(string='Capitalized Name', compute='_compute_capitalized_name',
                                   store=True)  # Auto-capitalized name
    ref = fields.Char(string="Reference", default='New', readonly=True)  # Auto-generated patient reference ID
    mobile = fields.Char(string='Phone Number', required=True, tracking=True)  # Mobile number (tracked)
    email = fields.Char(string='Email', required=True, tracking=True)  # Email address (tracked)
    dob = fields.Date(string='Date of Birth')  # Patient's date of birth
    address = fields.Char(string='Address', required=True, tracking=True)  # Address (tracked)
    amount = fields.Integer(string="Amount", tracking=True)  # Amount field (not clear in usage)

    # ========== Lab Information ==========
    lab_id = fields.Many2one('hospital.lab', string="Lab")  # Links the patient to a lab
    test_name1 = fields.Char(string="Test Name", related='lab_id.test_name',
                             store=True)  # Retrieves test name from lab record

    # ========== Tags & Pharmacy Details ==========
    tag_ids = fields.Many2many('res.partner.category', string="Tags")  # Tags for categorization
    pharmacy_line_ids = fields.One2many('hospital.patient.pharmacy.line', 'patient_id',
                                        string="Pharmacy Lines")  # Links pharmacy purchases

    # Computed pharmacy totals
    total_products = fields.Integer(string="Total Products", compute='_compute_pharmacy_totals',
                                    store=True)  # Count of pharmacy products
    total_quantity = fields.Float(string="Total Quantity", compute='_compute_pharmacy_totals',
                                  store=True)  # Total quantity of medicines purchased
    total_price = fields.Float(string="Total Price", compute='_compute_pharmacy_totals',
                               store=True)  # Total price of purchased medicines

    # ========== Constraints ==========
    _sql_constraints = [
        ('name_uniq', 'UNIQUE (name)', 'Patient name must be unique.'),  # Ensures patient name is unique
        ('valid_mobile', "CHECK (char_length(mobile) > 0)", 'Mobile number must not be empty.')
        # Ensures mobile number is not empty
    ]
    # Adding the CNIC field
    cnic = fields.Char(string="CNIC", required=True, tracking=True)

    # SQL constraint to ensure CNIC is unique
    _sql_constraints = [
        ('cnic_uniq', 'UNIQUE (cnic)', 'CNIC must be unique.'),
    ]

    @api.constrains('cnic')
    def _check_cnic_format(self):
        """Ensure CNIC is exactly 13 digits and contains only numbers."""
        for record in self:
            if not record.cnic or not re.fullmatch(r'\d{13}', record.cnic):
                raise ValueError("CNIC must be exactly 13 digits long and contain only numbers.")

    @api.model
    def search_patient_by_cnic(self, cnic_number):
        """Search for a patient by CNIC number."""
        patient = self.search([('cnic', '=', cnic_number)], limit=1)
        if patient:
            return {
                'name': patient.name,
                'age': patient.age,
                'gender': patient.gender,
                'mobile': patient.mobile,
                'email': patient.email,
                'address': patient.address,
                'lab': patient.lab_id.name if patient.lab_id else 'N/A',
                'total_products': patient.total_products,
                'total_price': patient.total_price,
            }
        return {'error': 'No patient found with this CNIC'}
    # ========== Compute Functions ==========
    @api.depends('dob')
    def _compute_age(self):
        """Calculates the patient's age based on their date of birth."""
        today = date.today()
        for patient in self:
            if patient.dob:
                patient.age = today.year - patient.dob.year - (
                        (today.month, today.day) < (patient.dob.month, patient.dob.day))
            else:
                patient.age = 0  # Defaults to 0 if DOB is not set

    @api.depends('age')
    def _compute_is_child(self):
        """Checks if the patient is a child (age <= 10)."""
        for patient in self:
            patient.is_child = patient.age <= 10

    @api.depends('name')
    def _compute_capitalized_name(self):
        """Capitalizes the patient's name."""
        for rec in self:
            rec.capitalized_name = rec.name.upper() if rec.name else ''

    @api.depends('pharmacy_line_ids.qty', 'pharmacy_line_ids.price_unit')
    def _compute_pharmacy_totals(self):
        """Calculates total number of products, quantity, and price from pharmacy lines."""
        for rec in self:
            rec.total_products = len(rec.pharmacy_line_ids)
            rec.total_quantity = sum(rec.pharmacy_line_ids.mapped('qty'))
            rec.total_price = sum(line.qty * line.price_unit for line in rec.pharmacy_line_ids)

    @api.model
    def create(self, vals):
        """Generates a unique reference for new patient records."""
        vals['ref'] = self.env['ir.sequence'].next_by_code('hospital.patient') or 'New'
        return super(HospitalPatient, self).create(vals)

    # ========== Excel Report Generation ==========
    def print_excel(self):
        """Generates an Excel file containing patient details and attaches it to the record."""
        self.ensure_one()  # Ensures only one record is processed

        # Create a new Excel workbook and sheet
        workbook = xlwt.Workbook(encoding='utf-8')
        sheet = workbook.add_sheet('Patient Data')

        # Define column headers
        headers = ['Name', 'Reference', 'Gender', 'Date of Birth', 'Age', 'Phone', 'Email', 'Lab', 'Tags']

        # Write headers to the first row
        for col, header in enumerate(headers):
            sheet.write(0, col, header)

        # Gather patient data for writing
        data = [
            self.name, self.ref, self.gender, self.dob.strftime('%d-%m-%Y') if self.dob else '',
            self.age, self.mobile, self.email, self.lab_id.name if self.lab_id else '',
            ', '.join(self.tag_ids.mapped('name'))
        ]

        # Write patient data to the second row
        for col, value in enumerate(data):
            sheet.write(1, col, value)

        # Save workbook in memory buffer
        buffer = BytesIO()
        workbook.save(buffer)
        buffer.seek(0)

        # Create an attachment in Odoo
        attachment = self.env['ir.attachment'].create({
            'name': f'Patient_{self.name}.xls',
            'type': 'binary',
            'datas': base64.b64encode(buffer.getvalue()),
            'res_model': 'hospital.patient',
            'res_id': self.id,
        })

        # Return an action to allow the user to download the file
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }


# ========== Pharmacy Line Model ==========
class HospitalPatientPharmacyLine(models.Model):
    _name = 'hospital.patient.pharmacy.line'  # Defines the model name
    _description = 'Patient Pharmacy Line'  # Model description

    patient_id = fields.Many2one('hospital.patient', string='Patient', required=True,
                                 ondelete='cascade')  # Links the line to a patient
    product_id = fields.Many2one('product.product', string='Product', required=True)  # Medicine/Product purchased
    qty = fields.Float(string='Quantity', required=True, digits=(16, 4))  # Quantity of the product
    price_unit = fields.Float(string="Price Unit", required=True, digits=(16, 4))  # Unit price of the product
    subtotal = fields.Float(string="Subtotal", compute="_compute_subtotal", store=True,
                            digits=(16, 4))  # Auto-computed total price

    tag_id = fields.Many2one('res.partner.category', string="Tag")  # Category tag for pharmacy line

    @api.depends('qty', 'price_unit')
    def _compute_subtotal(self):
        """Computes subtotal for each pharmacy line (quantity * price)."""
        for line in self:
            line.subtotal = line.qty * line.price_unit
