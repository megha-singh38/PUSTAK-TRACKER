from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, get_jwt
from werkzeug.security import check_password_hash
from marshmallow import Schema, fields, ValidationError
from ..models import User, Book, Transaction, Category, Reservation
from ..utils import issue_book, return_book, calculate_overdue_fines, get_dashboard_stats
from .. import db, csrf
from datetime import datetime, timedelta
from collections import defaultdict
# In-memory storage for tracking read notifications per user session
user_notification_reads = defaultdict(set)


def _serialize_user_for_app(user: User):
    """Serialize user data in the format expected by the mobile app."""
    membership_id = f"USER{user.id:05d}"
    return {
        'id': user.id,
        'name': user.name,
        'email': user.email,
        'membership_id': membership_id,
    }


def _serialize_book_for_app(book: Book):
    """Serialize book data with fields expected by the mobile app."""
    pending_reservations = Reservation.query.filter_by(
        book_id=book.id, status='pending'
    ).count()
    available = max(0, book.available_copies - pending_reservations)
    return {
        'id': book.id,
        'title': book.title,
        'author': book.author,
        'category': book.category.name if getattr(book, 'category', None) else 'General',
        'available_copies': available,
        'total_copies': book.total_copies,
        'description': book.publisher or 'No description available.',
        'cover_url': None,
    }


def _serialize_transaction_for_app(transaction: Transaction):
    """Serialize transaction details for the mobile app borrowed books view."""
    book = transaction.book
    return {
        'id': transaction.id,
        'book': _serialize_book_for_app(book),
        'issue_date': transaction.issue_date.isoformat() if transaction.issue_date else None,
        'due_date': transaction.due_date.isoformat() if transaction.due_date else None,
        'status': transaction.status,
    }


def _serialize_reservation_for_app(reservation: Reservation):
    """Serialize reservation information to align with borrowed book structure."""
    book = reservation.book
    if not book:
        return {
            'id': reservation.id,
            'book': None,
            'issue_date': reservation.created_at.isoformat(),
            'due_date': (reservation.created_at + timedelta(days=3)).isoformat(),
            'status': 'reserved',
        }
    expected_pickup = reservation.created_at + timedelta(days=3)
    return {
        'id': reservation.id,
        'book': _serialize_book_for_app(book),
        'issue_date': reservation.created_at.isoformat(),
        'due_date': expected_pickup.isoformat(),
        'status': 'reserved',
    }

api_bp = Blueprint('api', __name__)

# Marshmallow Schemas for serialization
class UserSchema(Schema):
    id = fields.Int()
    name = fields.Str()
    email = fields.Str()
    role = fields.Str()
    is_active = fields.Bool()
    created_at = fields.DateTime()

class BookSchema(Schema):
    id = fields.Int()
    title = fields.Str()
    author = fields.Str()
    publisher = fields.Str()
    isbn = fields.Str()
    category_id = fields.Int()
    category_name = fields.Str()
    total_copies = fields.Int()
    available_copies = fields.Int()
    created_at = fields.DateTime()

class TransactionSchema(Schema):
    id = fields.Int()
    user_id = fields.Int()
    user_name = fields.Str()
    book_id = fields.Int()
    book_title = fields.Str()
    issue_date = fields.DateTime()
    due_date = fields.DateTime()
    return_date = fields.DateTime()
    fine_amount = fields.Float()
    status = fields.Str()
    created_at = fields.DateTime()

class CategorySchema(Schema):
    id = fields.Int()
    name = fields.Str()
    description = fields.Str()
    created_at = fields.DateTime()

# Initialize schemas
user_schema = UserSchema()
users_schema = UserSchema(many=True)
book_schema = BookSchema()
books_schema = BookSchema(many=True)
transaction_schema = TransactionSchema()
transactions_schema = TransactionSchema(many=True)
category_schema = CategorySchema()
categories_schema = CategorySchema(many=True)

# Authentication endpoints
@api_bp.route('/auth/login', methods=['POST'])
def api_login():
    data = request.get_json()
    
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Email and password required'}), 400
    
    user = User.query.filter_by(email=data['email']).first()
    
    if user and user.check_password(data['password']) and user.role == 'librarian':
        access_token = create_access_token(identity=user.id, additional_claims={'role': 'librarian'})
        return jsonify({
            'access_token': access_token,
            'user': user_schema.dump(user)
        }), 200
    else:
        return jsonify({'error': 'Invalid credentials'}), 401


# ---------------------------------------------------------------------------
# User Mobile App Endpoints
# ---------------------------------------------------------------------------

@api_bp.route('/user/login', methods=['POST'])
def user_login():
    """Authenticate mobile app users (role=user) and issue JWT."""
    data = request.get_json() or {}

    email = data.get('email', '').strip().lower()
    password = data.get('password', '')

    if not email or not password:
        return jsonify({'error': 'Email and password required'}), 400

    user = User.query.filter_by(email=email).first()

    if not user or not user.check_password(password):
        return jsonify({'error': 'Invalid credentials'}), 401

    if user.role != 'user':
        return jsonify({'error': 'Access restricted to library users'}), 403

    if not user.is_active:
        return jsonify({'error': 'Account is inactive. Contact librarian.'}), 403

    access_token = create_access_token(identity=user.id, additional_claims={'role': 'user'})

    return jsonify({
        'token': access_token,
        'user': _serialize_user_for_app(user)
    }), 200


def _ensure_user_role():
    claims = get_jwt()
    if claims.get('role') != 'user':
        return False
    return True


@api_bp.route('/user/profile', methods=['GET'])
@jwt_required()
def user_profile():
    if not _ensure_user_role():
        return jsonify({'error': 'Access denied'}), 403

    user_id = get_jwt_identity()
    user = User.query.get_or_404(user_id)
    return jsonify({'user': _serialize_user_for_app(user)}), 200


@api_bp.route('/user/borrowed-books', methods=['GET'])
@jwt_required()
def user_borrowed_books():
    if not _ensure_user_role():
        return jsonify({'error': 'Access denied'}), 403

    user_id = get_jwt_identity()
    calculate_overdue_fines()

    transactions = Transaction.query.filter(
        Transaction.user_id == user_id,
        Transaction.status.in_(['issued', 'overdue'])
    ).order_by(Transaction.due_date.asc()).all()

    reservations = Reservation.query.filter_by(
        user_id=user_id, status='pending'
    ).order_by(Reservation.created_at.asc()).all()

    borrowed_items = [_serialize_transaction_for_app(tx) for tx in transactions]
    borrowed_items.extend(_serialize_reservation_for_app(res) for res in reservations)

    return jsonify({'books': borrowed_items}), 200


@api_bp.route('/user/fines', methods=['GET'])
@jwt_required()
def user_fines():
    if not _ensure_user_role():
        return jsonify({'error': 'Access denied'}), 403

    user_id = get_jwt_identity()
    calculate_overdue_fines()

    transactions = Transaction.query.filter(
        Transaction.user_id == user_id,
        Transaction.fine_amount > 0
    ).order_by(Transaction.due_date.desc()).all()

    fines = []
    for tx in transactions:
        status = 'pending' if tx.status in ('issued', 'overdue') else 'paid'
        fines.append({
            'id': tx.id,
            'amount': tx.fine_amount,
            'reason': f"Fine for '{tx.book.title}'",
            'date': (tx.due_date or tx.issue_date or datetime.utcnow()).isoformat(),
            'status': status,
        })

    return jsonify({'fines': fines}), 200


@api_bp.route('/user/notifications', methods=['GET'])
@jwt_required()
def user_notifications():
    if not _ensure_user_role():
        return jsonify({'error': 'Access denied'}), 403

    user_id = get_jwt_identity()
    now = datetime.utcnow()

    notifications = []
    transactions = Transaction.query.filter(
        Transaction.user_id == user_id
    ).all()

    for tx in transactions:
        due_date = tx.due_date
        if not due_date:
            continue

        # Overdue notification
        if tx.status == 'overdue':
            notif_id = tx.id * 10 + 1
            notifications.append({
                'id': notif_id,
                'title': 'Overdue Book',
                'body': f"'{tx.book.title}' is overdue. Please return it as soon as possible.",
                'type': 'overdue',
                'created_at': due_date.isoformat(),
                'seen': notif_id in user_notification_reads[user_id],
            })

        # Due soon reminder (within 3 days)
        if tx.status in ('issued', 'reserved'):
            days_left = (due_date - now).days
            if days_left >= 0 and days_left <= 3:
                notif_id = tx.id * 10 + 2
                notifications.append({
                    'id': notif_id,
                    'title': 'Return Reminder',
                    'body': f"'{tx.book.title}' is due in {days_left} day(s).",
                    'type': 'reminder',
                    'created_at': now.isoformat(),
                    'seen': notif_id in user_notification_reads[user_id],
                })

    reservations = Reservation.query.filter_by(
        user_id=user_id, status='pending'
    ).all()

    for reservation in reservations:
        notif_id = reservation.id * 10 + 5
        notifications.append({
            'id': notif_id,
            'title': 'Reservation Confirmed',
            'body': f"You reserved '{reservation.book.title if reservation.book else 'a book'}'. We will hold it for 3 days.",
            'type': 'reservation',
            'created_at': reservation.created_at.isoformat(),
            'seen': notif_id in user_notification_reads[user_id],
        })

    # Sort notifications by created_at descending
    notifications.sort(key=lambda n: n['created_at'], reverse=True)

    return jsonify({'notifications': notifications}), 200


@api_bp.route('/user/notifications/<int:notification_id>/read', methods=['PUT'])
@jwt_required()
def mark_notification_read(notification_id):
    if not _ensure_user_role():
        return jsonify({'error': 'Access denied'}), 403

    user_id = get_jwt_identity()
    user_notification_reads[user_id].add(notification_id)
    return jsonify({'success': True}), 200


@api_bp.route('/books/available', methods=['GET'])
@jwt_required(optional=True)
def books_available():
    """List books available for users (does not require librarian role)."""
    books = Book.query.filter(Book.available_copies > 0).order_by(Book.title.asc()).all()
    serialized = [_serialize_book_for_app(book) for book in books]
    return jsonify({'books': serialized}), 200


@api_bp.route('/books/search', methods=['GET'])
@jwt_required(optional=True)
def books_search():
    """Search books by title, author, or ISBN for mobile users."""
    query = request.args.get('query', '').strip()

    q = Book.query
    if query:
        like_query = f"%{query}%"
        q = q.filter(
            (Book.title.ilike(like_query)) |
            (Book.author.ilike(like_query)) |
            (Book.isbn.ilike(like_query))
        )

    books = q.order_by(Book.title.asc()).all()
    serialized = [_serialize_book_for_app(book) for book in books]
    return jsonify({'books': serialized}), 200


@api_bp.route('/books/reserve', methods=['POST'])
@jwt_required()
def reserve_book_user():
    if not _ensure_user_role():
        return jsonify({'error': 'Access denied'}), 403

    user_id = get_jwt_identity()
    data = request.get_json() or {}
    book_id = data.get('book_id')

    if not book_id:
        return jsonify({'error': 'book_id is required'}), 400

    book = Book.query.get(book_id)
    if not book:
        return jsonify({'error': 'Book not found'}), 404

    if book.available_copies <= 0:
        return jsonify({'error': 'Book not available for reservation'}), 400

    existing_transaction = Transaction.query.filter(
        Transaction.user_id == user_id,
        Transaction.book_id == book_id,
        Transaction.status.in_(['issued', 'overdue'])
    ).first()

    if existing_transaction:
        return jsonify({'error': 'You already have this book issued or reserved'}), 400

    existing_reservation = Reservation.query.filter_by(
        user_id=user_id, book_id=book_id, status='pending'
    ).first()

    if existing_reservation:
        return jsonify({'error': 'You already have a pending reservation for this book'}), 400

    pending_reservations = Reservation.query.filter_by(
        book_id=book_id, status='pending'
    ).count()

    if (book.available_copies - pending_reservations) <= 0:
        return jsonify({'error': 'All copies are already reserved'}), 400

    try:
        reservation = Reservation(
            user_id=user_id,
            book_id=book_id,
            status='pending'
        )
        db.session.add(reservation)
        db.session.commit()
        return jsonify({'success': True, 'reservation_id': reservation.id}), 200
    except Exception as exc:
        db.session.rollback()
        return jsonify({'error': str(exc)}), 500


@api_bp.route('/books/cancel-reservation/<int:reservation_id>', methods=['DELETE'])
@jwt_required()
def cancel_reservation_user(reservation_id):
    if not _ensure_user_role():
        return jsonify({'error': 'Access denied'}), 403

    user_id = get_jwt_identity()
    reservation = Reservation.query.get_or_404(reservation_id)

    if reservation.user_id != user_id or reservation.status != 'pending':
        return jsonify({'error': 'Reservation not found'}), 404

    try:
        reservation.status = 'cancelled'
        db.session.commit()
        return jsonify({'success': True}), 200
    except Exception as exc:
        db.session.rollback()
        return jsonify({'error': str(exc)}), 500

# Book endpoints
@api_bp.route('/books', methods=['GET'])
@jwt_required()
def get_books():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    search = request.args.get('search', '')
    
    query = Book.query
    if search:
        query = query.filter(
            (Book.title.contains(search)) |
            (Book.author.contains(search)) |
            (Book.isbn.contains(search))
        )
    
    books = query.paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'books': books_schema.dump(books.items),
        'total': books.total,
        'pages': books.pages,
        'current_page': books.page
    })

@api_bp.route('/books', methods=['POST'])
@jwt_required()
def create_book():
    data = request.get_json()
    
    try:
        book = Book(
            title=data['title'],
            author=data['author'],
            publisher=data.get('publisher', ''),
            isbn=data.get('isbn', ''),
            category_id=data['category_id'],
            total_copies=data['total_copies'],
            available_copies=data['total_copies']
        )
        db.session.add(book)
        db.session.commit()
        
        return jsonify(book_schema.dump(book)), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@api_bp.route('/books/<int:book_id>', methods=['GET'])
@jwt_required()
def get_book(book_id):
    book = Book.query.get_or_404(book_id)
    return jsonify(book_schema.dump(book))

@api_bp.route('/books/<int:book_id>', methods=['PUT'])
@jwt_required()
def update_book(book_id):
    book = Book.query.get_or_404(book_id)
    data = request.get_json()
    
    try:
        book.title = data.get('title', book.title)
        book.author = data.get('author', book.author)
        book.publisher = data.get('publisher', book.publisher)
        book.isbn = data.get('isbn', book.isbn)
        book.category_id = data.get('category_id', book.category_id)
        
        # Handle total copies change
        old_total = book.total_copies
        book.total_copies = data.get('total_copies', book.total_copies)
        if book.total_copies > old_total:
            book.available_copies += (book.total_copies - old_total)
        elif book.total_copies < old_total:
            book.available_copies = max(0, book.available_copies - (old_total - book.total_copies))
        
        db.session.commit()
        return jsonify(book_schema.dump(book))
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@api_bp.route('/books/<int:book_id>', methods=['DELETE'])
@jwt_required()
def delete_book(book_id):
    book = Book.query.get_or_404(book_id)
    
    # Check if book has active transactions
    active_transactions = Transaction.query.filter(
        Transaction.book_id == book_id,
        Transaction.status.in_(['issued', 'overdue'])
    ).count()
    
    if active_transactions > 0:
        return jsonify({'error': 'Cannot delete book with active transactions'}), 400
    
    db.session.delete(book)
    db.session.commit()
    return jsonify({'message': 'Book deleted successfully'})

# User endpoints
@api_bp.route('/users', methods=['GET'])
@jwt_required()
def get_users():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    search = request.args.get('search', '')
    
    query = User.query.filter(User.role == 'user')
    if search:
        query = query.filter(
            (User.name.contains(search)) |
            (User.email.contains(search))
        )
    
    users = query.paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'users': users_schema.dump(users.items),
        'total': users.total,
        'pages': users.pages,
        'current_page': users.page
    })

@api_bp.route('/users', methods=['POST'])
@jwt_required()
def create_user():
    data = request.get_json()
    
    # Check if email already exists
    existing_user = User.query.filter_by(email=data['email']).first()
    if existing_user:
        return jsonify({'error': 'Email already exists'}), 400
    
    try:
        user = User(
            name=data['name'],
            email=data['email'],
            role=data.get('role', 'user')
        )
        user.set_password(data['password'])
        db.session.add(user)
        db.session.commit()
        
        return jsonify(user_schema.dump(user)), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@api_bp.route('/users/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user(user_id):
    user = User.query.get_or_404(user_id)
    return jsonify(user_schema.dump(user))

@api_bp.route('/users/<int:user_id>', methods=['PUT'])
@jwt_required()
def update_user(user_id):
    user = User.query.get_or_404(user_id)
    data = request.get_json()
    
    try:
        user.name = data.get('name', user.name)
        user.email = data.get('email', user.email)
        user.role = data.get('role', user.role)
        user.is_active = data.get('is_active', user.is_active)
        
        if 'password' in data:
            user.set_password(data['password'])
        
        db.session.commit()
        return jsonify(user_schema.dump(user))
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@api_bp.route('/users/<int:user_id>', methods=['DELETE'])
@jwt_required()
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    
    # Get all active transactions for this user
    active_transactions = Transaction.query.filter(
        Transaction.user_id == user_id,
        Transaction.status.in_(['issued', 'overdue'])
    ).all()
    
    # Mark all issued books as returned before deleting user
    for transaction in active_transactions:
        transaction.return_book()
        print(f"Auto-returned book '{transaction.book.title}' for deleted user '{user.name}'")
    
    # Cancel any pending reservations
    pending_reservations = Reservation.query.filter_by(
        user_id=user_id,
        status='pending'
    ).all()
    
    for reservation in pending_reservations:
        reservation.status = 'cancelled'
    
    db.session.delete(user)
    db.session.commit()
    
    return jsonify({
        'message': 'User deleted successfully',
        'books_returned': len(active_transactions),
        'reservations_cancelled': len(pending_reservations)
    })

# Transaction endpoints
@api_bp.route('/transactions', methods=['GET'])
@jwt_required()
def get_transactions():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    status = request.args.get('status', '')
    
    query = Transaction.query
    if status:
        query = query.filter(Transaction.status == status)
    
    transactions = query.order_by(Transaction.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'transactions': transactions_schema.dump(transactions.items),
        'total': transactions.total,
        'pages': transactions.pages,
        'current_page': transactions.page
    })

@api_bp.route('/transactions/issue', methods=['POST'])
@jwt_required()
def issue_book_api():
    data = request.get_json()
    
    if not data.get('user_id') or not data.get('book_id'):
        return jsonify({'error': 'user_id and book_id required'}), 400
    
    due_date = None
    if data.get('due_date'):
        due_date = datetime.fromisoformat(data['due_date'].replace('Z', '+00:00'))
    
    success, message = issue_book(data['user_id'], data['book_id'], due_date)
    
    if success:
        # Get the created transaction
        transaction = Transaction.query.filter(
            Transaction.user_id == data['user_id'],
            Transaction.book_id == data['book_id'],
            Transaction.status == 'issued'
        ).order_by(Transaction.created_at.desc()).first()
        
        return jsonify(transaction_schema.dump(transaction)), 201
    else:
        return jsonify({'error': message}), 400

@api_bp.route('/transactions/return', methods=['POST'])
@jwt_required()
def return_book_api():
    data = request.get_json()
    
    if not data.get('transaction_id'):
        return jsonify({'error': 'transaction_id required'}), 400
    
    success, message = return_book(data['transaction_id'])
    
    if success:
        transaction = Transaction.query.get(data['transaction_id'])
        return jsonify(transaction_schema.dump(transaction))
    else:
        return jsonify({'error': message}), 400

@api_bp.route('/transactions/overdue', methods=['GET'])
@jwt_required()
def get_overdue_transactions():
    # Calculate overdue fines
    calculate_overdue_fines()
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    overdue_transactions = Transaction.query.filter(
        Transaction.status == 'overdue'
    ).order_by(Transaction.due_date.asc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'transactions': transactions_schema.dump(overdue_transactions.items),
        'total': overdue_transactions.total,
        'pages': overdue_transactions.pages,
        'current_page': overdue_transactions.page
    })

# Quick scan endpoint
@api_bp.route('/quick-scan', methods=['POST'])
@jwt_required()
def quick_scan():
    """Handle quick scan input for books or users"""
    data = request.get_json()
    
    if not data or 'value' not in data:
        return jsonify({'error': 'Scan value required'}), 400
    
    scan_value = data['value'].strip()
    
    try:
        # Check if it's a book scan (starts with BOOK)
        if scan_value.upper().startswith('BOOK'):
            book_id = scan_value.upper().replace('BOOK', '').strip()
            if not book_id.isdigit():
                return jsonify({'error': 'Invalid book ID format'}), 400
            
            book_id = int(book_id)
            book = Book.query.get(book_id)
            
            if not book:
                return jsonify({'error': f'Book with ID {book_id} not found'}), 404
            
            # Check if book is available for checkout
            if book.available_copies > 0:
                return jsonify({
                    'success': True,
                    'type': 'book_available',
                    'message': f'Book "{book.title}" is available for checkout',
                    'book_id': book.id,
                    'book_title': book.title,
                    'available_copies': book.available_copies,
                    'action': 'checkout'
                })
            else:
                return jsonify({
                    'success': True,
                    'type': 'book_unavailable',
                    'message': f'Book "{book.title}" is not available (0 copies left)',
                    'book_id': book.id,
                    'book_title': book.title,
                    'available_copies': book.available_copies,
                    'action': 'unavailable'
                })
        
        # Check if it's a user scan (7-digit number)
        elif scan_value.isdigit() and len(scan_value) == 7:
            user_id = int(scan_value)
            user = User.query.get(user_id)
            
            if not user:
                return jsonify({'error': f'User with ID {user_id} not found'}), 404
            
            # Get user's current transactions
            current_transactions = Transaction.query.filter(
                Transaction.user_id == user_id,
                Transaction.status.in_(['issued', 'overdue'])
            ).all()
            
            if current_transactions:
                transaction_list = []
                for trans in current_transactions:
                    transaction_list.append({
                        'id': trans.id,
                        'book_title': trans.book.title,
                        'book_id': trans.book_id,
                        'due_date': trans.due_date.isoformat(),
                        'days_overdue': max(0, (datetime.utcnow() - trans.due_date).days) if trans.due_date < datetime.utcnow() else 0
                    })
                
                return jsonify({
                    'success': True,
                    'type': 'user_transactions',
                    'message': f'User "{user.name}" has {len(current_transactions)} active transactions',
                    'user_id': user.id,
                    'user_name': user.name,
                    'transactions': transaction_list,
                    'action': 'return'
                })
            else:
                return jsonify({
                    'success': True,
                    'type': 'user_no_transactions',
                    'message': f'User "{user.name}" has no active transactions',
                    'user_id': user.id,
                    'user_name': user.name,
                    'action': 'checkout'
                })
        
        # Check if it's a regular book ID (just a number)
        elif scan_value.isdigit():
            book_id = int(scan_value)
            book = Book.query.get(book_id)
            
            if not book:
                return jsonify({'error': f'Book with ID {book_id} not found'}), 404
            
            if book.available_copies > 0:
                return jsonify({
                    'success': True,
                    'type': 'book_available',
                    'message': f'Book "{book.title}" is available for checkout',
                    'book_id': book.id,
                    'book_title': book.title,
                    'available_copies': book.available_copies,
                    'action': 'checkout'
                })
            else:
                return jsonify({
                    'success': True,
                    'type': 'book_unavailable',
                    'message': f'Book "{book.title}" is not available (0 copies left)',
                    'book_id': book.id,
                    'book_title': book.title,
                    'available_copies': book.available_copies,
                    'action': 'unavailable'
                })
        
        else:
            return jsonify({'error': 'Invalid scan format. Use BOOK123, 7-digit user ID, or book ID'}), 400
            
    except ValueError:
        return jsonify({'error': 'Invalid ID format'}), 400
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

# Category endpoints
@api_bp.route('/categories', methods=['GET'])
@jwt_required()
def get_categories():
    categories = Category.query.all()
    return jsonify(categories_schema.dump(categories))

@api_bp.route('/categories', methods=['POST'])
@jwt_required()
def create_category():
    data = request.get_json()
    
    try:
        category = Category(
            name=data['name'],
            description=data.get('description', '')
        )
        db.session.add(category)
        db.session.commit()
        
        return jsonify(category_schema.dump(category)), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@api_bp.route('/categories/<int:category_id>', methods=['GET'])
@jwt_required()
def get_category(category_id):
    category = Category.query.get_or_404(category_id)
    return jsonify(category_schema.dump(category))

@api_bp.route('/categories/<int:category_id>', methods=['PUT'])
@jwt_required()
def update_category(category_id):
    category = Category.query.get_or_404(category_id)
    data = request.get_json()
    
    try:
        category.name = data.get('name', category.name)
        category.description = data.get('description', category.description)
        db.session.commit()
        return jsonify(category_schema.dump(category))
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@api_bp.route('/categories/<int:category_id>', methods=['DELETE'])
@jwt_required()
def delete_category(category_id):
    category = Category.query.get_or_404(category_id)
    
    # Check if category has books
    if category.books:
        return jsonify({'error': 'Cannot delete category with books'}), 400
    
    db.session.delete(category)
    db.session.commit()
    return jsonify({'message': 'Category deleted successfully'})

# Mobile Scanner Integration
@api_bp.route('/scan', methods=['POST', 'OPTIONS'])
@csrf.exempt
def mobile_scan():
    """Process scanned barcode from mobile scanner"""
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        return response
    
    try:
        data = request.get_json()
        if not data:
            response = jsonify({'error': 'No JSON data provided'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400
            
        code = data.get('code')
        code_type = data.get('type', 'BARCODE')
        
        print(f"Scan received - Code: {code}, Type: {code_type}")
        
        if not code:
            response = jsonify({'error': 'No code provided'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400
        
        # Look up book by barcode_id
        book = Book.query.filter_by(barcode_id=code).first()
        
        if book:
            # Check if book is currently issued or overdue
            active_transaction = Transaction.query.filter(
                Transaction.book_id == book.id,
                Transaction.status.in_(['issued', 'overdue'])
            ).first()
            
            result = {
                'found': True,
                'book_info': {
                    'id': book.id,
                    'title': book.title,
                    'author': book.author,
                    'barcode_id': book.barcode_id,
                    'available_copies': book.available_copies,
                    'is_available': book.is_available()
                },
                'transaction_info': None,
                'action': 'issue' if book.is_available() else 'unavailable'
            }
            
            if active_transaction:
                result['transaction_info'] = {
                    'id': active_transaction.id,
                    'user_name': active_transaction.user.name,
                    'issue_date': active_transaction.issue_date.isoformat(),
                    'due_date': active_transaction.due_date.isoformat()
                }
                result['action'] = 'return'
            
            response = jsonify(result)
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response
        else:
            response = jsonify({
                'found': False,
                'message': f'No book found with barcode: {code}'
            })
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response
            
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@api_bp.route('/scan/issue', methods=['POST'])
@csrf.exempt
def scan_issue_book():
    """Issue book using scanned barcode"""
    from flask import session
    
    # Check session authentication
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        barcode_id = data.get('barcode_id')
        
        if not user_id or not barcode_id:
            return jsonify({'success': False, 'error': 'user_id and barcode_id required'}), 400
        
        # Find book by barcode
        book = Book.query.filter_by(barcode_id=barcode_id).first()
        if not book:
            return jsonify({'success': False, 'error': 'Book not found'}), 404
        
        # Use existing issue_book function
        success, message = issue_book(user_id, book.id)
        
        if success:
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'error': message}), 400
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/scan/return', methods=['POST'])
@csrf.exempt
def scan_return_book():
    """Return book using scanned barcode"""
    from flask import session
    
    # Check session authentication
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        data = request.get_json()
        barcode_id = data.get('barcode_id')
        
        if not barcode_id:
            return jsonify({'success': False, 'error': 'barcode_id required'}), 400
        
        # Find book by barcode
        book = Book.query.filter_by(barcode_id=barcode_id).first()
        if not book:
            return jsonify({'success': False, 'error': 'Book not found'}), 404
        
        # Find active transaction for this book
        transaction = Transaction.query.filter(
            Transaction.book_id == book.id,
            Transaction.status.in_(['issued', 'overdue'])
        ).first()
        
        if not transaction:
            return jsonify({'success': False, 'error': 'This book is not currently issued'}), 400
        
        # Use existing return_book function
        success, message = return_book(transaction.id)
        
        if success:
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'error': message}), 400
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Latest scan storage (in production, use Redis or database)
latest_scan_storage = {'timestamp': 0}

@api_bp.route('/latest-scan', methods=['GET'])
def get_latest_scan():
    """Get the most recent scan for dashboard polling"""
    return jsonify(latest_scan_storage)

@api_bp.route('/update-latest-scan', methods=['POST', 'OPTIONS'])
@csrf.exempt
def update_latest_scan():
    """Update the latest scan data from mobile scanner"""
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        return response
    
    try:
        global latest_scan_storage
        data = request.get_json()
        latest_scan_storage = data
        response = jsonify({'success': True})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

# Simple test endpoint for mobile scanner
@api_bp.route('/test', methods=['GET', 'OPTIONS'])
def test_connection():
    """Simple test endpoint for mobile scanner"""
    response = jsonify({'status': 'ok', 'message': 'Backend connected'})
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    response.headers.add('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
    return response


# Dashboard stats endpoint
@api_bp.route('/dashboard/stats', methods=['GET'])
@jwt_required()
def get_dashboard_stats_api():
    # Update fines before getting stats
    from ..utils import update_all_transaction_fines
    update_all_transaction_fines()
    
    stats = get_dashboard_stats()
    return jsonify(stats)

# Fine management endpoints
@api_bp.route('/fines/update', methods=['POST'])
@jwt_required()
def update_fines():
    """Manually update all transaction fines"""
    from ..utils import update_all_transaction_fines
    updated_count = update_all_transaction_fines()
    return jsonify({
        'success': True,
        'message': f'Updated {updated_count} transactions with current fines'
    })
