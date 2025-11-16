# Pustak Tracker - Library Management System

A comprehensive library management system with a Flutter mobile app and Flask backend API.

## 📋 Table of Contents

- [Features](#features)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Setup Instructions](#setup-instructions)
  - [Backend Setup](#backend-setup)
  - [Mobile App Setup](#mobile-app-setup)
- [Running the Application](#running-the-application)
- [API Endpoints](#api-endpoints)
- [Database Schema](#database-schema)
- [Troubleshooting](#troubleshooting)

## ✨ Features

### Mobile App (Flutter)
- User authentication with JWT tokens
- Browse available books
- View borrowed books with due dates
- Track fines and overdue books
- View notifications
- User profile management
- Modern, responsive UI with Material Design 3

### Backend API (Flask)
- RESTful API with JWT authentication
- User management
- Book catalog management
- Transaction tracking (issue/return)
- Fine calculation
- Notification system
- SQLite database

## 📁 Project Structure

```
LIBRARY MANAGEMENT/
├── library_backend/           # Flask backend API for mobile app
│   ├── app.py                 # Main Flask application
│   ├── run.py                 # Server startup script
│   ├── requirements.txt       # Python dependencies
│   ├── START_BACKEND.bat      # Windows startup script
│   └── venv/                  # Python virtual environment
├── flutter_library_app/       # Flutter mobile application
│   ├── lib/
│   │   ├── main.dart          # App entry point
│   │   ├── app.dart           # Main app widget
│   │   ├── core/              # Core utilities (config, theme, utils)
│   │   ├── data/              # Data layer (models, repositories, services)
│   │   ├── providers/         # State management (Provider)
│   │   ├── routes/            # Navigation routing
│   │   ├── screens/           # UI screens
│   │   └── widgets/           # Reusable widgets
│   ├── pubspec.yaml           # Flutter dependencies
│   └── android/               # Android platform files
├── app/                       # Flask web application (admin panel)
│   ├── models.py              # Database models
│   ├── routes/                # Web routes
│   └── frontend/              # HTML templates
├── instance/
│   └── pustak_tracker.db      # SQLite database (main database)
└── README.md                  # This file
```

## 🔧 Prerequisites

### Backend
- Python 3.8 or higher
- pip (Python package manager)

### Mobile App
- Flutter SDK 3.0 or higher
- Dart 3.0 or higher
- Android Studio / VS Code with Flutter extensions
- Android SDK (API 21+)
- Physical device or emulator

## 🚀 Setup Instructions

### Backend Setup

1. **Navigate to backend directory:**
   ```bash
   cd library_backend
   ```

2. **Create virtual environment (recommended):**
   ```bash
   python -m venv venv
   ```

3. **Activate virtual environment:**
   - Windows:
     ```bash
     venv\Scripts\activate
     ```
   - macOS/Linux:
     ```bash
     source venv/bin/activate
     ```

4. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

5. **Verify database exists:**
   - The database file should be at: `../instance/pustak_tracker.db`
   - If it doesn't exist, the app will create it automatically

### Mobile App Setup

1. **Navigate to mobile app directory:**
   ```bash
   cd flutter_library_app
   ```

2. **Install Flutter dependencies:**
   ```bash
   flutter pub get
   ```

3. **Update API configuration:**
   - Open `lib/core/config/api_config.dart`
   - Update `baseUrl` with your backend server IP address:
     ```dart
     static const String baseUrl = 'http://YOUR_IP_ADDRESS:5001/api';
     ```
   - To find your IP address:
     - Windows: Run `ipconfig` and look for IPv4 Address
     - macOS/Linux: Run `ifconfig` or `ip addr`
   - For Android Emulator: Use `http://10.0.2.2:5001/api`
   - For Physical Device: Use your computer's IP (e.g., `http://192.168.1.100:5001/api`)

4. **Connect device or start emulator:**
   - For Android: Start Android emulator or connect physical device
   - Enable USB debugging on physical device

## ▶️ Running the Application

### Start Backend Server

1. **Navigate to backend directory:**
   ```bash
   cd library_backend
   ```

2. **Activate virtual environment** (if not already active):
   - Windows: `venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`

3. **Run the server:**
   ```bash
   python run.py
   ```
   
   Or on Windows:
   ```bash
   START_BACKEND.bat
   ```

4. **Server will start on:**
   - URL: `http://0.0.0.0:5001`
   - API Base: `http://YOUR_IP:5001/api`
   - The console will display the exact URLs to use
   - Default port: **5001** (not 5000)

### Run Mobile App

1. **Navigate to mobile app directory:**
   ```bash
   cd flutter_library_app
   ```

2. **Run the app:**
   ```bash
   flutter run
   ```

3. **Or use your IDE:**
   - Android Studio: Click the Run button
   - VS Code: Press F5 or use Run menu

4. **Build release APK (optional):**
   ```bash
   flutter build apk --release
   ```

## 🔌 API Endpoints

### Authentication
- `POST /api/auth/login` - User login
  - Body: `{ "email": "user@example.com", "password": "password" }`
  - Returns: `{ "success": true, "token": "...", "user": {...} }`

### User Endpoints (Require JWT Token)
- `GET /api/user/profile` - Get user profile
- `GET /api/user/borrowed-books` - Get user's borrowed books
- `GET /api/user/fines` - Get user's fines
- `GET /api/user/notifications` - Get user's notifications
- `GET /api/user/dashboard-stats` - Get dashboard statistics
- `PUT /api/user/notifications/<id>/read` - Mark notification as read

### Book Endpoints (Require JWT Token)
- `GET /api/books/available` - Get all available books
- `GET /api/books/search?query=<query>` - Search books

### Health Check
- `GET /api/health` - Server health check

**Note:** All endpoints except `/api/auth/login` and `/api/health` require JWT token in Authorization header:
```
Authorization: Bearer <your_token>
```

## 🗄️ Database Schema

The main database (`instance/pustak_tracker.db`) contains:

- **users** - User accounts (id, name, email, password_hash, role)
- **books** - Book catalog (id, title, author, publisher, isbn, category_id, total_copies, available_copies)
- **categories** - Book categories (id, name, description)
- **transactions** - Book transactions (id, user_id, book_id, issue_date, due_date, return_date, status, fine_amount)
- **reservations** - Book reservations (id, user_id, book_id, status, created_at)
- **fines** - Fine records (id, user_id, amount, reason, date, status)
- **notifications** - User notifications (id, user_id, title, body, type, seen, created_at)

## 🐛 Troubleshooting

### Backend Issues

1. **Port already in use:**
   - Change port in `run.py` (line 16) or stop the process using port 5001

2. **Database errors:**
   - Ensure `instance/pustak_tracker.db` exists
   - Check file permissions

3. **JWT token errors (422 errors):**
   - This is fixed - tokens now use string identity
   - If still occurring, restart backend server
   - Clear app data and login again

4. **CORS errors:**
   - Verify CORS is enabled in `app.py`
   - Check that API URL in mobile app matches backend URL

### Mobile App Issues

1. **Cannot connect to backend:**
   - Verify backend is running on port 5001
   - Check API URL in `api_config.dart` matches backend
   - Ensure device/emulator can reach backend IP
   - For Android emulator: Use `http://10.0.2.2:5001/api`
   - For physical device: Use your computer's IP (e.g., `http://192.168.1.100:5001/api`)
   - Test backend with: `curl http://YOUR_IP:5001/api/health`

2. **Build errors:**
   - Run `flutter clean`
   - Run `flutter pub get`
   - Delete `build/` folder and rebuild
   - Check for syntax errors in Dart files

3. **Dependencies issues:**
   - Run `flutter pub upgrade`
   - Check `pubspec.yaml` for version conflicts
   - Ensure Flutter SDK version is compatible

4. **Yellow/Black error lines (Dart errors):**
   - All debug print statements have been removed
   - Check for any remaining syntax errors
   - Run `flutter analyze` to check for issues

### Common Solutions

- **Clear Flutter build cache:**
  ```bash
  cd flutter_library_app
  flutter clean
  flutter pub get
  ```

- **Restart backend server:**
  - Stop the server (Ctrl+C)
  - Activate virtual environment
  - Run `python run.py` again

- **Check network connectivity:**
  - Ping backend server from device/emulator
  - Verify firewall settings
  - Check if backend is accessible from mobile device

## 📝 Important Notes

- **Database:** The main database is `instance/pustak_tracker.db` - this is the single source of truth
- **Backend Port:** Default port is **5001** (configured in `run.py`)
- **JWT Tokens:** Expire after 7 days, use string identity (Flask-JWT-Extended 4.x requirement)
- **API Base URL:** Configure in `flutter_library_app/lib/core/config/api_config.dart`
- **Security:** All passwords are hashed using Werkzeug
- **Network:** Mobile app requires network connection to backend server
- **Database Schema:** Uses `transactions` table (not `borrowed_books`) for book loans

## 👥 User Accounts

User accounts are stored in the database. To create a new user:
- Use the web admin panel at `http://YOUR_IP:5000` (web app)
- Or use database management tools
- Users with role 'user' can login to the mobile app
- Users with role 'librarian' can only access the web admin panel

## 📄 License

This project is part of the Pustak Tracker Library Management System.

---

**For support or issues, please check the troubleshooting section or review the code comments.**
