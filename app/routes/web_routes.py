from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from ..models import User, Book, Transaction, Category
from ..forms import LoginForm, BookForm, UserForm, CategoryForm, IssueBookForm, ReturnBookForm
from ..utils import get_dashboard_stats, issue_book, return_book, calculate_overdue_fines
from .. import db
from datetime import datetime, timedelta

web_bp = Blueprint('web', __name__)

@web_bp.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('web.login'))
    return redirect(url_for('web.dashboard'))

@web_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('web.dashboard'))
    
    # Ensure default librarian exists
    librarian = User.query.filter_by(email='librarian@pustak.com').first()
    if not librarian:
        librarian = User(
            name='Librarian',
            email='librarian@pustak.com',
            role='librarian'
        )
        librarian.set_password('admin123')
        db.session.add(librarian)
        db.session.commit()
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data) and user.role == 'librarian':
            session['user_id'] = user.id
            session['user_name'] = user.name
            session['user_role'] = user.role
            flash('Login successful!', 'success')
            return redirect(url_for('web.dashboard'))
        else:
            flash('Invalid email or password', 'error')
    
    return render_template('pages/auth/login.html', form=form)

@web_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('web.login'))

@web_bp.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('web.login'))
    
    stats = get_dashboard_stats()
    
    # Recent transactions
    recent_transactions = Transaction.query.order_by(Transaction.created_at.desc()).limit(10).all()
    
    # Overdue books
    overdue_books = Transaction.query.filter(
        Transaction.status == 'overdue'
    ).order_by(Transaction.due_date.asc()).limit(5).all()
    
    return render_template('pages/management/dashboard.html', 
                         stats=stats, 
                         recent_transactions=recent_transactions,
                         overdue_books=overdue_books)

@web_bp.route('/books')
def books():
    if 'user_id' not in session:
        return redirect(url_for('web.login'))
    
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    query = Book.query
    if search:
        query = query.filter(
            (Book.title.contains(search)) |
            (Book.author.contains(search)) |
            (Book.isbn.contains(search))
        )
    
    books = query.paginate(
        page=page, per_page=10, error_out=False
    )
    
    form = BookForm()
    categories = Category.query.all()
    return render_template('pages/management/books.html', books=books, form=form, search=search, categories=categories)

@web_bp.route('/books/add', methods=['POST'])
def add_book():
    if 'user_id' not in session:
        return redirect(url_for('web.login'))
    
    form = BookForm()
    if form.validate_on_submit():
        book = Book(
            title=form.title.data,
            author=form.author.data,
            publisher=form.publisher.data,
            isbn=form.isbn.data,
            category_id=form.category_id.data,
            total_copies=form.total_copies.data,
            available_copies=form.total_copies.data
        )
        db.session.add(book)
        db.session.commit()
        flash('Book added successfully!', 'success')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{field}: {error}', 'error')
    
    return redirect(url_for('web.books'))

@web_bp.route('/books/<int:book_id>/edit', methods=['POST'])
def edit_book(book_id):
    if 'user_id' not in session:
        return redirect(url_for('web.login'))
    
    book = Book.query.get_or_404(book_id)
    form = BookForm()
    
    if form.validate_on_submit():
        book.title = form.title.data
        book.author = form.author.data
        book.publisher = form.publisher.data
        book.isbn = form.isbn.data
        book.category_id = form.category_id.data
        
        # Adjust available copies if total copies changed
        old_total = book.total_copies
        book.total_copies = form.total_copies.data
        if form.total_copies.data > old_total:
            book.available_copies += (form.total_copies.data - old_total)
        elif form.total_copies.data < old_total:
            book.available_copies = max(0, book.available_copies - (old_total - form.total_copies.data))
        
        db.session.commit()
        flash('Book updated successfully!', 'success')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{field}: {error}', 'error')
    
    return redirect(url_for('web.books'))

@web_bp.route('/books/<int:book_id>/delete', methods=['POST'])
def delete_book(book_id):
    if 'user_id' not in session:
        return redirect(url_for('web.login'))
    
    print(f"Delete book request received for book_id: {book_id}")
    print(f"Request method: {request.method}")
    print(f"Request data: {request.form}")
    
    try:
        book = Book.query.get_or_404(book_id)
        print(f"Book found: {book.title}")
        
        # Check if book has active transactions
        active_transactions = Transaction.query.filter(
            Transaction.book_id == book_id,
            Transaction.status == 'issued'
        ).count()
        
        print(f"Active transactions for this book: {active_transactions}")
        
        if active_transactions > 0:
            flash('Cannot delete book with active transactions', 'error')
            print("Cannot delete - book has active transactions")
        else:
            print(f"Deleting book: {book.title}")
            db.session.delete(book)
            db.session.commit()
            flash('Book deleted successfully!', 'success')
            print("Book deleted successfully")
            
    except Exception as e:
        print(f"Error deleting book: {str(e)}")
        flash(f'Error deleting book: {str(e)}', 'error')
    
    return redirect(url_for('web.books'))

@web_bp.route('/users')
def users():
    if 'user_id' not in session:
        return redirect(url_for('web.login'))
    
    # Check if current user is librarian
    if session.get('user_role') != 'librarian':
        flash('Access denied. Only librarians can view users.', 'error')
        return redirect(url_for('web.dashboard'))
    
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    query = User.query
    if search:
        query = query.filter(
            (User.name.contains(search)) |
            (User.email.contains(search))
        )
    
    users = query.paginate(
        page=page, per_page=10, error_out=False
    )
    
    form = UserForm()
    return render_template('pages/management/users.html', users=users, form=form, search=search, current_user_role=session.get('user_role'))

@web_bp.route('/users/add', methods=['POST'])
def add_user():
    if 'user_id' not in session:
        return redirect(url_for('web.login'))
    
    # Check if current user is librarian
    if session.get('user_role') != 'librarian':
        flash('Access denied. Only librarians can add users.', 'error')
        return redirect(url_for('web.users'))
    
    form = UserForm()
    if form.validate_on_submit():
        # Check if email already exists
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user:
            flash('Email already exists', 'error')
        else:
            # Validate role selection
            selected_role = form.role.data
            if selected_role not in ['user', 'librarian']:
                flash('Invalid role selected', 'error')
                return redirect(url_for('web.users'))
            
            try:
                user = User(
                    name=form.name.data,
                    email=form.email.data,
                    role=selected_role  # Explicitly use the selected role
                )
                user.set_password(form.password.data)
                db.session.add(user)
                db.session.commit()
                flash(f'User added successfully with role: {selected_role}!', 'success')
            except Exception as e:
                db.session.rollback()
                flash('Error adding user. Please try again.', 'error')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{field}: {error}', 'error')
    
    return redirect(url_for('web.users'))

@web_bp.route('/users/<int:user_id>/toggle', methods=['POST'])
def toggle_user_status(user_id):
    if 'user_id' not in session:
        return redirect(url_for('web.login'))
    
    # Check if current user is librarian
    if session.get('user_role') != 'librarian':
        flash('Access denied. Only librarians can modify user status.', 'error')
        return redirect(url_for('web.users'))
    
    user = User.query.get_or_404(user_id)
    
    # Prevent deactivating librarians
    if user.role == 'librarian':
        flash('Cannot modify librarian status.', 'error')
        return redirect(url_for('web.users'))
    
    user.is_active = not user.is_active
    db.session.commit()
    
    status = 'activated' if user.is_active else 'deactivated'
    flash(f'User {status} successfully!', 'success')
    
    return redirect(url_for('web.users'))

@web_bp.route('/transactions')
def transactions():
    if 'user_id' not in session:
        return redirect(url_for('web.login'))
    
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', '')
    
    query = Transaction.query
    if status_filter:
        query = query.filter(Transaction.status == status_filter)
    
    transactions = query.order_by(Transaction.created_at.desc()).paginate(
        page=page, per_page=10, error_out=False
    )
    
    # Forms for issuing and returning books
    issue_form = IssueBookForm()
    return_form = ReturnBookForm()
    
    # Populate form choices
    issue_form.user_id.choices = [(u.id, u.name) for u in User.query.filter_by(role='user', is_active=True).all()]
    issue_form.book_id.choices = [(b.id, f"{b.title} by {b.author}") for b in Book.query.filter(Book.available_copies > 0).all()]
    return_form.transaction_id.choices = [(t.id, f"{t.user.name} - {t.book.title}") for t in Transaction.query.filter_by(status='issued').all()]
    
    return render_template('pages/management/transactions.html', 
                         transactions=transactions, 
                         issue_form=issue_form,
                         return_form=return_form,
                         status_filter=status_filter)

@web_bp.route('/transactions/issue', methods=['POST'])
def issue_transaction():
    if 'user_id' not in session:
        return redirect(url_for('web.login'))
    
    form = IssueBookForm()
    
    # Populate form choices before validation
    form.user_id.choices = [(u.id, u.name) for u in User.query.filter_by(role='user', is_active=True).all()]
    form.book_id.choices = [(b.id, f"{b.title} by {b.author}") for b in Book.query.filter(Book.available_copies > 0).all()]
    
    if form.validate_on_submit():
        success, message = issue_book(
            form.user_id.data,
            form.book_id.data,
            form.due_date.data
        )
        if success:
            flash(message, 'success')
        else:
            flash(message, 'error')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{field}: {error}', 'error')
    
    return redirect(url_for('web.transactions'))

@web_bp.route('/transactions/return', methods=['POST'])
def return_transaction():
    if 'user_id' not in session:
        return redirect(url_for('web.login'))
    
    form = ReturnBookForm()
    
    # Populate form choices before validation
    form.transaction_id.choices = [(t.id, f"{t.user.name} - {t.book.title}") for t in Transaction.query.filter_by(status='issued').all()]
    
    if form.validate_on_submit():
        success, message = return_book(form.transaction_id.data)
        if success:
            flash(message, 'success')
        else:
            flash(message, 'error')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{field}: {error}', 'error')
    
    return redirect(url_for('web.transactions'))

@web_bp.route('/overdue')
def overdue():
    if 'user_id' not in session:
        return redirect(url_for('web.login'))
    
    # Calculate overdue fines
    calculate_overdue_fines()
    
    page = request.args.get('page', 1, type=int)
    overdue_transactions = Transaction.query.filter(
        Transaction.status == 'overdue'
    ).order_by(Transaction.due_date.asc()).paginate(
        page=page, per_page=10, error_out=False
    )
    
    return render_template('pages/management/overdue.html', overdue_transactions=overdue_transactions)

@web_bp.route('/overdue/recalculate', methods=['POST'])
def recalculate_overdue_fines():
    if 'user_id' not in session:
        return redirect(url_for('web.login'))
    
    try:
        updated_count = calculate_overdue_fines()
        flash(f'Overdue fines recalculated successfully! Updated {updated_count} transactions.', 'success')
    except Exception as e:
        flash(f'Error recalculating fines: {str(e)}', 'error')
    
    return redirect(url_for('web.overdue'))

@web_bp.route('/categories')
def categories():
    if 'user_id' not in session:
        return redirect(url_for('web.login'))
    
    categories = Category.query.all()
    form = CategoryForm()
    return render_template('pages/management/categories.html', categories=categories, form=form)

@web_bp.route('/categories/add', methods=['POST'])
def add_category():
    if 'user_id' not in session:
        return redirect(url_for('web.login'))
    
    form = CategoryForm()
    if form.validate_on_submit():
        category = Category(
            name=form.name.data,
            description=form.description.data
        )
        db.session.add(category)
        db.session.commit()
        flash('Category added successfully!', 'success')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{field}: {error}', 'error')
    
    return redirect(url_for('web.categories'))

@web_bp.route('/categories/<int:category_id>/delete', methods=['POST'])
def delete_category(category_id):
    if 'user_id' not in session:
        return redirect(url_for('web.login'))
    
    category = Category.query.get_or_404(category_id)
    
    # Check if category has books
    if category.books:
        flash('Cannot delete category with books', 'error')
    else:
        db.session.delete(category)
        db.session.commit()
        flash('Category deleted successfully!', 'success')
    
    return redirect(url_for('web.categories'))

@web_bp.route('/debug/users')
def debug_users():
    """Debug route to check user data"""
    if 'user_id' not in session:
        return redirect(url_for('web.login'))
    
    users = User.query.all()
    user_data = []
    for user in users:
        user_data.append({
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'role': user.role,
            'is_active': user.is_active,
            'created_at': user.created_at.strftime('%Y-%m-%d %H:%M:%S')
        })
    
    return jsonify({
        'total_users': len(user_data),
        'users': user_data
    })
