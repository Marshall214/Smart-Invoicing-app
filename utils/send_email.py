# utils/send_email.py

import smtplib
import os
from email.message import EmailMessage

def send_email_with_invoice(client_name, client_email, invoice_path):
    # Set these to your sender credentials
    SENDER_EMAIL = os.getenv("EMAIL_USER") or "your_email@example.com"
    SENDER_PASSWORD = os.getenv("EMAIL_PASS") or "your_app_password"

    msg = EmailMessage()
    msg['Subject'] = f"Invoice for {client_name}"
    msg['From'] = SENDER_EMAIL
    msg['To'] = client_email
    msg.set_content(f"Hi {client_name},\n\nPlease find your invoice attached.\n\nThank you.")

    # Attach PDF
    with open(invoice_path, 'rb') as f:
        file_data = f.read()
        file_name = os.path.basename(invoice_path)
        msg.add_attachment(file_data, maintype='application', subtype='pdf', filename=file_name)

    # Send Email
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(SENDER_EMAIL, SENDER_PASSWORD)
        smtp.send_message(msg)

    print(f"Invoice sent to {client_email} successfully.")
