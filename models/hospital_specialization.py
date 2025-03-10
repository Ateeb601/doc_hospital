from odoo import models, fields

class HospitalDoctorSpecialized(models.Model):
    _inherit = "hospital.doctor"

    specialization = fields.Many2one('hospital.specialization', string="Specialization")

class HospitalSpecialization(models.Model):
    _name = "hospital.specialization"
    _description = "Doctor Specialization"

    name = fields.Char(string="Specialization", required=True, unique=True)
    description = fields.Text(string="Description")
