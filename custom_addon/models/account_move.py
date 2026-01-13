from odoo import models, fields, api, _
from odoo.exceptions import UserError
import requests
import json
import base64

class AccountMove(models.Model):
    _inherit = 'account.move'

    xero_invoice_id = fields.Char(string="Xero Invoice ID", readonly=True)

    def action_push_bill_to_xero(self):
        self.ensure_one()
        if self.move_type != 'in_invoice':
            raise UserError(_("Only bills can be pushed to Xero in this POC."))
            
        access_token = self.env['xero.token'].get_token()
        if not access_token:
            raise UserError(_("Please authenticate Xero first in settings."))
            
        tenant_id = self.env['ir.config_parameter'].sudo().get_param('xero.tenant_id')
        if not tenant_id:
            raise UserError(_("Xero Tenant ID not found. Please re-authenticate."))

        # Ensure contact exists in Xero
        if not self.partner_id.xero_contact_id:
            self.partner_id.action_sync_to_xero()
            
        url = "https://api.xero.com/api.xro/2.0/Invoices"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Xero-tenant-id": tenant_id,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        line_items = []
        for line in self.invoice_line_ids:
            line_items.append({
                "Description": line.name,
                "Quantity": line.quantity,
                "UnitAmount": line.price_unit,
                "AccountCode": "429" # Hardcoded for POC as in poc_xero.py
            })
            
        data = {
            "Invoices": [
                {
                    "Type": "ACCPAY",
                    "Contact": {
                        "ContactID": self.partner_id.xero_contact_id
                    },
                    "LineItems": line_items,
                    "Status": "DRAFT",
                    "Date": self.invoice_date.isoformat() if self.invoice_date else fields.Date.today().isoformat()
                }
            ]
        }
        
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            result = response.json()
            if result.get('Invoices'):
                self.xero_invoice_id = result['Invoices'][0].get('InvoiceID')
                self.message_post(body=_("Bill successfully pushed to Xero. Invoice ID: %s") % self.xero_invoice_id)
                self._upload_attachments_to_xero()
        else:
            raise UserError(_("Failed to push Bill to Xero: %s") % response.text)

    def _upload_attachments_to_xero(self):
        self.ensure_one()
        if not self.xero_invoice_id:
            return
            
        attachments = self.env['ir.attachment'].search([
            ('res_model', '=', 'account.move'),
            ('res_id', '=', self.id)
        ])
        
        if not attachments:
            return

        access_token = self.env['xero.token'].get_token()
        tenant_id = self.env['ir.config_parameter'].sudo().get_param('xero.tenant_id')
        
        for attachment in attachments:
            url = f"https://api.xero.com/api.xro/2.0/Invoices/{self.xero_invoice_id}/Attachments/{attachment.name}"
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Xero-tenant-id": tenant_id,
                "Content-Type": attachment.mimetype or "application/octet-stream"
            }
            
            file_data = base64.b64decode(attachment.datas)
            response = requests.post(url, headers=headers, data=file_data)
            
            if response.status_code in (200, 201):
                self.message_post(body=_("Attachment '%s' uploaded to Xero.") % attachment.name)
            else:
                # Log error but don't fail the whole process for attachment
                self.message_post(body=_("Failed to upload attachment '%s' to Xero.") % attachment.name)
