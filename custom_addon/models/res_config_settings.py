from odoo import models, fields, api
import json
import base64
import requests

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    xero_client_id = fields.Char(string="Xero Client ID", config_parameter='xero.client_id')
    xero_client_secret = fields.Char(string="Xero Client Secret", config_parameter='xero.client_secret')
    xero_redirect_uri = fields.Char(string="Xero Redirect URI", config_parameter='xero.redirect_uri', default="http://localhost:8069/xero_callback")
    
    xero_tenant_id = fields.Char(string="Xero Tenant ID", config_parameter='xero.tenant_id')
    
    def action_xero_authenticate(self):
        self.ensure_one()
        client_id = self.xero_client_id
        redirect_uri = self.xero_redirect_uri
        scopes = "offline_access openid profile email accounting.transactions accounting.contacts accounting.settings accounting.attachments"
        
        auth_url = "https://login.xero.com/identity/connect/authorize"
        params = {
            "response_type": "code",
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "scope": scopes,
            "state": "odoo_xero_integration"
        }
        
        target_url = f"{auth_url}?{requests.compat.urlencode(params)}"
        return {
            'type': 'ir.actions.act_url',
            'url': target_url,
            'target': 'new',
        }
