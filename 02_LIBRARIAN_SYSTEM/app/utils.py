from datetime import datetime, timedelta
from flask import current_app
from .models import Transaction, User, Book, Category
from . import db

def calculate_overdue_fines():
    """Calculate fines for all overdue transactions and update their status"""
    # Find all issued transactions that are past due date
    overdue_transactions = Transaction.query.filter(
        Transaction.status == 'issued',
        Transaction.due_date < datetime.utcnow()
    ).all()
    
    fine_rate = current_app.config.get('FINE_RATE', 5)
    updated_count = 0
    
    for transaction in overdue_transactions:
        old_fine = transaction.fine_amount
        old_status = transaction.status
        
        # Calculate fine and update status
        transaction.calculate_fine(fine_rate)
        
        if transaction.fine_amount != old_fine or old_status != transaction.status:
            updated_count += 1
    
    db.session.commit()
    return updated_count

def update_all_transaction_fines():
    """Update fines for all active transactions (issued and overdue)"""
    active_transactions = Transaction.query.filter(
        Transaction.status.in_(['issued', 'overdue'])
    ).all()
    
    fine_rate = current_app.config.get('FINE_RATE', 5)
    updated_count = 0
    
    for transaction in active_transactions:
        old_fine = transaction.fine_amount
        old_status = transaction.status
        
        # Calculate current fine
        transaction.calculate_fine(fine_rate)
        
        if transaction.fine_amount != old_fine or old_status != transaction.status:
            updated_count += 1
    
    db.session.commit()
    return updated_count

def send_overdue_reminders():
    """Send reminders for overdue books (placeholder for email functionality)"""
    overdue_transactions = Transaction.query.filter(
        Transaction.status == 'overdue'
    ).all()
    
    reminders_sent = 0
    for transaction in overdue_transactions:
        # Placeholder for email sending
        print(f"REMINDER: {transaction.user.name} has overdue book '{transaction.book.title}' "
              f"due on {transaction.due_date.strftime('%Y-%m-%d')}. "
              f"Fine: ₹{transaction.fine_amount}")
        reminders_sent += 1
    
    return reminders_sent

def get_dashboard_stats():
    """Get statistics for dashboard"""
    from sqlalchemy import func, extract
    
    # Basic counts
    total_books = Book.query.count()
    total_users = User.query.filter_by(role='user').count()
    issued_books = Transaction.query.filter(Transaction.status == 'issued').count()
    overdue_books = Transaction.query.filter(Transaction.status == 'overdue').count()
    total_fines = db.session.query(func.sum(Transaction.fine_amount)).scalar() or 0
    
    # Calculate total copies and available copies
    total_copies = db.session.query(func.sum(Book.total_copies)).scalar() or 0
    available_copies = db.session.query(func.sum(Book.available_copies)).scalar() or 0
    
    # Calculate availability percentage
    availability_percentage = round((available_copies / total_copies * 100), 1) if total_copies > 0 else 0
    
    # Get new users this week
    one_week_ago = datetime.utcnow() - timedelta(days=7)
    new_users_this_week = User.query.filter(
        User.created_at >= one_week_ago,
        User.role == 'user'
    ).count()
    
    # Get monthly circulation data for the last 10 months
    circulation_data = []
    for i in range(9, -1, -1):
        month_start = datetime.utcnow().replace(day=1) - timedelta(days=30*i)
        month_end = month_start + timedelta(days=30)
        
        issued_count = Transaction.query.filter(
            Transaction.issue_date >= month_start,
            Transaction.issue_date < month_end
        ).count()
        
        returned_count = Transaction.query.filter(
            Transaction.return_date >= month_start,
            Transaction.return_date < month_end,
            Transaction.status == 'returned'
        ).count()
        
        circulation_data.append({
            'month': month_start.strftime('%b'),
            'issued': issued_count,
            'returned': returned_count
        })
    
    # Get top 5 categories by borrow count
    category_stats = db.session.query(
        Category.name,
        func.count(Transaction.id).label('borrow_count')
    ).join(Book, Book.category_id == Category.id)\
     .join(Transaction, Transaction.book_id == Book.id)\
     .group_by(Category.id, Category.name)\
     .order_by(func.count(Transaction.id).desc())\
     .limit(5)\
     .all()
    
    stats = {
        'total_books': total_books,
        'total_copies': total_copies,
        'available_copies': available_copies,
        'availability_percentage': availability_percentage,
        'total_users': total_users,
        'new_users_this_week': new_users_this_week,
        'total_issued': issued_books,
        'overdue_count': overdue_books,
        'total_fines': round(total_fines, 2),
        'circulation_data': circulation_data,
        'category_stats': [{'name': name, 'count': count} for name, count in category_stats]
    }
    return stats

def issue_book(user_id, book_id, due_date=None):
    """Issue a book to a user"""
    user = User.query.get_or_404(user_id)
    book = Book.query.get_or_404(book_id)
    
    if not book.is_available():
        return False, "Book is not available"
    
    if due_date is None:
        due_date = datetime.utcnow() + timedelta(days=14)
    
    # Check if user already has this book issued or overdue
    existing_transaction = Transaction.query.filter(
        Transaction.user_id == user_id,
        Transaction.book_id == book_id,
        Transaction.status.in_(['issued', 'overdue'])
    ).first()
    
    if existing_transaction:
        return False, "User already has this book issued"
    
    # Create transaction
    transaction = Transaction(
        user_id=user_id,
        book_id=book_id,
        due_date=due_date
    )
    
    # Update book availability
    book.available_copies -= 1
    
    db.session.add(transaction)
    db.session.commit()
    
    return True, "Book issued successfully"

def return_book(transaction_id):
    """Return a book"""
    transaction = Transaction.query.get_or_404(transaction_id)
    
    if transaction.status not in ['issued', 'overdue']:
        return False, "Book is not currently issued or overdue"
    
    # Return the book
    transaction.return_book()
    
    db.session.commit()
    
    return True, "Book returned successfully"
