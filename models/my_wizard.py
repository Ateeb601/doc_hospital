from odoo import models, fields, api

class MyWizard(models.TransientModel):
    _name = 'my.wizard'
    _description = 'My Wizard'

    report_type = fields.Selection([
        ('pdf', 'PDF Report'),
        ('xlsx', 'Excel Report'),
        ('csv', 'CSV Report'),
    ], string="Report Type", default="pdf", required=True)
    def action_confirm(self):
        active_ids = self.env.context.get('active_ids', [])  # Get selected practice records
        if not active_ids:
            active_ids = self.env['practice'].search([]).ids  # Get all records if none selected

        return self.env.ref('doc_hospital.action_report_practice').report_action(active_ids)

    def action_cancel(self):
        return {'type': 'ir.actions.act_window_close'}
