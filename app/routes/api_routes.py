from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import check_password_hash
from marshmallow import Schema, fields, ValidationError
from ..models import User, Book, Transaction, Category
from ..utils import issue_book, return_book, calculate_overdue_fines, get_dashboard_stats
from .. import db
from datetime import datetime, timedelta

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
        access_token = create_access_token(identity=user.id)
        return jsonify({
            'access_token': access_token,
            'user': user_schema.dump(user)
        }), 200
    else:
        return jsonify({'error': 'Invalid credentials'}), 401

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
        Transaction.status == 'issued'
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
    
    # Check if user has active transactions
    active_transactions = Transaction.query.filter(
        Transaction.user_id == user_id,
        Transaction.status == 'issued'
    ).count()
    
    if active_transactions > 0:
        return jsonify({'error': 'Cannot delete user with active transactions'}), 400
    
    db.session.delete(user)
    db.session.commit()
    return jsonify({'message': 'User deleted successfully'})

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

# Dashboard stats endpoint
@api_bp.route('/dashboard/stats', methods=['GET'])
@jwt_required()
def get_dashboard_stats_api():
    stats = get_dashboard_stats()
    return jsonify(stats)
