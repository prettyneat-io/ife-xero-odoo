import os
import json
import base64
import threading
import time
from flask import Flask, request, redirect, url_for
from xero_python.api_client import ApiClient, Configuration
from xero_python.api_client.oauth2 import OAuth2Token
from xero_python.accounting import AccountingApi, Contact, Contacts, Invoice, Invoices, LineItem, Attachment
from xero_python.identity import IdentityApi
from dotenv import load_dotenv
import requests

load_dotenv()

# Configuration
CLIENT_ID = os.getenv("XERO_CLIENT_ID")
CLIENT_SECRET = os.getenv("XERO_CLIENT_SECRET")
REDIRECT_URI = os.getenv("XERO_REDIRECT_URI", "https://localhost:5000/callback")
SCOPES = os.getenv("XERO_SCOPES", "offline_access openid profile email accounting.transactions accounting.contacts accounting.settings accounting.attachments").split()

TOKEN_FILE = "token.json"

app = Flask(__name__)

def get_xero_config():
    return Configuration(
        debug=False,
        oauth2_token=OAuth2Token(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET
        )
    )

api_client = ApiClient(get_xero_config())

@api_client.oauth2_token_getter
def obtain_xero_oauth2_token():
    return load_token()

@api_client.oauth2_token_saver
def store_xero_oauth2_token(token):
    with open(TOKEN_FILE, "w") as f:
        json.dump(token, f)

@app.route("/")
def login():
    state = "12345" # In production, use a random string and verify it
    params = {
        "response_type": "code",
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": " ".join(SCOPES),
        "state": state
    }
    authorization_url = f"https://login.xero.com/identity/connect/authorize?{requests.compat.urlencode(params)}"
    return redirect(authorization_url)

@app.route("/callback")
def callback():
    code = request.args.get("code")
    
    # Exchange code for token
    token_url = "https://identity.xero.com/connect/token"
    auth_str = f"{CLIENT_ID}:{CLIENT_SECRET}"
    auth_header = base64.b64encode(auth_str.encode()).decode()
    
    headers = {
        "Authorization": f"Basic {auth_header}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI
    }
    
    response = requests.post(token_url, headers=headers, data=data)
    token = response.json()
    
    store_xero_oauth2_token(token)
    
    def shutdown():
        time.sleep(1)
        print("\nAuthentication received. Continuing script...")
        # Since we are running in the same process, we can't just os._exit(0) 
        # because it would kill the main script too if not handled carefully.
        # But for this PoC, main() calls app.run(), so we actually want to 
        # stop the flask loop. Werkzeug doesn't have a great clean shutdown 
        # in recent versions, so we'll use a slightly different approach 
        # in main().
        
    threading.Thread(target=shutdown).start()
    
    return "Authentication successful! You can now close this tab. The script will continue in the terminal."

def load_token():
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "r") as f:
            return json.load(f)
    return None

def main():
    token = load_token()
    
    if not token:
        print("Starting authentication server...")
        print(f"Please visit https://localhost:5000 to authenticate.")
        
        # We run flask in a thread so main can wait for the token file
        server_thread = threading.Thread(target=lambda: app.run(port=5000, ssl_context='adhoc', debug=False, use_reloader=False))
        server_thread.daemon = True
        server_thread.start()
        
        while not token:
            time.sleep(1)
            token = load_token()
        
        print("Token obtained.")

    if not token:
        print("Failed to obtain token.")
        return

    # Set token in api_client
    api_client.set_oauth2_token(token)

    # In 9.x, the SDK handles token refresh automatically during API calls 
    # if the @api_client.oauth2_token_getter and @api_client.oauth2_token_saver 
    # decorators are used. 

    # Get Tenant ID
    identity_api = IdentityApi(api_client)
    connections = identity_api.get_connections()
    if not connections:
        print("No Xero connections found.")
        return
    
    # We'll use the first connection
    xero_tenant_id = connections[0].tenant_id
    print(f"Connected to Xero Tenant: {connections[0].tenant_name}")

    accounting_api = AccountingApi(api_client)

    # 1. Create Demo Contact
    print("Creating Demo Contact...")
    # Use a unique name to avoid "Contact name already assigned" error
    unique_suffix = int(time.time())
    contact_name = f"Demo Supplier {unique_suffix}"
    contact = Contact(
        name=contact_name,
        email_address=f"supplier_{unique_suffix}@demo.com",
        is_supplier=True
    )
    contacts = Contacts(contacts=[contact])
    created_contacts = accounting_api.create_contacts(xero_tenant_id, contacts)
    contact_id = created_contacts.contacts[0].contact_id
    print(f"Contact created: {contact_id}")

    # 2. Create Bill (ACCPAY)
    print("Creating Bill...")
    line_item = LineItem(
        description="Demo Consultation Services",
        quantity=1.0,
        unit_amount=100.0,
        account_code="429" # General Expenses
    )
    invoice = Invoice(
        type="ACCPAY",
        contact=Contact(contact_id=contact_id),
        line_items=[line_item],
        status="DRAFT"
    )
    invoices = Invoices(invoices=[invoice])
    created_invoices = accounting_api.create_invoices(xero_tenant_id, invoices)
    invoice_id = created_invoices.invoices[0].invoice_id
    print(f"Bill created: {invoice_id}")

    # 3. Add Multiple Attachments
    print("Uploading Attachments...")
    test_files_dir = "test_files"

    if os.path.exists(test_files_dir) and os.path.isdir(test_files_dir):
        attachment_files = [f for f in os.listdir(test_files_dir) if os.path.isfile(os.path.join(test_files_dir, f))]

        if not attachment_files:
            print(f"Warning: No files found in {test_files_dir} directory.")
        else:
            print(f"Found {len(attachment_files)} file(s) to upload: {', '.join(attachment_files)}")

            for filename in attachment_files:
                attachment_path = os.path.join(test_files_dir, filename)
                try:
                    with open(attachment_path, "rb") as f:
                        file_data = f.read()
                        accounting_api.create_invoice_attachment_by_file_name(
                            xero_tenant_id,
                            invoice_id,
                            filename,
                            file_data
                        )
                    print(f"  ✓ Uploaded: {filename}")
                except Exception as e:
                    print(f"  ✗ Failed to upload {filename}: {str(e)}")
    else:
        print(f"Warning: {test_files_dir} directory not found.")

if __name__ == "__main__":
    main()
