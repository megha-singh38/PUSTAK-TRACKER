# 📚 PUSTAK TRACKER - Library Management System

## 🏗️ Project Structure

This project is organized into **3 main categories** for better maintainability and clarity:

```
📁 LIBRARY MANAGEMENT/
├── 📱 01_USER_MOBILE_APP/          # Mobile app for library users
│   ├── flutter_library_app/        # Flutter mobile application
│   ├── library_backend/            # Backend API for mobile app
│   └── README.md
│
├── 🏛️ 02_LIBRARIAN_SYSTEM/         # All librarian tools in one place
│   ├── app/                        # Flask web application
│   ├── run.py                      # Main server startup
│   ├── get_ids.py                  # Database utilities
│   ├── view_database.py            # Database inspection
│   ├── barcode_generator.py        # Barcode generation
│   ├── mobile_scanner.html         # Web barcode scanner
│   ├── mobile_server_https.py      # HTTPS scanner server
│   ├── cert.pem                    # SSL certificate
│   ├── key.pem                     # SSL private key
│   └── README.md
│
├── 🔗 03_SHARED_RESOURCES/         # Shared data and config
│   ├── instance/                   # Database files
│   ├── barcodes/                   # Generated barcodes
│   ├── .env                        # Environment config
│   ├── env.example                 # Config template
│   ├── requirements.txt            # Dependencies
│   ├── .gitignore                  # Git ignore
│   └── README.md
│
├── README.md                       # Original project README
└── PROJECT_STRUCTURE.md           # This file
```

## 🎯 System Categories

### 📱 **01_USER_MOBILE_APP** 
**Target Users**: Library members, students
- Flutter mobile application for Android
- Backend API server
- Features: Browse books, borrow/return, notifications, profile

### 🏛️ **02_LIBRARIAN_SYSTEM**
**Target Users**: Librarians, administrators  
- Web-based management interface
- Administrative utilities
- Mobile barcode scanning tools
- SSL certificates for secure access

### 🔗 **03_SHARED_RESOURCES**
**Shared by both systems**
- SQLite database (`pustak_tracker.db`)
- Configuration files
- Generated barcode images
- Dependencies and environment setup

## 🚀 Quick Start Guide

### 1. Setup Shared Resources
```bash
cd 03_SHARED_RESOURCES
cp env.example .env
pip install -r requirements.txt
```

### 2. Start Librarian Web System
```bash
cd 02_LIBRARIAN_SYSTEM
python run.py
```

### 3. Start Mobile App Backend
```bash
cd 01_USER_MOBILE_APP/library_backend
python app.py
```

### 4. Run Flutter Mobile App
```bash
cd 01_USER_MOBILE_APP/flutter_library_app
flutter pub get
flutter run
```

## 🔧 Key Features

- **Dual Interface**: Web for librarians, Mobile for users
- **Shared Database**: Single source of truth
- **Barcode System**: Generate and scan book barcodes
- **Real-time Updates**: Automatic fine calculations
- **Secure Access**: SSL certificates and JWT authentication
- **Modern UI**: Flutter mobile app with custom branding

## 📋 Dependencies

- **Python 3.8+** for backend systems
- **Flutter 3.0+** for mobile app
- **SQLite** for database
- **SSL certificates** for HTTPS

## 🔒 Security Notes

- Keep `.env` files secure
- SSL certificates in `02_LIBRARIAN_SYSTEM/certificates/`
- JWT authentication for API access
- Role-based access control (User/Librarian)

---

**Project**: Pustak Tracker Library Management System  
**Structure**: Organized by user roles and functionality  
**Maintainability**: Clear separation of concerns
