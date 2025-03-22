from odoo import api, fields, models

class HospitalTeacher(models.Model):
    _name = "hospital.teacher"
    _inherit = ['mail.thread', 'mail.activity.mixin']  # Enable chatter

    name = fields.Char(string="Teacher Name", required=True)
    ref = fields.Char(string="Reference", default=lambda self: 'New')

    @api.model
    def create(self, vals):
        if not vals.get('ref') or vals['ref'] == 'New':
            vals['ref'] = self.env['ir.sequence'].next_by_code('hospital.teacher') or 'New'
        return super().create(vals)

    def action_open_wizard(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'My Wizard',
            'res_model': 'my.wizard',
            'view_mode': 'form',
            'view_id': self.env.ref('doc_hospital.view_my_wizard_form').id,
            'target': 'new',
        }
