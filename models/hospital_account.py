from odoo import api, fields, models

class HospitalAccount(models.TransientModel):
    _name = 'hospital.account'
    _description = 'Hospital Account'

    account_currency = fields.Boolean(
        string='With Currency',
        help='Print Report with the currency column if the currency differs from the company currency.'
    )
    name = fields.Char(string='Name')

    def pre_print_report(self, date):
        """Prepare data before printing the report"""
        data = {'form': {}}  # Define the data dictionary
        data['form'].update({'amount_currency': self.account_currency})  # Fix key name (amount_currency)
        return data
