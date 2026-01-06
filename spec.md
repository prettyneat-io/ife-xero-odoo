Today we're building an integration between Odoo and Xero. 

Initially, we want to build a proof of concept python script that will:
1. Authenticate 
2. Create a demo contact with minimal information, marked as IsSupplier = true
3. Insert a Bill via Invoice API (ACCPAY type) with an attachment 

Start by: 
1. Proposing some mock data to send
2. Providing guidance on how to get necessary client + secret for api access
3. Implementing a simple implementatation of the above
4. Testing the implementation above 

Once done:
1. We will continue with building the Odoo addon, but for now, let's build just the proof of concept.