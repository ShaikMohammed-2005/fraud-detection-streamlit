# fraud-detection-streamlit
Streamlit app for invoice fraud detection using AI
veripay-fraud-detection/
│── app.py                 # Your main Streamlit app (the one you uploaded)
│── requirements.txt       # Python dependencies
│── README.md              # Project documentation
│── data/                  # (Optional) Sample invoices/receipts for testing
│── .gitignore             # Ignore unnecessary files

requirements.txt

streamlit
pdfplumber
pymupdf
pytesseract
pillow
pandas


# 📄 VeriPay – AI-Powered Fraud Detection for Invoices & Receipts

VeriPay is a **Streamlit-based web app** that extracts key details from invoices & receipts, and flags them as **valid, suspicious, or fraudulent** using AI-powered heuristics & OCR.

## 🚀 Features
- Upload **PDF or image files** of invoices/receipts.
- Automatic **OCR extraction** (via PyMuPDF, pdfplumber & Tesseract).
- Detects and parses:
  - Invoice Number, Dates, Vendor/Customer
  - Subtotal, Tax, Total Amount
  - Line Items Table
- **Fraud Detection** 🔍
  - Flags anomalies such as:
    - Mismatched totals
    - Invalid vendors
    - Duplicate invoice IDs
    - Suspicious patterns
- Beautiful **dark theme UI**.

---

## 🛠️ Installation

Clone this repo and install dependencies:

```bash
git clone https://github.com/your-username/veripay-fraud-detection.git
cd veripay-fraud-detection
pip install -r requirements.txt

to run the app : streamlit run app.py

