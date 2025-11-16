# 🔗 SHARED RESOURCES

This section contains **shared resources** used by both User and Librarian systems.

## 📂 Contents

### `instance/`
- **`pustak_tracker.db`** - Main SQLite database
- Contains all books, users, transactions, and system data
- Shared by both mobile app and web interface

### `barcodes/`
- **Generated barcode images** for library books
- Used by both scanning systems

### Configuration Files
- **`.env`** - Environment variables and configuration
- **`env.example`** - Template for environment setup
- **`requirements.txt`** - Python dependencies list
- **`.gitignore`** - Git ignore patterns

## 🔧 Setup Instructions

### 1. Environment Configuration
```bash
cp env.example .env
# Edit .env with your specific settings
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Database Setup
The database file `instance/pustak_tracker.db` is automatically created when you first run either system.

## 📋 Important Notes

- **Database Location**: Both systems reference `../03_SHARED_RESOURCES/instance/pustak_tracker.db`
- **Environment Variables**: Both systems load from `../03_SHARED_RESOURCES/.env`
- **Barcodes**: Generated barcodes are stored in `barcodes/` folder
- **Security**: Keep `.env` file secure and never commit to version control

## 🔄 Usage by Systems

### User Mobile App
- Reads database for book data and user authentication
- Uses environment variables for API configuration

### Librarian System
- Full read/write access to database
- Generates barcodes stored in shared folder
- Uses SSL certificates for secure connections
