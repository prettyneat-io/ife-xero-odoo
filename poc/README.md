# Xero Integration Proof of Concept

This script demonstrates basic integration with Xero:
1. Authenticates using OAuth2.
2. Creates a contact marked as a supplier.
3. Creates a bill (ACCPAY invoice) for that contact.
4. Attaches a PDF document to the bill.

## Setup

1. **Get Xero Credentials:**
   - Go to [Xero Developer Portal](https://developer.xero.com/).
   - Create a new App.
   - Set Redirect URI to `https://localhost:5000/callback`.
   - Copy Client ID and Client Secret.

2. **Configure Environment:**
   - Copy `.env.example` to `.env`:
     ```bash
     cp .env.example .env
     ```
   - Fill in your `XERO_CLIENT_ID` and `XERO_CLIENT_SECRET`.

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Running the PoC

1. Run the script:
   ```bash
   python poc_xero.py
   ```
2. The script will start a temporary web server on port 5000 with a self-signed certificate.
3. Open `https://localhost:5000` in your browser. (You may need to bypass the browser security warning for the self-signed certificate).
4. Authorize the app with your Xero organization.
5. Once authorized, the script will automatically continue in the terminal to:
   - Create the contact "Demo Supplier Ltd".
   - Create a Draft bill.
   - Attach `demo-bill.pdf`.

## Files
- `poc_xero.py`: The main PoC script.
- `requirements.txt`: Python dependencies.
- `demo-bill.pdf`: Sample attachment.
