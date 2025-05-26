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

    endpoint_ids = fields.One2many(
        comodel_name='res.api.endpoint',
        inverse_name='id',  # Placeholder, see note below
        string='API Endpoints',
        compute='_compute_endpoint_ids',
        store=False,
    )

    # New field: select allowed companies for this API key.
    company_ids = fields.Many2many('res.company', string="Allowed Companies")

    def generate_key(self):
        for rec in self:
            rec.key = secrets.token_hex(20)

    def create(self, vals):
        vals['key'] = secrets.token_hex(20)
        return super().create(vals)

    def _compute_endpoint_ids(self):
        for rec in self:
            rec.endpoint_ids = self.env['res.api.endpoint'].search([('api_key_ids', 'in', rec.id)])