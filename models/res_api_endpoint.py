from odoo import models, fields

class ApiEndpoint(models.Model):
    _name = 'res.api.endpoint'
    _description = 'Dynamic API Endpoint'

    name = fields.Char(required=True)
    url_path = fields.Char(required=True, help="Path after /api/, e.g., sales_data")
    model_id = fields.Many2one('ir.model', required=True, string="Model")
    field_ids = fields.Many2many('ir.model.fields', string="Fields", domain="[('model_id', '=', model_id)]")
    api_key_ids = fields.Many2many('res.api.key', string="Allowed API Keys")
    active = fields.Boolean(default=True)