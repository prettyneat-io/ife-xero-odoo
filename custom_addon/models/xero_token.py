from odoo import models, fields, api
import time
import json
import base64
import requests

class XeroToken(models.Model):
    _name = 'xero.token'
    _description = 'Xero Token Storage'

    access_token = fields.Text()
    refresh_token = fields.Text()
    expires_at = fields.Float() # Unix timestamp
    id_token = fields.Text()
    
    @api.model
    def set_token(self, token_data):
        # We store only one token for simplicity in this POC
        existing = self.search([], limit=1)
        vals = {
            'access_token': token_data.get('access_token'),
            'refresh_token': token_data.get('refresh_token'),
            'expires_at': time.time() + token_data.get('expires_in', 0),
            'id_token': token_data.get('id_token'),
        }
        if existing:
            existing.write(vals)
        else:
            self.create(vals)

    @api.model
    def get_token(self):
        token_record = self.search([], limit=1)
        if not token_record:
            return None
            
        if time.time() > token_record.expires_at - 60: # refresh 1 minute before expiry
            return self._refresh_xero_token(token_record)
        
        return token_record.access_token

    def _refresh_xero_token(self, token_record):
        ICPSudo = self.env['ir.config_parameter'].sudo()
        client_id = ICPSudo.get_param('xero.client_id')
        client_secret = ICPSudo.get_param('xero.client_secret')
        
        token_url = "https://identity.xero.com/connect/token"
        auth_str = f"{client_id}:{client_secret}"
        auth_header = base64.b64encode(auth_str.encode()).decode()
        
        headers = {
            "Authorization": f"Basic {auth_header}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {
            "grant_type": "refresh_token",
            "refresh_token": token_record.refresh_token
        }
        
        response = requests.post(token_url, headers=headers, data=data)
        if response.status_code == 200:
            token_data = response.json()
            token_record.write({
                'access_token': token_data.get('access_token'),
                'refresh_token': token_data.get('refresh_token'),
                'expires_at': time.time() + token_data.get('expires_in', 0),
            })
            return token_record.access_token
        else:
            # Handle error
            return None
