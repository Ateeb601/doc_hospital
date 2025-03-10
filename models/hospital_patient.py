from odoo import api, fields, models
import xlwt  # For generating Excel files
import base64  # For encoding Excel file to attach it in Odoo
from io import BytesIO  # To create file in

class HospitalPatient(models.Model):
    _name = "hospital.patient"
    _inherit = "mail.thread"
    _description = "Patient Records"

    # ================================
    # Fields Declaration
    # ================================
    name = fields.Char(string='Name', required=True, tracking=True)
    age = fields.Integer(string="Age", tracking=True)
    is_child = fields.Boolean(string="Is Child?", tracking=True)
    notes = fields.Text(string="Notes")

    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
        ('others', 'Others')],
        string="Gender", tracking=True
    )

    capitalized_name = fields.Char(string='Capitalized Name', compute='_compute_capitalized_name', store=True)

    ref = fields.Char(string="Reference", default=lambda self: 'New')
    mobile = fields.Char(string='Phone Number', required=True, tracking=True)
    email = fields.Char(string='Email', required=True, tracking=True)
    dob = fields.Date(string='Date of Birth', required=True, tracking=True)
    address = fields.Char(string='Address', required=True, tracking=True)
    amount = fields.Integer(string="Amount", tracking=True)

    # Link to a single lab (hospital.lab model), representing the lab where this patient is assigned.
    lab_id = fields.Many2one('hospital.lab', string="Lab")

    # Many-to-Many relationship linking patients to multiple tags (categories) from res.partner.category.
    # This helps to classify patients with multiple labels like "VIP", "Diabetic", etc.
    # The relation table is 'hospital_patient_tag_rel', linking patient_id with the tag record.
    tag_ids = fields.Many2many('res.partner.category', 'hospital_patient_tag_rel', 'patient_id', string="Tags")

    # One-to-Many relationship linking this patient to multiple pharmacy lines (medications/products).
    # Each pharmacy line records the product, quantity, and price.
    # This allows tracking of all medications prescribed to the patient.
    pharmacy_line_ids = fields.One2many('hospital.patient.pharmacy.line', 'patient_id', string="Pharmacy Lines")

    total_products = fields.Integer(string="Total Products", compute='_compute_pharmacy_totals', store=True)
    total_quantity = fields.Float(string="Total Quantity", compute='_compute_pharmacy_totals', store=True)
    total_price = fields.Float(string="Total Price", compute='_compute_pharmacy_totals', store=True)

    # ================================
    # SQL Constraints
    # ================================
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
        This will automatically convert the name to uppercase.
        """
        for rec in self:
            rec.capitalized_name = rec.name.upper() if rec.name else ''

    @api.depends('pharmacy_line_ids.qty', 'pharmacy_line_ids.price_unit')
    def _compute_pharmacy_totals(self):
        """
        Compute total products, total quantity, and total price for all pharmacy lines.
        This ensures the totals are always up-to-date whenever a pharmacy line changes.
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
        Automatically mark the patient as a child if their age is 10 or below.
        This is triggered when the 'age' field is changed.
        """
        self.is_child = self.age <= 10

    # ================================
    # Override Create Method
    # ================================
    @api.model
    def create(self, vals):
        """
        Override the create method to automatically set the 'ref' field using a sequence.
        This ensures every patient has a unique reference number.
        """
        vals['ref'] = self.env['ir.sequence'].next_by_code('hospital.patient') or 'New'
        return super(HospitalPatient, self).create(vals)

    # ================================
    # Pharmacy Line Totals Helper
    # ================================
    def _get_pharmacy_totals(self):
        """
        Calculate total product count, total quantity, and total price for all pharmacy lines.
        This is used both for computed fields and for generating the Excel report.
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
        Generates an Excel report for the patient including their basic information
        and all associated pharmacy line data (products, quantities, prices).
        Also creates an attachment record in Odoo and triggers the file download.
        """
        self.ensure_one()

        # Create Excel workbook and sheet
        workbook = xlwt.Workbook(encoding='utf-8')
        sheet = workbook.add_sheet('Patient Data')

        # Define styles for header and data cells
        blue_style = xlwt.easyxf('pattern: pattern solid, fore_colour light_blue; font: bold on; align: horiz center;')
        yellow_style = xlwt.easyxf('pattern: pattern solid, fore_colour light_yellow; font: bold on; align: horiz center;')
        center_style = xlwt.easyxf('align: horiz center;')

        # Header for basic patient information
        headers = ['Name', 'Reference', 'Gender', 'Date of Birth', 'Age', 'Phone', 'Email', 'Lab', 'Tags']
        for col, header in enumerate(headers):
            sheet.write(0, col, header, blue_style)

        # Patient data row
        tags = ', '.join(self.tag_ids.mapped('name'))
        data = [
            self.name or '',
            self.ref or '',
            self.gender or '',
            self.dob.strftime('%d-%m-%Y') if self.dob else '',
            self.age or '',
            self.mobile or '',
            self.email or '',
            self.lab_id.name if self.lab_id else '',
            tags
        ]
        for col, value in enumerate(data):
            sheet.write(1, col, value, center_style)

        # Header for pharmacy lines
        sheet.write(3, 0, 'Pharmacy Lines:', center_style)

        pharmacy_headers = ['Product', 'Quantity', 'Price Unit']
        for col, header in enumerate(pharmacy_headers):
            sheet.write(4, col, header, yellow_style)

        # Populate pharmacy line data
        row = 5
        for line in self.pharmacy_line_ids:
            sheet.write(row, 0, line.product_id.name or '', center_style)
            sheet.write(row, 1, line.qty or 0, center_style)
            sheet.write(row, 2, line.price_unit or 0, center_style)
            row += 1

        # Total row
        totals = self._get_pharmacy_totals()
        sheet.write(row, 0, 'Total', blue_style)
        sheet.write(row, 1, totals['total_quantity'], center_style)
        sheet.write(row, 2, totals['total_price'], center_style)

        # Save workbook to memory buffer
        buffer = BytesIO()
        workbook.save(buffer)
        buffer.seek(0)

        # Create attachment in Odoo and trigger download
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

    patient_id = fields.Many2one('hospital.patient', string='Patient', required=True, ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Product', required=True)
    qty = fields.Float(string='Quantity', required=True)
    price_unit = fields.Float(string="Price Unit", required=True)
    tag_id = fields.Many2one('res.partner.category', string='Tag')

    subtotal = fields.Float(string="Subtotal", compute="_compute_subtotal", store=True)

    @api.depends('qty', 'price_unit')
    def _compute_subtotal(self):
        """
        Compute the subtotal for each pharmacy line (quantity * price unit).
        This is automatically updated when quantity or price changes.
        """
        for line in self:
            line.subtotal = line.qty * line.price_unit
