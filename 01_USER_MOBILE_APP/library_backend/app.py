from flask import Flask, request, jsonify, Blueprint
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from datetime import datetime, timedelta
import sqlite3
import bcrypt
import os
import socket

app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = 'your-secret-key-change-in-production'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=7)
app.config['JWT_ALGORITHM'] = 'HS256'
# Configure JWT to look for tokens in headers (must be before JWTManager)
# Flask-JWT-Extended 4.x requires explicit configuration
app.config['JWT_TOKEN_LOCATION'] = ['headers']
app.config['JWT_HEADER_NAME'] = 'Authorization'
app.config['JWT_HEADER_TYPE'] = 'Bearer'

jwt = JWTManager(app)

# JWT error handlers
@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return jsonify({'error': 'Token has expired'}), 401

@jwt.invalid_token_loader
def invalid_token_callback(error):
    return jsonify({'error': 'Invalid token. Please login again.'}), 422

@jwt.unauthorized_loader
def missing_token_callback(error):
    return jsonify({'error': 'Authorization token is missing'}), 401

# CORS configuration - allow all origins and methods for API
CORS(app, resources={r"/api/*": {
    "origins": "*",
    "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    "allow_headers": ["Content-Type", "Authorization"],
    "expose_headers": ["Content-Type"]
}})

# Create API blueprint
api_bp = Blueprint('api', __name__, url_prefix='/api')

# Database setup
import os
DATABASE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '03_SHARED_RESOURCES', 'instance', 'pustak_tracker.db')

def init_db():
    """Initialize the database with required tables"""
    # Ensure instance directory exists
    os.makedirs(os.path.dirname(DATABASE), exist_ok=True)
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            membership_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Books table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            category TEXT NOT NULL,
            description TEXT,
            cover_url TEXT,
            total_copies INTEGER NOT NULL DEFAULT 1,
            available_copies INTEGER NOT NULL DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Borrowed books table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS borrowed_books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            book_id INTEGER NOT NULL,
            issue_date DATE NOT NULL,
            due_date DATE NOT NULL,
            return_date DATE,
            status TEXT NOT NULL DEFAULT 'active',
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (book_id) REFERENCES books(id)
        )
    ''')
    
    # Reservations table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reservations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            book_id INTEGER NOT NULL,
            reserved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT NOT NULL DEFAULT 'pending',
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (book_id) REFERENCES books(id)
        )
    ''')
    
    # Fines table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS fines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            borrowed_book_id INTEGER,
            amount REAL NOT NULL,
            reason TEXT NOT NULL,
            date DATE NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (borrowed_book_id) REFERENCES borrowed_books(id)
        )
    ''')
    
    # Notifications table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            body TEXT NOT NULL,
            type TEXT NOT NULL,
            seen BOOLEAN NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    conn.commit()
    conn.close()
    
    # Create default admin user and sample books
    create_default_data()

def create_default_data():
    """Create default user and sample books"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Skip creating default data - main database already has it
    conn.close()
    return
    
    # Check if books exist
    cursor.execute('SELECT id FROM books LIMIT 1')
    if not cursor.fetchone():
        # Create sample books
        sample_books = [
            ('The Great Gatsby', 'F. Scott Fitzgerald', 'Fiction', 'A classic American novel', None, 5, 5),
            ('To Kill a Mockingbird', 'Harper Lee', 'Fiction', 'A gripping tale of racial injustice', None, 3, 3),
            ('1984', 'George Orwell', 'Fiction', 'Dystopian novel', None, 4, 4),
            ('A Brief History of Time', 'Stephen Hawking', 'Science', 'Exploring the universe', None, 2, 2),
            ('Sapiens', 'Yuval Noah Harari', 'History', 'A brief history of humankind', None, 3, 3),
            ('The Diary of a Young Girl', 'Anne Frank', 'Biography', 'A powerful account of the Holocaust', None, 2, 2),
        ]
        
        cursor.executemany('''
            INSERT INTO books (title, author, category, description, cover_url, total_copies, available_copies)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', sample_books)
        conn.commit()
    
    conn.close()

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# Authentication routes
@api_bp.route('/auth/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id, name, email, password_hash, role FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()
        conn.close()
        
        if not user:
            return jsonify({'error': 'Invalid email or password'}), 401
        
        # Get user data
        user_id = user[0]
        user_name = user[1]
        user_email = user[2]
        user_password_hash = user[3]
        user_role = user[4] if len(user) > 4 else 'user'
        
        # Check if user role is 'user' (block librarians)
        if user_role != 'user':
            return jsonify({'error': 'Access denied. Only users can login to mobile app'}), 403
        
        # Check password using password_hash column (main database uses werkzeug)
        from werkzeug.security import check_password_hash
        
        if not check_password_hash(user_password_hash, password):
            return jsonify({'error': 'Invalid email or password'}), 401
        
        # Create access token - Flask-JWT-Extended 4.x requires identity to be a string
        access_token = create_access_token(identity=str(user_id))
        
        return jsonify({
            'success': True,
            'token': access_token,
            'user': {
                'id': user_id,
                'name': user_name,
                'email': user_email,
                'membership_id': None
            }
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# User routes
@api_bp.route('/user/profile', methods=['GET', 'OPTIONS'])
@jwt_required()
def get_user_profile():
    try:
        user_id_str = get_jwt_identity()
        user_id = int(user_id_str)  # Convert string back to int
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id, name, email, membership_id FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        conn.close()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'user': {
                'id': user['id'],
                'name': user['name'],
                'email': user['email'],
                'membership_id': user['membership_id']
            }
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/user/borrowed-books', methods=['GET', 'OPTIONS'])
@jwt_required()
def get_borrowed_books():
    try:
        user_id_str = get_jwt_identity()
        user_id = int(user_id_str)  # Convert string back to int
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                t.id,
                t.issue_date,
                t.due_date,
                t.status,
                t.fine_amount,
                b.id as book_id,
                b.title,
                b.author,
                b.publisher,
                b.isbn,
                b.total_copies,
                b.available_copies,
                c.name as category
            FROM transactions t
            JOIN books b ON t.book_id = b.id
            LEFT JOIN categories c ON b.category_id = c.id
            WHERE t.user_id = ? AND t.status IN ('issued', 'overdue')
            ORDER BY t.due_date ASC
        ''', (user_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        books = []
        for row in rows:
            books.append({
                'id': row[0],
                'book': {
                    'id': row[5],
                    'title': row[6],
                    'author': row[7],
                    'category': row[12] or 'Unknown',
                    'description': f'Publisher: {row[8]}',
                    'cover_url': None,
                    'total_copies': row[10],
                    'available_copies': row[11]
                },
                'issue_date': str(row[1]),
                'due_date': str(row[2]),
                'status': row[3]
            })
        
        return jsonify({'books': books}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/user/fines', methods=['GET', 'OPTIONS'])
@jwt_required()
def get_fines():
    try:
        user_id_str = get_jwt_identity()
        user_id = int(user_id_str)  # Convert string back to int
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, amount, reason, date, status
            FROM fines
            WHERE user_id = ?
            ORDER BY date DESC
        ''', (user_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        fines = []
        for row in rows:
            fines.append({
                'id': row['id'],
                'amount': row['amount'],
                'reason': row['reason'],
                'date': row['date'],
                'status': row['status']
            })
        
        return jsonify({'fines': fines}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/user/notifications', methods=['GET'])
@jwt_required()
def get_notifications():
    try:
        user_id_str = get_jwt_identity()
        user_id = int(user_id_str)  # Convert string back to int
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, title, body, type, seen, created_at
            FROM notifications
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT 50
        ''', (user_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        notifications = []
        for row in rows:
            notifications.append({
                'id': row['id'],
                'title': row['title'],
                'body': row['body'],
                'type': row['type'],
                'seen': bool(row['seen']),
                'created_at': row['created_at']
            })
        
        return jsonify({'notifications': notifications}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/user/notifications/<int:notification_id>/read', methods=['PUT'])
@jwt_required()
def mark_notification_as_read(notification_id):
    try:
        user_id_str = get_jwt_identity()
        user_id = int(user_id_str)  # Convert string back to int
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE notifications
            SET seen = 1
            WHERE id = ? AND user_id = ?
        ''', (notification_id, user_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Book routes
@api_bp.route('/books/available', methods=['GET', 'OPTIONS'])
@jwt_required()
def get_available_books():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT b.id, b.title, b.author, b.publisher, b.isbn, b.total_copies, b.available_copies, c.name as category
            FROM books b
            LEFT JOIN categories c ON b.category_id = c.id
            WHERE b.available_copies > 0
            ORDER BY b.title ASC
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        books = []
        for row in rows:
            books.append({
                'id': row[0],
                'title': row[1],
                'author': row[2],
                'category': row[7] or 'Unknown',
                'description': f'Publisher: {row[3]}\nISBN: {row[4]}',
                'cover_url': None,
                'total_copies': row[5],
                'available_copies': row[6]
            })
        
        return jsonify({'books': books}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/books/search', methods=['GET'])
@jwt_required()
def search_books():
    try:
        query = request.args.get('query', '')
        if not query:
            return jsonify({'books': []}), 200
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT b.id, b.title, b.author, b.publisher, b.isbn, b.total_copies, b.available_copies, c.name as category
            FROM books b
            LEFT JOIN categories c ON b.category_id = c.id
            WHERE b.title LIKE ? OR b.author LIKE ? OR c.name LIKE ?
            ORDER BY b.title ASC
        ''', (f'%{query}%', f'%{query}%', f'%{query}%'))
        
        rows = cursor.fetchall()
        conn.close()
        
        books = []
        for row in rows:
            books.append({
                'id': row[0],
                'title': row[1],
                'author': row[2],
                'category': row[7] or 'Unknown',
                'description': f'Publisher: {row[3]}\nISBN: {row[4]}',
                'cover_url': None,
                'total_copies': row[5],
                'available_copies': row[6]
            })
        
        return jsonify({'books': books}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Dashboard stats route
@api_bp.route('/user/dashboard-stats', methods=['GET', 'OPTIONS'])
@jwt_required()
def get_dashboard_stats():
    try:
        user_id_str = get_jwt_identity()
        user_id = int(user_id_str)  # Convert string back to int
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get borrowed books count
        cursor.execute('''
            SELECT COUNT(*) 
            FROM transactions 
            WHERE user_id = ? AND status IN ('issued', 'overdue')
        ''', (user_id,))
        borrowed_count = cursor.fetchone()[0]
        
        # Get overdue books count
        cursor.execute('''
            SELECT COUNT(*) 
            FROM transactions 
            WHERE user_id = ? AND status = 'overdue'
        ''', (user_id,))
        overdue_count = cursor.fetchone()[0]
        
        # Get total fines from transactions
        cursor.execute('''
            SELECT COALESCE(SUM(fine_amount), 0) 
            FROM transactions 
            WHERE user_id = ? AND status IN ('issued', 'overdue')
        ''', (user_id,))
        total_fines = cursor.fetchone()[0] or 0.0
        
        # Also check fines table for pending fines
        cursor.execute('''
            SELECT COALESCE(SUM(amount), 0) 
            FROM fines 
            WHERE user_id = ? AND status = 'pending'
        ''', (user_id,))
        pending_fines = cursor.fetchone()[0] or 0.0
        
        # Use the maximum of transaction fines and fines table
        total_fines = max(float(total_fines), float(pending_fines))
        
        conn.close()
        
        return jsonify({
            'borrowed_count': borrowed_count,
            'overdue_count': overdue_count,
            'total_fines': total_fines
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Health check route
@api_bp.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy'}), 200

def get_local_ip():
    """Get local IP address"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return 'localhost'

# Register blueprint
app.register_blueprint(api_bp)

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)

