# 🏛️ LIBRARIAN SYSTEM

This folder contains all components for the **Librarian Management System** - everything librarians need in one place.

## 📂 Direct Contents

### Main Web Application
- **`app/`** - Complete Flask web application for library management
- **`run.py`** - Main server startup script

### Utility Scripts
- **`get_ids.py`** - Database ID extraction utility
- **`view_database.py`** - Database inspection tool
- **`barcode_generator.py`** - Generate barcodes for library books

### Mobile Scanner Tools
- **`mobile_scanner.html`** - Web-based barcode scanner interface
- **`mobile_server_https.py`** - HTTPS server for mobile scanning

### SSL Certificates
- **`cert.pem`** - SSL certificate for HTTPS
- **`key.pem`** - SSL private key

## 🚀 Quick Start

### Start Main Web Interface
```bash
python run.py
```

### Run Mobile Scanner
```bash
python mobile_server_https.py
```

### Use Utilities
```bash
python view_database.py        # View database contents
python barcode_generator.py    # Generate barcodes
python get_ids.py             # Extract IDs
```

## 🔗 Dependencies
- Shared database: `../03_SHARED_RESOURCES/instance/`
- Environment config: `../03_SHARED_RESOURCES/.env`

## 👥 Target Users
- **Librarians** - Complete library management
- **Administrators** - System maintenance and reports

## 📋 Features
- Book management, user management, transactions
- Real-time fine calculations
- Barcode generation and scanning
- Comprehensive reporting
- Secure HTTPS access
