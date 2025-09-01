import streamlit as st
import pdfplumber
import pytesseract
import fitz  # PyMuPDF
import pandas as pd
import numpy as np
import cv2
import tempfile
import os
import re
import io
from PIL import Image
from datetime import datetime
import uuid

# Set page configuration and theme
st.set_page_config(
    page_title="Invoice Checker - Fraud Detection System",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main {background-color: #0E1117; color: #FAFAFA;}
    .stButton>button {
        background-color: #4CAF50; 
        color: white;
        font-weight: 600;
        border-radius: 8px;
        padding: 0.75rem 1.5rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        border: none;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .stButton>button:hover {
        background-color: #3d8b40;
        box-shadow: 0 6px 8px rgba(0, 0, 0, 0.15);
        transform: translateY(-2px);
    }
    .stButton>button:active {
        transform: translateY(1px);
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    .stTextInput>div>div>input {background-color: #262730; color: #FAFAFA; border-radius: 8px; padding: 0.75rem;}
    .stSelectbox>div>div>select {background-color: #262730; color: #FAFAFA;}
    .stHeader {color: #4CAF50;}
    .stDataFrame {color: #FAFAFA;}
    .css-1d391kg {background-color: #1E1E1E;}
    .css-12oz5g7 {padding-top: 2rem;}
    .fraud-alert {color: #FF4B4B; font-weight: bold;}
    .valid-alert {color: #4CAF50; font-weight: bold;}
    .suspicious-alert {color: #FFA500; font-weight: bold;}
    footer {visibility: hidden;}
    
    /* Social login buttons */
    .social-login-button {
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 12px 16px;
        margin: 10px 0;
        border-radius: 8px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s ease;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    .social-login-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
    }
    .social-login-button:active {
        transform: translateY(1px);
    }
    .google-login {
        background-color: white;
        color: #757575;
        border: 1px solid #dadce0;
    }
    .google-login:hover {
        background-color: #f8f9fa;
    }
    .email-login {
        background-color: #0078d4;
        color: white;
    }
    .email-login:hover {
        background-color: #106ebe;
    }
    .button-icon {
        width: 24px;
        height: 24px;
        margin-right: 12px;
    }
    .divider {
        text-align: center;
        margin: 20px 0;
        color: #9e9e9e;
        position: relative;
    }
    .divider:before, .divider:after {
        content: "";
        position: absolute;
        top: 50%;
        width: 45%;
        height: 1px;
        background-color: #4a4a4a;
    }
    .divider:before {
        left: 0;
    }
    .divider:after {
        right: 0;
    }
    
    /* New custom styles */
    .app-header {font-size: 2.5rem; font-weight: 700; margin-bottom: 0;}
    .app-subheader {font-size: 1.5rem; font-weight: 400; margin-top: 0; margin-bottom: 2rem; color: #9e9e9e;}
    .status-card {background-color: #1E1E1E; padding: 1rem; border-radius: 0.5rem; margin-bottom: 1rem;}
    .status-indicator {display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 0.5rem;}
    .status-online {background-color: #4CAF50;}
    .status-offline {background-color: #FF4B4B;}
    .user-profile {text-align: center; padding: 1rem; margin-top: 2rem;}
    .user-avatar {font-size: 2rem; background-color: #4CAF50; color: white; width: 50px; height: 50px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; margin-bottom: 0.5rem;}
    .upload-container {border: 2px dashed #4CAF50; border-radius: 0.5rem; padding: 2rem; text-align: center; margin-top: 1rem;}
    
    /* Responsive design */
    @media (max-width: 768px) {
        .app-header {font-size: 2rem;}
        .app-subheader {font-size: 1.2rem;}
        .stButton>button {padding: 0.6rem 1.2rem;}
        .social-login-button {padding: 10px 14px;}
    }
    @media (max-width: 480px) {
        .app-header {font-size: 1.8rem;}
        .app-subheader {font-size: 1rem;}
        .stButton>button {padding: 0.5rem 1rem; font-size: 0.9rem;}
        .social-login-button {padding: 8px 12px; font-size: 0.9rem;}
    }
</style>
""", unsafe_allow_html=True)

if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if 'vendors' not in st.session_state:
    st.session_state.vendors = {
        # Sample vendors for demonstration
        'Apple Inc.': {'status': 'active', 'risk_score': 'low'},
        'Microsoft Corporation': {'status': 'active', 'risk_score': 'low'},
        'Fake Supplies Ltd.': {'status': 'inactive', 'risk_score': 'high'},
        'Suspicious Vendor Co.': {'status': 'active', 'risk_score': 'medium'}
    }

if 'admin_users' not in st.session_state:
    st.session_state.admin_users = {
        'admin@example.com': {
            'password': 'admin123',  # In production, use hashed passwords
            'name': 'Admin User',
            'role': 'Fraud Detection Specialist'
        },
        'user@example.com': {
            'password': 'user123',
            'name': 'Regular User',
            'role': 'Document Analyst'
        }
    }

if 'otp_data' not in st.session_state:
    st.session_state.otp_data = {}

if 'session_expiry' not in st.session_state:
    st.session_state.session_expiry = {}

def generate_otp(email):
    import random
    import time
    
    otp = ''.join([str(random.randint(0, 9)) for _ in range(6)])
    
    st.session_state.otp_data[email] = {
        'otp': otp,
        'created_at': time.time(),
        'valid_for': 600  # 10 minutes in seconds
    }
    
    return otp

def verify_otp(email, otp):
    import time
    
    if email not in st.session_state.otp_data:
        return False
    
    otp_info = st.session_state.otp_data[email]
    current_time = time.time()

    if otp_info['otp'] == otp and (current_time - otp_info['created_at']) < otp_info['valid_for']:

        del st.session_state.otp_data[email]
        return True
    
    return False


def send_otp_email(email, otp):

    st.session_state.last_otp = otp  
    return True

def authenticate(email, otp=None, keep_logged_in=False):
    # First check if the email exists
    if email in st.session_state.admin_users:
        if otp is None:

            new_otp = generate_otp(email)
            if send_otp_email(email, new_otp):
                return "otp_sent"
            else:
                return False
        else:

            if verify_otp(email, otp):
                st.session_state.authenticated = True
                st.session_state.current_user = {
                    'email': email,
                    'name': st.session_state.admin_users[email]['name'],
                    'role': st.session_state.admin_users[email]['role']
                }

                if not keep_logged_in:
                    import time

                    st.session_state.session_expiry[email] = time.time() + 1800
                
                return True
            else:
                return False
    return False


def check_session_expired():
    import time
    
    if not st.session_state.authenticated or 'current_user' not in st.session_state:
        return False
    
    email = st.session_state.current_user['email']
    
    # If keep_logged_in was true, there's no expiry
    if email not in st.session_state.session_expiry:
        return False
    
    current_time = time.time()
    if current_time > st.session_state.session_expiry[email]:
        
        logout()
        return True
    
    return False

def logout():
    st.session_state.authenticated = False
    if 'current_user' in st.session_state:
        email = st.session_state.current_user['email']
        if email in st.session_state.session_expiry:
            del st.session_state.session_expiry[email]
        del st.session_state.current_user

def handle_oauth_callback():
    """Handle OAuth callback from Google and Outlook"""
    query_params = st.query_params
    
    if 'code' in query_params:
        code = query_params['code'][0]
        
        # Determine provider from path
        if 'callback/google' in st.query_params.get('path', [''])[0]:
            try:
                
                user_info = {
                    'email': 'user@gmail.com',  
                    'name': 'Google User',
                    'provider': 'google'
                }
                
                # Create user if not exists
                if user_info['email'] not in st.session_state.admin_users:
                    st.session_state.admin_users[user_info['email']] = {
                        'name': user_info['name'],
                        'role': 'Document Analyst',
                        'provider': 'google'
                    }
                
                
                st.session_state.authenticated = True
                st.session_state.current_user = {
                    'email': user_info['email'],
                    'name': user_info['name'],
                    'role': st.session_state.admin_users[user_info['email']]['role']
                }
                
                
                st.experimental_set_query_params()
                st.success("Successfully logged in with Google!")
                
            except Exception as e:
                st.error(f"Error authenticating with Google: {str(e)}")
                
        elif 'callback/outlook' in st.query_params.get('path', [''])[0]:
            try:
              
                user_info = {
                    'email': 'user@outlook.com', 
                    'name': 'Outlook User',
                    'provider': 'outlook'
                }
                
               
                if user_info['email'] not in st.session_state.admin_users:
                    st.session_state.admin_users[user_info['email']] = {
                        'name': user_info['name'],
                        'role': 'Document Analyst',
                        'provider': 'outlook'
                    }
                
              
                st.session_state.authenticated = True
                st.session_state.current_user = {
                    'email': user_info['email'],
                    'name': user_info['name'],
                    'role': st.session_state.admin_users[user_info['email']]['role']
                }
                
               
                st.experimental_set_query_params()
                st.success("Successfully logged in with Outlook!")
                
            except Exception as e:
                st.error(f"Error authenticating with Outlook: {str(e)}")
    
 
    elif 'error' in query_params:
        error = query_params['error'][0]
        error_description = query_params.get('error_description', ['Unknown error'])[0]
        st.error(f"Authentication error: {error} - {error_description}")
        st.experimental_set_query_params()


def check_tesseract_installation():
    try:
        
        version = pytesseract.get_tesseract_version()
        return True, f"Tesseract OCR v{version} is installed and configured correctly."
    except Exception as e:
        return False, f"Tesseract OCR is not properly configured: {str(e)}"


if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
    

if 'tesseract_checked' not in st.session_state:
    tesseract_available, tesseract_message = check_tesseract_installation()
    st.session_state.tesseract_available = tesseract_available
    st.session_state.tesseract_message = tesseract_message
    
if 'alert_enabled' not in st.session_state:
    st.session_state.alert_enabled = True
    
if 'last_alert_time' not in st.session_state:
    st.session_state.last_alert_time = None

handle_oauth_callback()

def get_ai_response(query, invoice_data=None):
    
    query = query.lower()
    
    if invoice_data is None:
        if any(word in query for word in ['hello', 'hi', 'hey']):
            return "Hello! I'm your invoice assistant. Please upload an invoice or receipt to get started. I can help you analyze documents for fraud indicators, extract key information, and answer questions about invoice processing."
        elif 'help' in query:
            return "I can help you with the following:\n\n• Analyzing invoices and receipts for potential fraud\n• Extracting key information like dates, amounts, and vendor details\n• Explaining invoice terminology\n• Providing insights on invoice processing best practices\n\nTry uploading a document first, then ask specific questions about it."
        else:
            return "Please upload an invoice first so I can help answer your questions about it."
    
    if any(word in query for word in ['vendor', 'supplier', 'seller', 'company']):
        return f"The vendor on this invoice is {invoice_data.get('vendor', 'not specified')}."
    
    elif any(word in query for word in ['total', 'amount', 'cost', 'price']):
        return f"The total amount on this invoice is {invoice_data.get('currency', '$')}{invoice_data.get('total_amount', 'not specified')}."
    
    elif any(word in query for word in ['date', 'when', 'time']):
        return f"This invoice was issued on {invoice_data.get('invoice_date', 'not specified')}."
    
    elif any(word in query for word in ['due', 'payment', 'deadline']):
        return f"The payment is due on {invoice_data.get('due_date', 'not specified')}."
    
    elif any(word in query for word in ['items', 'products', 'services', 'purchased']):
        if invoice_data.get('line_items'):
            items = ', '.join([item.get('description', 'Item') for item in invoice_data.get('line_items', [])])
            return f"The invoice includes: {items}."
        else:
            return "I couldn't find detailed line items on this invoice."
    
    elif any(word in query for word in ['fraud', 'suspicious', 'fake', 'legitimate', 'valid']):
        fraud_score = invoice_data.get('fraud_score', 'low')
        fraud_reasons = invoice_data.get('fraud_reasons', [])
        
        if fraud_score == 'high':
            return f"⚠️ This document has high fraud risk indicators. Issues detected: {', '.join(fraud_reasons) if fraud_reasons else 'Multiple suspicious elements found'}. I recommend additional verification before processing this document."
        elif fraud_score == 'medium':
            return f"⚠️ This document has some suspicious elements. Potential issues: {', '.join(fraud_reasons) if fraud_reasons else 'Some inconsistencies detected'}. Consider verifying these details before proceeding."
        elif fraud_score == 'low':
            return f"✅ This document appears legitimate with low fraud risk. {', '.join(fraud_reasons) if fraud_reasons else 'No significant issues detected.'}"
        else:
            return "Based on my analysis, this invoice appears to be legitimate. There are no obvious fraud indicators detected."
    
    else:
        return "I'm not sure how to answer that question about this invoice. Try asking about the vendor, total amount, date, or line items."

if not st.session_state.authenticated:

    st.markdown("<h1 class='app-header'>🔍 Invoice Checker</h1>", unsafe_allow_html=True)
    st.markdown("<p class='app-subheader'>Get invoice analysis using AI</p>", unsafe_allow_html=True)
    
    if 'signup_mode' not in st.session_state:
        st.session_state.signup_mode = False
        
    header_title = "Create Account" if st.session_state.signup_mode else "Sign In"
    header_subtitle = "Sign up to get started" if st.session_state.signup_mode else "Sign in to your account"
    
    st.markdown("""
    <style>
    .login-container {
        max-width: 400px;
        margin: 0 auto;
        padding: 2rem;
        background-color: #1E1E1E;
        border-radius: 0.5rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .login-header {
        text-align: center;
        margin-bottom: 1.5rem;
    }
    .social-login-button {
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 10px;
        margin-bottom: 10px;
        border-radius: 4px;
        cursor: pointer;
        font-weight: 500;
        transition: all 0.3s ease;
        text-align: center;
        position: relative;
    }
    .social-login-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    .social-login-button:active {
        transform: translateY(0);
    }
    .button-icon {
        margin-right: 10px;
        width: 20px;
        height: 20px;
    }
    .google-login {
        background-color: #ffffff;
        color: #757575;
        border: 1px solid #dadce0;
    }
    .google-login:hover {
        background-color: #f8f8f8;
    }
    .facebook-login {
        background-color: #1877f2;
        color: white;
    }
    .facebook-login:hover {
        background-color: #166fe5;
    }
    .instagram-login {
        background: linear-gradient(45deg, #f09433 0%, #e6683c 25%, #dc2743 50%, #cc2366 75%, #bc1888 100%);
        color: white;
    }
    .instagram-login:hover {
        opacity: 0.9;
    }
    .email-login {
        background-color: #0078d4;
        color: white;
    }
    .email-login:hover {
        background-color: #106ebe;
    }
    .divider {
        display: flex;
        align-items: center;
        text-align: center;
        margin: 15px 0;
        color: #9e9e9e;
    }
    .divider::before, .divider::after {
        content: '';
        flex: 1;
        border-bottom: 1px solid #9e9e9e;
    }
    .divider::before {
        margin-right: 10px;
    }
    .divider::after {
        margin-left: 10px;
    }
    .toggle-signup {
        text-align: center;
        margin-top: 15px;
        color: #9e9e9e;
    }
    .toggle-signup a {
        color: #4CAF50;
        text-decoration: none;
        cursor: pointer;
    }
    </style>
    
    <div class='login-container'>
    <div class='login-header'>
        <h2>""" + header_title + """</h2>
        <p>""" + header_subtitle + """</p>
    </div>
    </div>
    """, unsafe_allow_html=True)
    
   
    if 'otp_verification_mode' not in st.session_state:
        st.session_state.otp_verification_mode = False
        
    if 'email_for_otp' not in st.session_state:
        st.session_state.email_for_otp = ""
    
   
    with st.container():
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            
            if not st.session_state.signup_mode and not st.session_state.otp_verification_mode:
                
                google_client_id = "YOUR_GOOGLE_CLIENT_ID.apps.googleusercontent.com"  # Replace with your actual client ID
                google_redirect_uri = "http://localhost:8501/callback/google"
                google_scope = "email profile"
                google_auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?client_id={google_client_id}&redirect_uri={google_redirect_uri}&response_type=code&scope={google_scope}&access_type=offline&prompt=consent"
                
                google_button = f"""
                <a href="{google_auth_url}" style="text-decoration: none;">
                    <div class="social-login-button google-login">
                        <svg class="button-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48">
                            <path fill="#FFC107" d="M43.611,20.083H42V20H24v8h11.303c-1.649,4.657-6.08,8-11.303,8c-6.627,0-12-5.373-12-12c0-6.627,5.373-12,12-12c3.059,0,5.842,1.154,7.961,3.039l5.657-5.657C34.046,6.053,29.268,4,24,4C12.955,4,4,12.955,4,24c0,11.045,8.955,20,20,20c11.045,0,20-8.955,20-20C44,22.659,43.862,21.35,43.611,20.083z"/>
                            <path fill="#FF3D00" d="M6.306,14.691l6.571,4.819C14.655,15.108,18.961,12,24,12c3.059,0,5.842,1.154,7.961,3.039l5.657-5.657C34.046,6.053,29.268,4,24,4C16.318,4,9.656,8.337,6.306,14.691z"/>
                            <path fill="#4CAF50" d="M24,44c5.166,0,9.86-1.977,13.409-5.192l-6.19-5.238C29.211,35.091,26.715,36,24,36c-5.202,0-9.619-3.317-11.283-7.946l-6.522,5.025C9.505,39.556,16.227,44,24,44z"/>
                            <path fill="#1976D2" d="M43.611,20.083H42V20H24v8h11.303c-0.792,2.237-2.231,4.166-4.087,5.571c0.001-0.001,0.002-0.001,0.003-0.002l6.19,5.238C36.971,39.205,44,34,44,24C44,22.659,43.862,21.35,43.611,20.083z"/>
                        </svg>
                        Continue with Google
                    </div>
                </a>
                """
                
                # Outlook login button with logo
                outlook_client_id = "YOUR_OUTLOOK_CLIENT_ID"  # Replace with your actual client ID
                outlook_redirect_uri = "http://localhost:8501/callback/outlook"
                outlook_scope = "openid profile email User.Read"
                outlook_auth_url = f"https://login.microsoftonline.com/common/oauth2/v2.0/authorize?client_id={outlook_client_id}&redirect_uri={outlook_redirect_uri}&response_type=code&scope={outlook_scope}&response_mode=query"
                
                email_button = f"""
                <a href="{outlook_auth_url}" style="text-decoration: none;">
                    <div class="social-login-button email-login">
                        <svg class="button-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="white">
                            <path d="M22.28 6.633c0-.344-.14-.672-.387-.915-.246-.242-.578-.378-.925-.378H3.032c-.347 0-.679.136-.925.378-.247.243-.387.571-.387.915v10.734c0 .344.14.672.387.915.246.242.578.378.925.378h17.936c.347 0 .679-.136.925-.378.247-.243.387-.571.387-.915V6.633zm-2.022.915v9.819H3.742V7.548h16.516zm-9.031 5.233L4.452 7.548h15.097l-6.775 5.233c-.347.269-.839.269-1.186 0z"/>
                        </svg>
                        Continue with Outlook
                    </div>
                </a>
                """
                
                st.markdown(google_button, unsafe_allow_html=True)
                st.markdown("<div class=\"divider\">OR</div>", unsafe_allow_html=True)
                st.markdown(email_button, unsafe_allow_html=True)
            
            # OTP Verification Mode
            if st.session_state.otp_verification_mode:
                st.info(f"An OTP has been sent to {st.session_state.email_for_otp}. Please check your email.")
                st.markdown("<p>The OTP is valid for 10 minutes. Please enter it below:</p>", unsafe_allow_html=True)
                
                # For demo purposes only - show the OTP
                if 'last_otp' in st.session_state:
                    st.code(f"Demo OTP: {st.session_state.last_otp}", language="text")
                
                # OTP input field
                otp = st.text_input("Enter OTP", max_chars=6)
                
                # Keep me logged in checkbox
                keep_logged_in = st.checkbox("Keep me logged in", help="If checked, you will stay logged in until you manually log out.")
                
                # Verify OTP button
                verify_button = st.button("Verify OTP", use_container_width=True)
                
                # Resend OTP button
                if st.button("Resend OTP"):
                    new_otp = generate_otp(st.session_state.email_for_otp)
                    if send_otp_email(st.session_state.email_for_otp, new_otp):
                        st.success("New OTP sent successfully!")
                        st.rerun()
                
                # Back button
                if st.button("Back to Login"):
                    st.session_state.otp_verification_mode = False
                    st.session_state.email_for_otp = ""
                    st.rerun()
                
                # Handle OTP verification
                if verify_button and otp:
                    if authenticate(st.session_state.email_for_otp, otp, keep_logged_in):
                        st.success("Login successful!")
                        st.rerun()
                    else:
                        st.error("Invalid or expired OTP. Please try again or request a new one.")
            
            # Regular Login/Signup Mode
            elif not st.session_state.otp_verification_mode:
                # Email field
                email = st.text_input("Email")
                
                # Username field (only in signup mode)
                if st.session_state.signup_mode:
                    username = st.text_input("Username")
                    
                    # Password field for signup
                    password = st.text_input("Password", type="password")
                    
                    # Confirm password field
                    confirm_password = st.text_input("Confirm Password", type="password")
                
                # Login/Signup button with enhanced styling
                button_label = "Sign Up" if st.session_state.signup_mode else "Sign On"
                
                # Custom CSS for the Sign On button
                st.markdown("""
                <style>
                .sign-on-button {
                    background: linear-gradient(90deg, #4CAF50 0%, #3d8b40 100%);
                    color: white;
                    font-weight: 600;
                    border-radius: 8px;
                    padding: 12px 24px;
                    cursor: pointer;
                    transition: all 0.3s ease;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                    border: none;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                    width: 100%;
                    text-align: center;
                    margin-top: 10px;
                    margin-bottom: 15px;
                    font-size: 16px;
                }
                .sign-on-button:hover {
                    background: linear-gradient(90deg, #3d8b40 0%, #2d682f 100%);
                    box-shadow: 0 6px 8px rgba(0, 0, 0, 0.15);
                    transform: translateY(-2px);
                }
                </style>
                """, unsafe_allow_html=True)
                
                # Use the standard button for functionality but with better styling
                action_button = st.button(button_label, use_container_width=True, key="sign_on_button")
                
                # Toggle between login and signup
                toggle_text = "Already have an account? Sign In" if st.session_state.signup_mode else "Don't have an account? Sign Up"
                if st.button(toggle_text):
                    st.session_state.signup_mode = not st.session_state.signup_mode
                    st.rerun()
                
                # Handle form submission
                if action_button:
                    if st.session_state.signup_mode:
                        # Handle signup
                        if not email or not username or not password:
                            st.error("Please fill in all fields.")
                        elif password != confirm_password:
                            st.error("Passwords do not match.")
                        elif email in st.session_state.admin_users:
                            st.error("Email already registered. Please use a different email.")
                        else:
                            # Register new user
                            st.session_state.admin_users[email] = {
                                'password': password,  # In production, use hashed passwords
                                'name': username,
                                'role': 'Document Analyst'
                            }
                            st.success("Account created successfully! Please sign in.")
                            st.session_state.signup_mode = False
                            st.rerun()
                    else:
                        # Handle login with OTP
                        if not email:
                            st.error("Please enter your email address.")
                        elif email not in st.session_state.admin_users:
                            st.error("Email not registered. Please sign up first.")
                        else:
                            # Send OTP and switch to verification mode
                            result = authenticate(email)
                            if result == "otp_sent":
                                st.session_state.otp_verification_mode = True
                                st.session_state.email_for_otp = email
                                st.rerun()
                            else:
                                st.error("Failed to send OTP. Please try again.")
    
    # No system status at the bottom of login page

else:
    # Check if session has expired
    if check_session_expired():
        st.warning("Your session has expired. Please log in again.")
        st.rerun()
    
    # Sidebar for authenticated users
    st.sidebar.markdown("<h1 class='app-header'>🔍 Invoice Checker</h1>", unsafe_allow_html=True)
    st.sidebar.markdown("<p class='app-subheader'>Fraud Detection System</p>", unsafe_allow_html=True)
    st.sidebar.markdown("---")

    # Sidebar navigation
    page = st.sidebar.radio("Navigation", ["Dashboard", "Check Invoice", "Manage Vendors", "Settings"])

    # User Profile with current user info
    if 'current_user' in st.session_state:
        user = st.session_state.current_user
        initials = user['name'][0] if user['name'] else 'U'
        st.sidebar.markdown(f"""<div class='user-profile'>
            <div class='user-avatar'>{initials}</div>
            <p><strong>{user['name']}</strong><br>{user['role']}</p>
            </div>""", unsafe_allow_html=True)
        
        # Alert settings
        st.sidebar.markdown("### Settings")
        alert_enabled = st.sidebar.checkbox("Enable Invoice Scan Alerts", value=st.session_state.alert_enabled)
        if alert_enabled != st.session_state.alert_enabled:
            st.session_state.alert_enabled = alert_enabled
            if alert_enabled:
                st.sidebar.success("Invoice scan alerts enabled")
            else:
                st.sidebar.info("Invoice scan alerts disabled")
    
    # Logout button
    if st.sidebar.button("Logout", key="logout_button"):
        logout()
        st.rerun()
    
    # No footer in admin pages

# Helper functions for document processing
def extract_invoice_data(pdf_file):
    """Extract data from invoice PDF using pdfplumber and PyMuPDF"""
    try:
        # Use pdfplumber for text extraction
        with pdfplumber.open(pdf_file) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text() + "\n"
        
        # Also use PyMuPDF for better table extraction
        doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
        
        # Extract invoice fields using regex patterns
        invoice_number = extract_field(text, r'(?i)invoice\s*(?:#|number|num|no)\s*[:\-]?\s*([A-Za-z0-9\-]+)')
        invoice_date = extract_date(text, r'(?i)invoice\s*date\s*[:\-]?\s*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4}|\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{2,4})')
        due_date = extract_date(text, r'(?i)due\s*date\s*[:\-]?\s*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4}|\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{2,4})')
        vendor = extract_field(text, r'(?i)(?:from|vendor|seller|billed\s*from|supplier)\s*[:\-]?\s*([A-Za-z0-9\s.,&]+?)(?:\n|\r|\s{2,})')
        customer = extract_field(text, r'(?i)(?:to|bill\s*to|sold\s*to|customer|client)\s*[:\-]?\s*([A-Za-z0-9\s.,&]+?)(?:\n|\r|\s{2,})')
        total_amount = extract_amount(text, r'(?i)(?:total|amount\s*due|balance\s*due)\s*[:\-]?\s*[$€£¥]?\s*(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2}))')
        subtotal = extract_amount(text, r'(?i)(?:subtotal|sub\s*total|net\s*amount)\s*[:\-]?\s*[$€£¥]?\s*(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2}))')
        tax_amount = extract_amount(text, r'(?i)(?:tax|vat|gst|hst|sales\s*tax)\s*[:\-]?\s*[$€£¥]?\s*(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2}))')
        currency = extract_currency(text)
        
        # Extract line items (simplified approach)
        line_items = extract_line_items(text, doc)
        
        # Close the document
        doc.close()
        
        return {
            "invoice_number": invoice_number,
            "invoice_date": invoice_date,
            "vendor": vendor,
            "customer": customer,
            "total_amount": total_amount,
            "subtotal": subtotal,
            "tax_amount": tax_amount,
            "due_date": due_date,
            "currency": currency,
            "line_items": line_items,
            "document_type": "invoice"
        }
    except Exception as e:
        st.error(f"Error extracting invoice data: {str(e)}")
        return None

def preprocess_image_for_ocr(image):
    """Apply advanced preprocessing techniques to improve OCR accuracy"""
    # Convert to numpy array if it's a PIL Image
    if isinstance(image, Image.Image):
        img_np = np.array(image)
    else:
        img_np = image
    
    # Convert to grayscale if needed
    gray = cv2.cvtColor(img_np, cv2.COLOR_BGR2GRAY) if len(img_np.shape) == 3 else img_np
    
    # Apply noise reduction
    denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
    
    # Apply adaptive thresholding
    adaptive_thresh = cv2.adaptiveThreshold(denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    
    # Apply dilation to make text more prominent
    kernel = np.ones((1, 1), np.uint8)
    dilated = cv2.dilate(adaptive_thresh, kernel, iterations=1)
    
    return dilated

def extract_receipt_data(file):
    """Extract data from receipt image/PDF using OCR"""
    try:
        # Check if file is PDF or image
        if file.name.lower().endswith('.pdf'):
            # Convert PDF to image for OCR
            doc = fitz.open(stream=file.read(), filetype="pdf")
            page = doc.load_page(0)  # First page
            pix = page.get_pixmap()
            img_data = pix.tobytes("png")
            image = Image.open(io.BytesIO(img_data))
            doc.close()
        else:
            # Process as image
            image = Image.open(file)
        
        # Convert to numpy array
        img_np = np.array(image)
        
        # Apply standard preprocessing
        gray = cv2.cvtColor(img_np, cv2.COLOR_BGR2GRAY) if len(img_np.shape) == 3 else img_np
        thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
        
        # Also prepare enhanced version using advanced preprocessing
        enhanced_img = preprocess_image_for_ocr(img_np)
        
        # Check if Tesseract is available and configured
        try:
            # Perform OCR with improved configuration
            custom_config = r'--oem 3 --psm 6 -l eng'
            
            # Try standard preprocessing first
            text = pytesseract.image_to_string(thresh, config=custom_config)
            
            # If text is too short or doesn't contain expected patterns, try enhanced preprocessing
            if len(text) < 50 or not re.search(r'(total|amount|receipt|invoice|date)', text.lower()):
                # Try with enhanced image
                enhanced_text = pytesseract.image_to_string(enhanced_img, config=custom_config)
                
                # Use the better result (longer text usually means better OCR)
                if len(enhanced_text) > len(text):
                    text = enhanced_text
                    
            # If still not good, try one more preprocessing method
            if len(text) < 50:
                # Try adaptive thresholding
                adaptive_thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
                adaptive_text = pytesseract.image_to_string(adaptive_thresh, config=custom_config)
                
                # Use the better result
                if len(adaptive_text) > len(text):
                    text = adaptive_text
                    
            # Log OCR success
            if len(text) > 50:
                st.success("OCR processing successful")
                
        except Exception as e:
            st.error(f"OCR Error: {str(e)}. Please ensure Tesseract OCR is installed correctly.")
            text = ""
        
        # Extract receipt fields using regex patterns
        store_name = extract_field(text, r'^([A-Za-z0-9\s.,&]+?)\n')
        date = extract_date(text, r'(?i)(?:date|dt)\s*[:\-]?\s*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4}|\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{2,4})')
        time = extract_field(text, r'(?i)(?:time)\s*[:\-]?\s*(\d{1,2}:\d{2}(?::\d{2})?\s*(?:AM|PM|am|pm)?)')
        total_amount = extract_amount(text, r'(?i)(?:total|amount|sum)\s*[:\-]?\s*[$€£¥]?\s*(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2}))')
        subtotal = extract_amount(text, r'(?i)(?:subtotal|sub\s*total)\s*[:\-]?\s*[$€£¥]?\s*(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2}))')
        tax_amount = extract_amount(text, r'(?i)(?:tax|vat|gst|hst|sales\s*tax)\s*[:\-]?\s*[$€£¥]?\s*(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2}))')
        payment_method = extract_field(text, r'(?i)(?:paid\s*(?:with|by|via)|payment\s*(?:method|type)|(?:credit|debit)\s*card)\s*[:\-]?\s*([A-Za-z0-9\s]+)')
        
        # Extract line items (simplified approach for receipts)
        line_items = extract_receipt_items(text)
        
        return {
            "store_name": store_name,
            "date": date,
            "time": time,
            "total_amount": total_amount,
            "subtotal": subtotal,
            "tax_amount": tax_amount,
            "payment_method": payment_method,
            "line_items": line_items,
            "document_type": "receipt"
        }
    except Exception as e:
        st.error(f"Error extracting receipt data: {str(e)}")
        return None

def extract_field(text, pattern):
    """Extract field using regex pattern"""
    match = re.search(pattern, text)
    return match.group(1).strip() if match else ""

def extract_date(text, pattern):
    """Extract and standardize date"""
    match = re.search(pattern, text)
    if not match:
        return ""
    
    date_str = match.group(1).strip()
    # Try different date formats
    for fmt in ["%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y", "%m-%d-%Y", "%d.%m.%Y", "%m.%d.%Y",
                "%d %b %Y", "%d %B %Y", "%b %d %Y", "%B %d %Y"]:
        try:
            date_obj = datetime.strptime(date_str, fmt)
            return date_obj.strftime("%Y-%m-%d")
        except ValueError:
            continue
    
    return date_str  # Return as is if parsing fails

def extract_amount(text, pattern):
    """Extract and standardize monetary amount"""
    match = re.search(pattern, text)
    if not match:
        return ""
    
    amount_str = match.group(1).strip()
    # Standardize decimal separator
    if ',' in amount_str and '.' in amount_str:
        if amount_str.rindex(',') > amount_str.rindex('.'):
            amount_str = amount_str.replace('.', '')
            amount_str = amount_str.replace(',', '.')
        else:
            amount_str = amount_str.replace(',', '')
    elif ',' in amount_str:
        amount_str = amount_str.replace(',', '.')
    
    try:
        return float(amount_str)
    except ValueError:
        return amount_str

def extract_currency(text):
    """Extract currency symbol or code"""
    currency_patterns = {
        'USD': r'\$|USD|US\s*dollars',
        'EUR': r'€|EUR|euros',
        'GBP': r'£|GBP|pounds',
        'JPY': r'¥|JPY|yen',
        'CAD': r'CAD|Canadian\s*dollars',
        'AUD': r'AUD|Australian\s*dollars',
        'INR': r'₹|INR|rupees'
    }
    
    for currency, pattern in currency_patterns.items():
        if re.search(pattern, text, re.IGNORECASE):
            return currency
    
    return "USD"  # Default

def extract_line_items(text, doc):
    """Extract line items from invoice"""
    # Try to find tables in the document using PyMuPDF
    tables = []
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        tables.extend(page.find_tables())
    
    if tables:
        # Use the first table that looks like line items
        for table in tables:
            df = table.to_pandas()
            if len(df.columns) >= 3 and len(df) > 0:  # At least description, quantity, price
                # Clean up the dataframe
                df = df.applymap(lambda x: str(x).strip() if isinstance(x, str) else x)
                df = df.replace('', np.nan).dropna(how='all').reset_index(drop=True)
                
                if not df.empty:
                    return df.to_dict('records')
    
    # Fallback: Try to extract line items using regex
    items = []
    lines = text.split('\n')
    item_pattern = r'(\d+)\s+([A-Za-z0-9\s.,&\-]+)\s+(\d+(?:[.,]\d+)?)\s+(\d+(?:[.,]\d+)?)\s+(\d+(?:[.,]\d+)?)'  # qty, desc, unit price, total
    
    for i, line in enumerate(lines):
        match = re.search(item_pattern, line)
        if match:
            items.append({
                'quantity': match.group(1),
                'description': match.group(2).strip(),
                'unit_price': match.group(3),
                'total': match.group(5)
            })
    
    return items if items else [{'description': 'No line items detected', 'quantity': '', 'unit_price': '', 'total': ''}]

def extract_receipt_items(text):
    """Extract line items from receipt using OCR text"""
    items = []
    lines = text.split('\n')
    
    # Look for the items section (usually between store header and total)
    item_section = False
    for i, line in enumerate(lines):
        # Skip empty lines
        if not line.strip():
            continue
            
        # Check if this line might be an item
        if re.search(r'\d+(?:[.,]\d{2})$', line.strip()):
            # This line ends with a price, likely an item
            item_section = True
            
            # Try to extract quantity, description and price
            parts = re.split(r'\s{2,}', line.strip())
            if len(parts) >= 2:
                # Last part is likely the price
                price = parts[-1]
                # Rest is description (and possibly quantity)
                desc = ' '.join(parts[:-1])
                
                # Try to extract quantity
                qty_match = re.search(r'^(\d+)\s+x\s+', desc)
                qty = qty_match.group(1) if qty_match else '1'
                desc = re.sub(r'^\d+\s+x\s+', '', desc) if qty_match else desc
                
                items.append({
                    'description': desc.strip(),
                    'quantity': qty,
                    'price': price
                })
        elif item_section and re.search(r'(?i)total|subtotal|tax', line):
            # We've reached the end of items section
            break
    
    return items if items else [{'description': 'No line items detected', 'quantity': '', 'price': ''}]

def detect_fraud(data):
    """Simple fraud detection logic"""
    fraud_indicators = 0
    max_indicators = 7
    reasons = []
    
    # Check if vendor is in our database
    vendor_name = data.get('vendor', '') or data.get('store_name', '')
    if vendor_name:
        if vendor_name not in st.session_state.vendors:
            fraud_indicators += 2
            reasons.append("Vendor not in approved database")
        elif st.session_state.vendors[vendor_name]['status'] == 'inactive':
            fraud_indicators += 3
            reasons.append("Vendor marked as inactive")
        elif st.session_state.vendors[vendor_name]['risk_score'] == 'high':
            fraud_indicators += 2
            reasons.append("Vendor has high risk score")
        elif st.session_state.vendors[vendor_name]['risk_score'] == 'medium':
            fraud_indicators += 1
            reasons.append("Vendor has medium risk score")
    
    # Check for missing critical fields
    if data['document_type'] == 'invoice':
        if not data.get('invoice_number'):
            fraud_indicators += 1
            reasons.append("Missing invoice number")
        if not data.get('invoice_date'):
            fraud_indicators += 1
            reasons.append("Missing invoice date")
    else:  # receipt
        if not data.get('date'):
            fraud_indicators += 1
            reasons.append("Missing receipt date")
    
    # Check for suspicious amounts
    if data.get('total_amount') and data.get('subtotal') and data.get('tax_amount'):
        # Convert to float if they're strings
        total = float(data['total_amount']) if isinstance(data['total_amount'], str) else data['total_amount']
        subtotal = float(data['subtotal']) if isinstance(data['subtotal'], str) else data['subtotal']
        tax = float(data['tax_amount']) if isinstance(data['tax_amount'], str) else data['tax_amount']
        
        # Check if total = subtotal + tax (with small margin for rounding errors)
        if abs(total - (subtotal + tax)) > 0.1:
            fraud_indicators += 1
            reasons.append("Total amount doesn't match subtotal + tax")
    
    # Check for round numbers (often suspicious in invoices)
    if data.get('total_amount') and isinstance(data['total_amount'], (int, float)):
        if data['total_amount'] % 100 == 0 and data['total_amount'] > 1000:
            fraud_indicators += 1
            reasons.append("Suspiciously round total amount")
    
    # Determine fraud status
    if fraud_indicators >= 3:
        status = "Fraud"
    elif fraud_indicators >= 1:
        status = "Suspicious"
    else:
        status = "Valid"
    
    return {
        "status": status,
        "score": fraud_indicators,
        "max_score": max_indicators,
        "reasons": reasons
    }

# Main application logic - only runs when authenticated
if st.session_state.authenticated and page == "Dashboard":
    st.markdown("<h1 class='app-header'>Dashboard</h1>", unsafe_allow_html=True)
    
    # Dashboard metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="Documents Analyzed", value="124", delta="12 today")
    with col2:
        st.metric(label="Fraud Detected", value="7", delta="-2 from last week", delta_color="inverse")
    with col3:
        st.metric(label="Active Vendors", value=str(sum(1 for v in st.session_state.vendors.values() if v['status'] == 'active')))
    
    # Recent activity
    st.markdown("### Recent Activity")
    st.dataframe({
        "Date": ["2023-06-01", "2023-06-01", "2023-05-31", "2023-05-31", "2023-05-30"],
        "Document": ["Invoice #12345", "Receipt #R-789", "Invoice #12344", "Invoice #12343", "Receipt #R-788"],
        "Vendor": ["Microsoft Corporation", "Office Supplies Inc.", "Fake Supplies Ltd.", "Apple Inc.", "Office Supplies Inc."],
        "Status": ["Valid", "Valid", "Fraud", "Valid", "Suspicious"],
        "Amount": ["$1,200.00", "$85.75", "$4,500.00", "$899.99", "$125.50"]  
    }, use_container_width=True)

elif st.session_state.authenticated and page == "Check Invoice":
    st.markdown("<h1 class='app-header'>Invoice Fraud Detection</h1>", unsafe_allow_html=True)
    st.markdown("Upload an invoice to verify its authenticity against our vendor database.")
    
    # File uploader with improved styling
    st.markdown("### Upload Invoice")
    st.markdown("""<div class='upload-container'>
                <h4>Upload Invoice Document</h4>
                <p>Drag and drop your invoice file, or click to browse</p>
                </div>""", unsafe_allow_html=True)
    uploaded_files = st.file_uploader("Browse Files", 
                                     type=["pdf", "png", "jpg", "jpeg"], 
                                     accept_multiple_files=True,
                                     label_visibility="collapsed")
    
    # Initialize data variable to store the current document data
    data = None
    
    if uploaded_files:
        for file in uploaded_files:
            st.markdown("---")
            st.subheader(f"Analyzing: {file.name}")
            
            # Determine file type and process accordingly
            if file.name.lower().endswith('.pdf'):
                # Try to determine if it's an invoice or receipt based on content
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
                    temp_file.write(file.getvalue())
                    temp_file_path = temp_file.name
                
                # First try as invoice
                with open(temp_file_path, "rb") as f:
                    data = extract_invoice_data(f)
                
                # If invoice extraction failed or returned minimal data, try as receipt
                if not data or (not data.get('invoice_number') and not data.get('vendor')):
                    with open(temp_file_path, "rb") as f:
                        data = extract_receipt_data(f)
                
                # Send alert about scanned invoice if enabled
                if st.session_state.alert_enabled and data:
                    current_time = datetime.now()
                    # Only send alert if it's been more than 1 hour since last alert or if it's the first alert
                    if (st.session_state.last_alert_time is None or 
                        (current_time - st.session_state.last_alert_time).total_seconds() > 3600):
                        st.session_state.last_alert_time = current_time
                        vendor_name = data.get('vendor', '') or data.get('store_name', 'Unknown Vendor')
                        st.toast(f"📧 Alert sent about invoice from {vendor_name}", icon="📊")
                        # In a real application, this would send an actual email or notification
                
                # Clean up temp file
                os.unlink(temp_file_path)
            else:
                # Process as receipt image
                data = extract_receipt_data(file)
            
            if data:
                # Perform fraud detection
                fraud_analysis = detect_fraud(data)
                
                # Display fraud analysis result with appropriate styling
                col1, col2 = st.columns([1, 3])
                with col1:
                    if fraud_analysis["status"] == "Fraud":
                        st.markdown(f"<div class='fraud-alert'>⚠️ {fraud_analysis['status']}</div>", unsafe_allow_html=True)
                    elif fraud_analysis["status"] == "Suspicious":
                        st.markdown(f"<div class='suspicious-alert'>⚠️ {fraud_analysis['status']}</div>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<div class='valid-alert'>✅ {fraud_analysis['status']}</div>", unsafe_allow_html=True)
                
                with col2:
                    st.progress(fraud_analysis["score"] / fraud_analysis["max_score"])
                    if fraud_analysis["reasons"]:
                        st.markdown("**Reasons:**")
                        for reason in fraud_analysis["reasons"]:
                            st.markdown(f"- {reason}")
                
                # Display extracted data based on document type
                if data["document_type"] == "invoice":
                    # Display invoice data
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown("### Invoice Details")
                        st.markdown(f"**Invoice Number:** {data['invoice_number']}")
                        st.markdown(f"**Invoice Date:** {data['invoice_date']}")
                        st.markdown(f"**Due Date:** {data['due_date']}")
                        st.markdown(f"**Vendor:** {data['vendor']}")
                        st.markdown(f"**Customer:** {data['customer']}")
                    
                    with col2:
                        st.markdown("### Financial Details")
                        st.markdown(f"**Total Amount:** {data['currency']} {data['total_amount']}")
                        st.markdown(f"**Subtotal:** {data['currency']} {data['subtotal']}")
                        st.markdown(f"**Tax Amount:** {data['currency']} {data['tax_amount']}")
                    
                    # Display line items
                    st.markdown("### Line Items")
                    if data['line_items'] and isinstance(data['line_items'], list):
                        df = pd.DataFrame(data['line_items'])
                        st.dataframe(df, use_container_width=True)
                    else:
                        st.info("No line items detected or could not parse table structure.")
                
                else:  # receipt
                    # Display receipt data
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown("### Receipt Details")
                        st.markdown(f"**Store:** {data['store_name']}")
                        st.markdown(f"**Date:** {data['date']}")
                        st.markdown(f"**Time:** {data['time']}")
                        st.markdown(f"**Payment Method:** {data['payment_method']}")
                    
                    with col2:
                        st.markdown("### Financial Details")
                        st.markdown(f"**Total Amount:** {data['total_amount']}")
                        st.markdown(f"**Subtotal:** {data['subtotal']}")
                        st.markdown(f"**Tax Amount:** {data['tax_amount']}")
                    
                    # Display line items
                    st.markdown("### Items Purchased")
                    if data['line_items'] and isinstance(data['line_items'], list):
                        df = pd.DataFrame(data['line_items'])
                        st.dataframe(df, use_container_width=True)
                    else:
                        st.info("No line items detected or could not parse receipt items.")
            else:
                st.error("Failed to extract data from this document. Please check the file format.")
    else:
        # Display sample message when no files are uploaded
        st.info("Please upload invoice PDFs or receipt images/PDFs to begin analysis.")
    
    # AI Chatbot for invoice questions
    st.markdown("---")
    st.markdown("<h2 style='color: #4CAF50;'>AI Invoice Assistant</h2>", unsafe_allow_html=True)
    st.markdown("Ask questions about the current invoice or general invoice processing.")
    
    # Chat container for history
    chat_container = st.container()
    
    # Add a border and styling to the chat interface
    st.markdown("""
    <style>
    .chat-container {
        border: 1px solid #4a4a4a;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 15px;
        background-color: #1E1E1E;
    }
    .chat-message-user {
        background-color: #2e7d32;
        color: white;
        padding: 10px 15px;
        border-radius: 15px 15px 0 15px;
        margin-bottom: 10px;
        max-width: 80%;
        margin-left: auto;
        box-shadow: 0 1px 2px rgba(0,0,0,0.2);
    }
    .chat-message-ai {
        background-color: #263238;
        color: white;
        padding: 10px 15px;
        border-radius: 15px 15px 15px 0;
        margin-bottom: 15px;
        max-width: 80%;
        box-shadow: 0 1px 2px rgba(0,0,0,0.2);
    }
    .chat-input {
        display: flex;
        margin-top: 15px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Chat input with improved styling
    col1, col2 = st.columns([5, 1])
    with col1:
        user_query = st.text_input("Your question:", key="user_query", placeholder="Type your question here...")
    with col2:
        submit_button = st.button("Ask AI", key="submit_query", use_container_width=True)
    
    # Initialize a session state variable for form submission if it doesn't exist
    if 'form_submitted' not in st.session_state:
        st.session_state.form_submitted = False
    
    # Process the query when submitted
    if submit_button and user_query:
        # Get AI response
        ai_response = get_ai_response(user_query, data)
        
        # Add to chat history
        st.session_state.chat_history.append({"user": user_query, "ai": ai_response})
        
        # Set form submitted flag instead of directly modifying the input widget
        st.session_state.form_submitted = True
        st.rerun()
    
    # Clear the input box after rerun if form was submitted
    if st.session_state.form_submitted:
        st.session_state.form_submitted = False
    
    # Display chat history in reverse order (newest at the bottom)
    with chat_container:
        st.markdown("<div class='chat-container'>", unsafe_allow_html=True)
        
        # If no chat history, show a welcome message
        if not st.session_state.chat_history:
            st.markdown("<div class='chat-message-ai'>👋 Hello! I'm your invoice assistant. Upload an invoice and ask me questions about it, or ask general questions about invoice processing.</div>", unsafe_allow_html=True)
        else:
            for chat in st.session_state.chat_history:
                st.markdown(f"<div class='chat-message-user'><strong>You:</strong> {chat['user']}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='chat-message-ai'><strong>AI Assistant:</strong> {chat['ai']}</div>", unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)

elif st.session_state.authenticated and page == "Manage Vendors":
    st.markdown("<h1 class='app-header'>Manage Vendors</h1>", unsafe_allow_html=True)
    st.markdown("Add, edit, or remove vendors from your approved vendor database.")
    
    # Add new vendor form
    with st.expander("Add New Vendor", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            new_vendor_name = st.text_input("Vendor Name")
        with col2:
            new_vendor_status = st.selectbox("Status", ["active", "inactive"])
            new_vendor_risk = st.selectbox("Risk Score", ["low", "medium", "high"])
        
        if st.button("Add Vendor"):
            if new_vendor_name:
                if new_vendor_name in st.session_state.vendors:
                    st.warning(f"Vendor '{new_vendor_name}' already exists.")
                else:
                    st.session_state.vendors[new_vendor_name] = {
                        'status': new_vendor_status,
                        'risk_score': new_vendor_risk
                    }
                    st.success(f"Vendor '{new_vendor_name}' added successfully.")
            else:
                st.error("Please enter a vendor name.")
    
    # Display and edit existing vendors
    st.markdown("### Current Vendors")
    
    # Convert vendors dictionary to DataFrame for display
    vendors_data = []
    for name, details in st.session_state.vendors.items():
        vendors_data.append({
            "Vendor Name": name,
            "Status": details['status'],
            "Risk Score": details['risk_score'],
            "Actions": name  # We'll use this to identify which vendor to edit/delete
        })
    
    vendors_df = pd.DataFrame(vendors_data)
    
    # Display vendors in a styled dataframe
    if not vendors_df.empty:
        # Create columns for each vendor with edit/delete buttons
        for i, row in vendors_df.iterrows():
            col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])
            
            with col1:
                st.markdown(f"**{row['Vendor Name']}**")
            
            with col2:
                status_color = "green" if row['Status'] == "active" else "red"
                st.markdown(f"<span style='color:{status_color};'>{row['Status']}</span>", unsafe_allow_html=True)
            
            with col3:
                risk_color = "green" if row['Risk Score'] == "low" else "orange" if row['Risk Score'] == "medium" else "red"
                st.markdown(f"<span style='color:{risk_color};'>{row['Risk Score']}</span>", unsafe_allow_html=True)
            
            with col4:
                if st.button("Edit", key=f"edit_{row['Actions']}"):
                    st.session_state.edit_vendor = row['Vendor Name']
            
            with col5:
                if st.button("Delete", key=f"delete_{row['Actions']}"):
                    if row['Vendor Name'] in st.session_state.vendors:
                        del st.session_state.vendors[row['Vendor Name']]
                        st.rerun()
            
            # If this vendor is being edited, show the edit form
            if 'edit_vendor' in st.session_state and st.session_state.edit_vendor == row['Vendor Name']:
                with st.form(key=f"edit_form_{row['Vendor Name']}"):
                    st.subheader(f"Edit {row['Vendor Name']}")
                    new_status = st.selectbox("Status", ["active", "inactive"], 
                                             index=0 if row['Status'] == "active" else 1)
                    new_risk = st.selectbox("Risk Score", ["low", "medium", "high"],
                                           index=0 if row['Risk Score'] == "low" else 
                                                 1 if row['Risk Score'] == "medium" else 2)
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        submit = st.form_submit_button("Save Changes")
                    with col2:
                        cancel = st.form_submit_button("Cancel")
                    
                    if submit:
                        st.session_state.vendors[row['Vendor Name']] = {
                            'status': new_status,
                            'risk_score': new_risk
                        }
                        del st.session_state.edit_vendor
                        st.rerun()
                    
                    if cancel:
                        del st.session_state.edit_vendor
                        st.rerun()
            
            st.markdown("---")
    else:
        st.info("No vendors in the database. Add vendors using the form above.")
    
elif st.session_state.authenticated and page == "Settings":
    st.markdown("<h1 class='app-header'>Settings</h1>", unsafe_allow_html=True)
    
    # OCR Status
    st.subheader("OCR Configuration")
    if st.session_state.tesseract_available:
        st.success(st.session_state.tesseract_message)
    else:
        st.error(st.session_state.tesseract_message)
        st.markdown("""
        To enable OCR functionality, please install Tesseract OCR:
        1. Download from [UB-Mannheim/tesseract](https://github.com/UB-Mannheim/tesseract/releases)
        2. Install with default options
        3. Restart this application
        """)
    
    # Alert settings
    st.subheader("Alert Settings")
    st.session_state.alert_enabled = st.toggle("Enable Fraud Alerts", value=st.session_state.alert_enabled)
    
    # Application settings
    st.subheader("Application Settings")
    st.info("Additional application settings can be configured here in future updates.")