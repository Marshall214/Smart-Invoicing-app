import streamlit as st
import os
from datetime import date
from utils.pdf_generator import generate_invoice_pdf
from utils.send_email import send_email_with_invoice
# from utils.whatsapp_api import send_invoice_whatsapp
import json
import random
import string
import time
from datetime import timedelta
import bcrypt


# Function to load users from the JSON file (for user authentication)
def load_users():
    try:
        with open(os.path.join("user", "users.json"), "r") as f:
            users = json.load(f)
    except FileNotFoundError:
        users = []
    return users

# Function to save users to the JSON file
def save_users(users):
    with open(os.path.join("user", "users.json"), "w") as f:
        json.dump(users, f, indent=4)

# Function to verify login credentials
def verify_login(username, password):
    users = load_users()
    for user in users:
        if user["username"] == username:
            if bcrypt.checkpw(password.encode(), user["password"].encode()):
                return user
    return None

# Function to check if the passwords match during sign up
def check_passwords_match(password, confirm_password):
    return password == confirm_password

# Function to generate a password reset token
def generate_reset_token():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=8))

# Function to send the password reset token via email
def send_reset_email(user_email, token):
    sender_email = "emmanuel.onuora@gmail.com"
    receiver_email = user_email
    password = "tpotmycgjjmszlup"

    subject = "Password Reset Request"
    body = f"Hello,\n\nYou requested a password reset. Use the following token to reset your password: {token}\n\nThis token will expire in 30 minutes."
    message = f"Subject: {subject}\n\n{body}"

    try:
        import smtplib
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message)
        server.quit()
        st.success("Password reset token sent successfully!")
    except Exception as e:
        st.error(f"Failed to send email: {e}")

# Function to update the user's password
def reset_password(username, new_password):
    users = load_users()
    for user in users:
        if user["username"] == username:
            user["password"] = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
            save_users(users)
            return True
    return False

# Function to validate if the token is still valid
def is_token_valid(expiry_time):
    return time.time() < expiry_time

if 'role' not in st.session_state:
    st.session_state['role'] = None

if st.session_state['role'] is None:
    st.title("Login / Sign Up")
    choice = st.radio("Choose an option", ["Login", "Sign Up", "Reset Password"])

    if choice == "Login":
        username = st.text_input("Username", key="login_username_input")
        password = st.text_input("Password", type="password", key="login_password_input")
        if st.button("Login"):
            user = verify_login(username, password)
            if user:
                st.session_state['role'] = user['role']
                st.session_state['username'] = user['username']
                st.success(f"Logged in as {user['role']}!")
            else:
                st.error("Invalid username or password")

    elif choice == "Sign Up":
        first_name = st.text_input("First Name", key="signup_first_name_input")
        last_name = st.text_input("Last Name", key="signup_last_name_input")
        email = st.text_input("Email", key="signup_email_input")
        username = st.text_input("Username", key="signup_username_input")
        password = st.text_input("Password", type="password", key="signup_password_input")
        confirm_password = st.text_input("Confirm Password", type="password", key="signup_confirm_password_input")

        if st.button("Sign Up"):
            if check_passwords_match(password, confirm_password):
                users = load_users()
                if any(u["username"] == username for u in users):
                    st.error("Username already exists. Please choose a different one.")
                else:
                    new_user = {
                        "first_name": first_name,
                        "last_name": last_name,
                        "email": email,
                        "username": username,
                        "password": bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode(),
                        "role": "superadmin",
                    }
                    users.append(new_user)
                    save_users(users)
                    st.session_state['role'] = "superadmin"
                    st.session_state['username'] = username
                    st.success("Sign up successful! You're logged in as Super Admin.")
            else:
                st.error("Passwords do not match.")

    elif choice == "Reset Password":
        reset_username = st.text_input("Enter your username to reset password", key="reset_username_input")
        if st.button("Generate Reset Token"):
            users = load_users()
            user = next((user for user in users if user["username"] == reset_username), None)
            if user:
                reset_token = generate_reset_token()
                send_reset_email(user["email"], reset_token)
                st.session_state['reset_token'] = reset_token
                st.session_state['reset_token_expiry'] = time.time() + 1800
                st.session_state['reset_username'] = reset_username
            else:
                st.error("Username not found.")

        if 'reset_token' in st.session_state:
            entered_token = st.text_input("Enter the reset token", key="reset_token_input")
            new_password = st.text_input("New password", type="password", key="reset_new_password_input")
            confirm_password = st.text_input("Confirm new password", type="password", key="reset_confirm_password_input")

            if st.button("Reset Password"):
                if entered_token == st.session_state['reset_token']:
                    if is_token_valid(st.session_state['reset_token_expiry']):
                        if check_passwords_match(new_password, confirm_password):
                            if reset_password(st.session_state['reset_username'], new_password):
                                st.success("Your password has been successfully reset.")
                                del st.session_state['reset_token']
                                del st.session_state['reset_token_expiry']
                                del st.session_state['reset_username']
                            else:
                                st.error("Error resetting password.")
                        else:
                            st.error("Passwords do not match.")
                    else:
                        st.error("The reset token has expired.")
                else:
                    st.error("Invalid token.")

if st.session_state['role'] is not None:
    st.sidebar.header(f"Welcome, {st.session_state['username']}")
    if st.sidebar.button("Logout"):
        st.session_state.clear()
        st.stop()

    role = st.session_state['role']

    # Invoice Creation and Viewing for both Superadmin and Staff
    if role in ["superadmin", "staff"]:
        st.markdown("---")
        st.subheader("Invoice Details")

        # Collecting client information
        client_name = st.text_input("Client Name", key="client_name_input")
        client_phone = st.text_input("Client Phone Number", key="client_phone_input")
        client_address = st.text_area("Client Address", key="client_address_input")
        client_email = st.text_input("Client Email", key="client_email_input")

        # Add rows for invoice items (s/n, description, qty, unit price, total price)
        if 'invoice_items' not in st.session_state:
            st.session_state.invoice_items = []

        # Add the first row (if no rows exist)
        if len(st.session_state.invoice_items) == 0:
            st.session_state.invoice_items.append({
                "description": "",
                "quantity": 1,
                "unit_price": 0.0,
                "total_price": 0.0
            })

        # Show and handle the input for each invoice item
        for idx, item in enumerate(st.session_state.invoice_items):
            col1, col2, col3, col4, col5 = st.columns([1, 3, 1, 1, 1])

            with col1:
                st.text(f"{idx + 1}")  # Serial Number
            with col2:
                item["description"] = st.text_input(f"Description {idx + 1}", value=item["description"], key=f"description_{idx}")
            with col3:
                item["quantity"] = st.number_input(f"Qty {idx + 1}", min_value=1, value=item["quantity"], key=f"qty_{idx}")
            with col4:
                item["unit_price"] = st.number_input(f"Unit Price {idx + 1}", min_value=0.0, value=item["unit_price"], format="%.2f", key=f"unit_price_{idx}")
            with col5:
                item["total_price"] = round(item["quantity"] * item["unit_price"], 2)
                st.write(f"₦{item['total_price']}")

        if st.button("Add Item"):
            st.session_state.invoice_items.append({
                "description": "",
                "quantity": 1,
                "unit_price": 0.0,
                "total_price": 0.0
            })

        # Calculate total amount and VAT
        total_amount = sum(item["total_price"] for item in st.session_state.invoice_items)
        vat = st.number_input("VAT (%)", min_value=0.0, max_value=100.0, value=7.5, key="vat_input")
        vat_amount = (vat / 100) * total_amount
        total_with_vat = total_amount + vat_amount

        # Display the total amount
        st.markdown(f"**Total Amount: ₦{round(total_amount, 2)}**")
        st.markdown(f"**VAT: ₦{round(vat_amount, 2)}**")
        st.markdown(f"**Total with VAT: ₦{round(total_with_vat, 2)}**")

        if st.button("Generate Invoice"):
            if client_name and client_phone and client_address and client_email:
                invoice_path = generate_invoice_pdf(client_name, client_phone, client_address, st.session_state.invoice_items, total_with_vat, vat, date.today())
                st.success("✅ Invoice generated successfully!")

                with open(invoice_path, "rb") as f:
                    st.download_button("⬇ View Invoice", f, file_name=os.path.basename(invoice_path), mime="application/pdf")

                # Reset the form inputs for new invoice
                st.session_state["client_name_input"] = ""
                st.session_state["client_phone_input"] = ""
                st.session_state["client_address_input"] = ""
                st.session_state["client_email_input"] = ""
                st.session_state["invoice_items"] = []

        # Display all generated invoices
        st.markdown("---")
        st.subheader("📁 All Generated Invoices")
        invoice_files = os.listdir("invoices")
        if invoice_files:
            for file in invoice_files:
                file_path = os.path.join("invoices", file)
                with open(file_path, "rb") as f:
                    st.download_button(f"⬇ {file}", f, file_name=file, mime="application/pdf")
                    if role == "superadmin":
                        # Superadmin can download
                        st.download_button("⬇ Download", f, file_name=file, mime="application/pdf")
                    # Staff can only view and share (no download)
                    if role == "staff":
                        st.button("📧 Send via Email", on_click=send_email_with_invoice, args=(file,))
        else:
            st.info("No invoices found.")

    # For Superadmin: Staff Account Creation
    if role == "superadmin":
        st.markdown("---")
        st.subheader("👤 Create New Staff Account")
        first_name = st.text_input("First Name", key="staff_first_name_input")
        last_name = st.text_input("Last Name", key="staff_last_name_input")
        email = st.text_input("Email", key="staff_email_input")
        password = st.text_input("Password", type="password", key="staff_password_input")

        if st.button("Create Staff Account"):
            users = load_users()
            new_user = {
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "username": f"{first_name.lower().strip()}{last_name.lower().strip()}",
                "password": bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode(),
                "role": "staff",
            }
            users.append(new_user)
            save_users(users)
            st.success(f"✅ Staff account created for {first_name} {last_name} ({email})")
