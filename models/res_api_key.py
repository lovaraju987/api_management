from odoo import models, fields
import secrets

class ResApiKey(models.Model):
    _name = 'res.api.key'
    _description = 'API Key'

    name = fields.Char(string="Name", required=True)
    key = fields.Char(string="API Key", readonly=True, copy=False)
    user_id = fields.Many2one('res.users', string="User")
    active = fields.Boolean(default=True)
    expiry_date = fields.Date()
    is_admin = fields.Boolean(string="Admin Access", default=False)

    allowed_model_ids = fields.Many2many(
        'ir.model',
        'res_api_key_ir_model_rel',
        'api_key_id',
        'model_id',
        string='Allowed Models'
    )

    def generate_key(self):
        for rec in self:
            rec.key = secrets.token_hex(20)

    def create(self, vals):
        vals['key'] = secrets.token_hex(20)
        return super().create(vals)