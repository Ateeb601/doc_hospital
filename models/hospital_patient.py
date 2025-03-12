from odoo import api, fields, models
import xlwt  # For generating Excel files
import base64  # For encoding Excel file to attach it in Odoo
from io import BytesIO  # To create file in memory


class HospitalPatient(models.Model):
    _name = "hospital.patient"
    _inherit = "mail.thread"
    _description = "Patient Records"

    # ================================
    # Fields Declaration
    # ================================
    name = fields.Char(string='Name', required=True, tracking=True)  # Patient's name
    age = fields.Integer(string="Age", tracking=True)  # Age of the patient
    is_child = fields.Boolean(string="Is Child?", tracking=True)  # Determines if the patient is a child (based on age)
    notes = fields.Text(string="Notes")  # Additional notes

    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
        ('others', 'Others')],
        string="Gender", tracking=True
    )  # Gender selection field

    capitalized_name = fields.Char(string='Capitalized Name', compute='_compute_capitalized_name', store=True)

    ref = fields.Char(string="Reference", default=lambda self: 'New')  # Auto-generated reference
    mobile = fields.Char(string='Phone Number', required=True, tracking=True)
    email = fields.Char(string='Email', required=True, tracking=True)
    dob = fields.Date(string='Date of Birth', required=True, tracking=True)
    address = fields.Char(string='Address', required=True, tracking=True)
    amount = fields.Integer(string="Amount", tracking=True)

    # Relationship fields
    lab_id = fields.Many2one('hospital.lab', string="Lab")  # Link to a lab record
    test_name1 = fields.Char(string="Test Name", related='lab_id.test_name', store=True)

    tag_ids = fields.Many2many('res.partner.category', 'hospital_patient_tag_rel', 'patient_id',
                               string="Tags")  # Tags (categories)
    pharmacy_line_ids = fields.One2many('hospital.patient.pharmacy.line', 'patient_id',
                                        string="Pharmacy Lines")  # Medications

    # Computed fields for totals
    total_products = fields.Integer(string="Total Products", compute='_compute_pharmacy_totals', store=True)
    total_quantity = fields.Float(string="Total Quantity", compute='_compute_pharmacy_totals', store=True)
    total_price = fields.Float(string="Total Price", compute='_compute_pharmacy_totals', store=True)

    # SQL Constraints for data integrity
    _sql_constraints = [
        ('name_uniq', 'UNIQUE (name)', 'Doctor name must be unique.'),
        ('valid_mobile', 'CHECK (char_length(mobile) > 0)', 'Mobile number must not be empty.')
    ]

    # ================================
    # Compute Methods
    # ================================
    @api.depends('name')
    def _compute_capitalized_name(self):
        """
        Compute the capitalized version of the patient's name.
        """
        for rec in self:
            rec.capitalized_name = rec.name.upper() if rec.name else ''

    @api.depends('pharmacy_line_ids.qty', 'pharmacy_line_ids.price_unit')
    def _compute_pharmacy_totals(self):
        """
        Compute total products, total quantity, and total price for pharmacy lines.
        """
        for rec in self:
            totals = rec._get_pharmacy_totals()
            rec.total_products = totals['total_products']
            rec.total_quantity = totals['total_quantity']
            rec.total_price = totals['total_price']

    # ================================
    # Onchange Methods
    # ================================
    @api.onchange('age')
    def _onchange_age(self):
        """
        Automatically set `is_child` if age is 10 or below.
        """
        self.is_child = self.age <= 10

    # ================================
    # Override Create Method
    # ================================
    @api.model
    def create(self, vals):
        """
        Override the create method to auto-generate reference number.
        """
        vals['ref'] = self.env['ir.sequence'].next_by_code('hospital.patient') or 'New'
        return super(HospitalPatient, self).create(vals)

    # ================================
    # Pharmacy Line Totals Helper
    # ================================
    def _get_pharmacy_totals(self):
        """
        Calculate total product count, total quantity, and total price for pharmacy lines.
        """
        self.ensure_one()
        total_quantity = sum(self.pharmacy_line_ids.mapped('qty'))
        total_price = sum(line.qty * line.price_unit for line in self.pharmacy_line_ids)

        return {
            'total_products': len(self.pharmacy_line_ids),
            'total_quantity': total_quantity,
            'total_price': total_price,
        }

    # ================================
    # Excel Export Function
    # ================================
    def print_excel(self):
        """
        Generates an Excel report for the patient including pharmacy line data.
        """
        self.ensure_one()

        # Create Excel workbook and sheet
        workbook = xlwt.Workbook(encoding='utf-8')
        sheet = workbook.add_sheet('Patient Data')

        # Header for patient information
        headers = ['Name', 'Reference', 'Gender', 'Date of Birth', 'Age', 'Phone', 'Email', 'Lab', 'Tags']
        for col, header in enumerate(headers):
            sheet.write(0, col, header)

        # Patient data row
        data = [
            self.name, self.ref, self.gender, self.dob.strftime('%d-%m-%Y') if self.dob else '',
            self.age, self.mobile, self.email, self.lab_id.name if self.lab_id else '',
            ', '.join(self.tag_ids.mapped('name'))
        ]
        for col, value in enumerate(data):
            sheet.write(1, col, value)

        # Create attachment
        buffer = BytesIO()
        workbook.save(buffer)
        buffer.seek(0)

        attachment = self.env['ir.attachment'].create({
            'name': f'Patient_{self.name}.xls',
            'type': 'binary',
            'datas': base64.b64encode(buffer.getvalue()),
            'res_model': 'hospital.patient',
            'res_id': self.id,
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }


class HospitalPatientPharmacyLine(models.Model):
    _name = 'hospital.patient.pharmacy.line'
    _description = 'Patient Pharmacy Line'

    tag_id = fields.Many2one('some.model', string="Tag")  # Placeholder field (fix needed)
    patient_id = fields.Many2one('hospital.patient', string='Patient', required=True, ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Product', required=True)
    qty = fields.Float(string='Quantity', required=True, digits=(16, 4))
    price_unit = fields.Float(string="Price Unit", required=True, digits=(16, 4))
    subtotal = fields.Float(string="Subtotal", compute="_compute_subtotal", store=True, digits=(16, 4))

    @api.depends('qty', 'price_unit')
    def _compute_subtotal(self):
        """
        Compute subtotal for pharmacy line (qty * price_unit).
        """
        for line in self:
            line.subtotal = line.qty * line.price_unit
