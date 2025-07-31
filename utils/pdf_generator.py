import pdfkit
import os
from jinja2 import Environment, FileSystemLoader
from datetime import datetime

# ✅ Path to wkhtmltopdf executable (adjust if your install path is different)
WKHTMLTOPDF_PATH = r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"
config = pdfkit.configuration(wkhtmltopdf=WKHTMLTOPDF_PATH)

# Set up Jinja2 environment for HTML templating
template_env = Environment(loader=FileSystemLoader('templates'))
template = template_env.get_template("invoice_template.html")

def generate_invoice_pdf(client_name, client_phone, client_address, service_items, total_amount, tax, due_date):
    # Generate a unique invoice ID based on current date and time
    invoice_id = f"INV-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # Calculate tax amount and total amount
    tax_amount = (tax / 100) * total_amount
    total = total_amount + tax_amount

    # Prepare the data to be rendered in the template
    html_out = template.render(
        invoice_id=invoice_id,
        client_name=client_name,
        client_phone=client_phone,  # Added phone number
        client_address=client_address,  # Added address
        service_items=service_items,  # List of items (description, qty, price)
        total_amount=round(total_amount, 2),
        tax=tax,
        tax_amount=round(tax_amount, 2),
        total=round(total, 2),
        due_date=due_date.strftime('%d %b %Y'),
        date_today=datetime.now().strftime('%d %b %Y')
    )

    # Output file path where the generated PDF will be saved
    output_path = os.path.join("invoices", f"{invoice_id}.pdf")

    # Convert HTML to PDF using the specified wkhtmltopdf configuration
    try:
        pdfkit.from_string(html_out, output_path, configuration=config)
        return output_path
    except Exception as e:
        print(f"Error generating PDF: {e}")
        return None
