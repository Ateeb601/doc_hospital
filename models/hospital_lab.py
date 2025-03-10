from odoo import api, fields, models


class HospitalLab(models.Model):
    _name = "hospital.lab"
    _inherit = "mail.thread"
    _description = "Hospital Lab"
    _rec_name = 'name'

    # Fields
    test_name = fields.Char(string="Test Name")
    name = fields.Char(string="Lab Name", required=True)
    patient_name = fields.Char(string="Patient Name", required=True)
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
        ('others', 'Others')
    ], string="Gender", tracking=True)

    mobile = fields.Char(string="Mobile")
    email = fields.Char(string='Email', required=True, tracking=True)
    dob = fields.Date(string='Date of Birth', required=True, tracking=True)
    address = fields.Char(string='Address', required=True, tracking=True)

    ref = fields.Char(string="Reference Number", default=lambda self: 'New', copy=False)


    capitalized_name = fields.Char(compute="_compute_capitalized_name", store=True)

    # Override the create method to set 'ref' field using a sequence
    @api.model
    def create(self, vals):
        """
        Override the create method to automatically set the 'ref' field using a sequence.
        This ensures every patient has a unique reference number.
        """
        if not vals.get('ref'):
            vals['ref'] = self.env['ir.sequence'].next_by_code('hospital.lab') or 'New'
        return super(HospitalLab, self).create(vals)

    # Compute the capitalized name for the patient
    @api.depends('patient_name')
    def _compute_capitalized_name(self):
        for rec in self:
            if rec.patient_name:
                rec.capitalized_name = rec.patient_name.upper()
            else:
                rec.capitalized_name = ''

    # Custom name_get method to display lab name and patient name
    def name_get(self):
        res = []
        for rec in self:
            res.append((rec.id, f'{rec.name} - {rec.patient_name}'))
        return res
