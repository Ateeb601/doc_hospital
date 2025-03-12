from odoo import models, fields


class HospitalSpecialization(models.Model):
    _name = "hospital.specialization"
    _description = "Doctor Specialization"

    name = fields.Char(string="Specialization", required=True, unique=True)
    code = fields.Char(string="Code", required=True, help="Unique code for the specialization")
    description = fields.Text(string="Description")
    active = fields.Boolean(string="Active", default=True)
