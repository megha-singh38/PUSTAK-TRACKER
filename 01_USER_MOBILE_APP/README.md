# 📱 USER MOBILE APP

This section contains all components for the **User Mobile Application**.

## 📂 Contents

### `flutter_library_app/`
- **Flutter Mobile App** for library users
- Features: Book browsing, borrowing, notifications, profile management
- Platform: Android (iOS removed for this project)
- Custom Pustak Tracker branding and logo

### `library_backend/`
- **Backend API Server** for mobile app
- Handles user authentication, book data, transactions
- Provides REST API endpoints for mobile app communication

## 🚀 Quick Start

### Mobile App (Flutter)
```bash
cd flutter_library_app
flutter pub get
flutter run
```

### Backend Server
```bash
cd library_backend
python app.py
```

## 🔗 Dependencies
- Shared database: `../03_SHARED_RESOURCES/instance/`
- Environment config: `../03_SHARED_RESOURCES/.env`

## 👥 Target Users
- **Library Members** - Browse and borrow books
- **Students** - Access library resources on mobile
