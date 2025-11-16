from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from ..models import User, Book, Transaction, Category
from ..forms import LoginForm, BookForm, UserForm, CategoryForm, IssueBookForm, ReturnBookForm
from ..utils import get_dashboard_stats, issue_book, return_book, calculate_overdue_fines
from .. import db, csrf
from datetime import datetime, timedelta

web_bp = Blueprint('web', __name__)

@web_bp.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('web.login'))
    return redirect(url_for('web.dashboard'))

@web_bp.route('/mobile_scanner.html')
def mobile_scanner():
    """Serve mobile scanner HTML"""
    from flask import send_from_directory
    import os
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return send_from_directory(root_dir, 'mobile_scanner.html')

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
    
    # Update all transaction fines before getting stats
    from ..utils import update_all_transaction_fines
    update_all_transaction_fines()
    
    stats = get_dashboard_stats()
    
    # Recent transactions
    recent_transactions = Transaction.query.order_by(Transaction.created_at.desc()).limit(10).all()
    
    # Books due soon (within next 3 days) or overdue
    three_days_from_now = datetime.utcnow() + timedelta(days=3)
    due_soon_books = Transaction.query.filter(
        Transaction.status.in_(['issued', 'overdue']),
        Transaction.due_date <= three_days_from_now
    ).order_by(Transaction.due_date.asc()).limit(5).all()
    
    return render_template('pages/management/dashboard.html', 
                         stats=stats, 
                         recent_transactions=recent_transactions,
                         due_soon_books=due_soon_books)

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

@web_bp.route('/users/delete/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    if 'user_id' not in session:
        return redirect(url_for('web.login'))
    
    # Check if current user is librarian
    if session.get('user_role') != 'librarian':
        flash('Access denied. Only librarians can delete users.', 'error')
        return redirect(url_for('web.users'))
    
    user = User.query.get_or_404(user_id)
    
    # Prevent deletion of librarian accounts
    if user.role == 'librarian':
        flash('Cannot delete librarian accounts.', 'error')
        return redirect(url_for('web.users'))
    
    # Prevent deletion of current user
    if user.id == session.get('user_id'):
        flash('Cannot delete your own account.', 'error')
        return redirect(url_for('web.users'))
    
    try:
        # Check if user has any active transactions
        active_transactions = Transaction.query.filter_by(
            user_id=user_id, 
            status='issued'
        ).count()
        
        if active_transactions > 0:
            flash(f'Cannot delete user. They have {active_transactions} active book(s) issued.', 'error')
            return redirect(url_for('web.users'))
        
        # Delete user and related data
        user_name = user.name
        
        # Delete related transactions (history)
        Transaction.query.filter_by(user_id=user_id).delete()
        
        # Delete the user
        db.session.delete(user)
        db.session.commit()
        
        flash(f'User "{user_name}" has been successfully deleted.', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash('Error deleting user. Please try again.', 'error')
    
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
    
    # Update all transaction fines before displaying
    from ..utils import update_all_transaction_fines
    update_all_transaction_fines()
    
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
    return_form.transaction_id.choices = [(t.id, f"{t.user.name} - {t.book.title}") for t in Transaction.query.filter(Transaction.status.in_(['issued', 'overdue'])).all()]
    
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
    form.transaction_id.choices = [(t.id, f"{t.user.name} - {t.book.title}") for t in Transaction.query.filter(Transaction.status.in_(['issued', 'overdue'])).all()]
    
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
    
    # Update all transaction fines and statuses
    from ..utils import update_all_transaction_fines
    update_all_transaction_fines()
    
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

@web_bp.route('/users/json')
def users_json():
    """JSON endpoint for users dropdown"""
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    users = User.query.filter_by(role='user', is_active=True).all()
    user_data = []
    for user in users:
        user_data.append({
            'id': user.id,
            'name': user.name,
            'email': user.email
        })
    
    return jsonify(user_data)

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

@web_bp.route('/quick-scan', methods=['POST'])
@csrf.exempt
def quick_scan_web():
    """Handle quick scan input for books or users (web version without JWT)"""
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
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
                Transaction.status == 'issued'
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
