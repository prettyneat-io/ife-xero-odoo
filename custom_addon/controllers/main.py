from odoo import http
from odoo.http import request
import requests
import base64
import json

class XeroController(http.Controller):

    @http.route('/xero_callback', type='http', auth='user', website=False)
    def xero_callback(self, **kwargs):
        code = kwargs.get('code')
        if not code:
            return "No code provided"
            
        ICPSudo = request.env['ir.config_parameter'].sudo()
        client_id = ICPSudo.get_param('xero.client_id')
        client_secret = ICPSudo.get_param('xero.client_secret')
        redirect_uri = ICPSudo.get_param('xero.redirect_uri')
        
        token_url = "https://identity.xero.com/connect/token"
        auth_str = f"{client_id}:{client_secret}"
        auth_header = base64.b64encode(auth_str.encode()).decode()
        
        headers = {
            "Authorization": f"Basic {auth_header}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri
        }
        
        response = requests.post(token_url, headers=headers, data=data)
        if response.status_code == 200:
            token_data = response.json()
            request.env['xero.token'].sudo().set_token(token_data)
            
            # Now also get the Tenant ID if it's not set
            access_token = token_data.get('access_token')
            connections_url = "https://api.xero.com/connections"
            conn_headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            conn_response = requests.get(connections_url, headers=conn_headers)
            if conn_response.status_code == 200:
                connections = conn_response.json()
                if connections:
                    tenant_id = connections[0].get('tenantId')
                    ICPSudo.set_param('xero.tenant_id', tenant_id)
            
            return "Authentication successful! You can close this window and go back to Odoo settings."
        else:
            return f"Failed to authenticate: {response.text}"
