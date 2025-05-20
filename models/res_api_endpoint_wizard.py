from odoo import models, fields, api

class ResApiEndpointWizard(models.TransientModel):
    _name = 'res.api.endpoint.wizard'
    _description = 'Create Dynamic API Endpoint'

    api_key_id = fields.Many2one(
        'res.api.key', string="API Key",
        required=True, readonly=True,
        default=lambda self: self.env.context.get('active_id')
    )
    model_id = fields.Many2one(
        'ir.model', string="Model",
        required=True,
    )
    url_path = fields.Char(
        string="URL Path",
        required=True,
        help="Will be exposed at /api/<url_path>"
    )
    field_ids = fields.Many2many(
        'ir.model.fields', string="Fields",
        domain="[('model_id','=',model_id)]"
    )
    allowed_model_ids_domain = fields.Many2many(
        'ir.model', compute='_compute_allowed_model_ids_domain', string="Allowed Models (Domain Helper)"
    )

    @api.depends('api_key_id')
    def _compute_allowed_model_ids_domain(self):
        for rec in self:
            rec.allowed_model_ids_domain = rec.api_key_id.allowed_model_ids.ids if rec.api_key_id else []

    @api.onchange('api_key_id')
    def _onchange_api_key_id(self):
        if self.api_key_id and self.api_key_id.allowed_model_ids:
            allowed_ids = self.api_key_id.allowed_model_ids.ids
            return {'domain': {'model_id': [('id', 'in', allowed_ids)]}}
        return {'domain': {'model_id': [('id', '=', False)]}}

    @api.onchange('model_id')
    def _onchange_model_id(self):
        if self.model_id:
            self.url_path = self.model_id.model.replace('.', '_')

    def action_create_endpoint(self):
        self.ensure_one()
        self.env['res.api.endpoint'].sudo().create({
            'name': f"{self.api_key_id.name}: {self.model_id.model}",
            'url_path': self.url_path,
            'model_id': self.model_id.id,
            'field_ids': [(6, 0, self.field_ids.ids)],
            'api_key_ids': [(6, 0, [self.api_key_id.id])],
            'active': True,
        })
        return {'type': 'ir.actions.act_window_close'}
