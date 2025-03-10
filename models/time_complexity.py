from odoo import models, fields, api


class TimeComplexity(models.Model):
    _name = 'time.complexity'
    _description = 'Time Complexity Calculation'

    name = fields.Char(string="Order Name", required=True)
    num_orders = fields.Integer(string="Number of Orders", required=True, default=0)

    # This is the processing time per order, with a default value of 2 seconds.
    processing_time_per_order = fields.Integer(
        string="Processing Time per Order (Seconds)",
        default=2,  # Default value 2 seconds
        required=True
    )

    time_unit = fields.Selection([
        ('seconds', 'Seconds'),
        ('minutes', 'Minutes'),
        ('hours', 'Hours')
    ], string="Time Unit", default='seconds')

    estimated_time = fields.Char(string="Estimated Time", compute="_compute_estimated_time", store=True)

    # Using compute means this field will not be manually input; it will be automatically calculated based on other fields.

    @api.depends('num_orders', 'processing_time_per_order', 'time_unit')
    def _compute_estimated_time(self):
        for record in self:
            # Ensure values are valid before calculation
            num_orders = record.num_orders or 0
            processing_time = record.processing_time_per_order or 2  # Defaulting to 2 seconds if None

            time_in_seconds = num_orders * processing_time

            # Convert based on time unit
            if record.time_unit == 'minutes':
                estimated_time = f"{time_in_seconds / 60:.2f} minutes"
            elif record.time_unit == 'hours':
                estimated_time = f"{time_in_seconds / 3600:.2f} hours"
            else:
                estimated_time = f"{time_in_seconds} seconds"

            record.estimated_time = estimated_time
