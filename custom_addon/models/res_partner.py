from odoo import models, fields, api, _
from odoo.exceptions import UserError
import requests
import json

class ResPartner(models.Model):
    _inherit = 'res.partner'

    xero_contact_id = fields.Char(string="Xero Contact ID", readonly=True)

    def action_sync_to_xero(self):
        self.ensure_one()
        access_token = self.env['xero.token'].get_token()
        if not access_token:
            raise UserError(_("Please authenticate Xero first in settings."))
            
        tenant_id = self.env['ir.config_parameter'].sudo().get_param('xero.tenant_id')
        if not tenant_id:
            raise UserError(_("Xero Tenant ID not found. Please re-authenticate."))

        url = "https://api.xero.com/api.xro/2.0/Contacts"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Xero-tenant-id": tenant_id,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        data = {
            "Contacts": [
                {
                    "Name": self.name,
                    "EmailAddress": self.email or "",
                    "IsSupplier": True
                }
            ]
        }
        
        # If we have a xero_contact_id, we should update instead of create? 
        # For POC, let's just create or match by name.
        # Actually Xero API handles "PUT" for create/update.
        
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            result = response.json()
            if result.get('Contacts'):
                self.xero_contact_id = result['Contacts'][0].get('ContactID')
        else:
            raise UserError(_("Failed to sync to Xero: %s") % response.text)
