from datetime import datetime, timedelta
from flask import current_app
from .models import Transaction, User, Book
from . import db

def calculate_overdue_fines():
    """Calculate fines for all overdue transactions"""
    overdue_transactions = Transaction.query.filter(
        Transaction.status == 'issued',
        Transaction.due_date < datetime.utcnow()
    ).all()
    
    fine_rate = current_app.config.get('FINE_RATE', 5)
    updated_count = 0
    
    for transaction in overdue_transactions:
        old_fine = transaction.fine_amount
        transaction.calculate_fine(fine_rate)
        if transaction.fine_amount != old_fine:
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
    stats = {
        'total_books': Book.query.count(),
        'total_users': User.query.count(),
        'issued_books': Transaction.query.filter(Transaction.status == 'issued').count(),
        'overdue_books': Transaction.query.filter(Transaction.status == 'overdue').count(),
        'total_fines': db.session.query(db.func.sum(Transaction.fine_amount)).scalar() or 0
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
    
    # Check if user already has this book issued
    existing_transaction = Transaction.query.filter(
        Transaction.user_id == user_id,
        Transaction.book_id == book_id,
        Transaction.status == 'issued'
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
    
    if transaction.status != 'issued':
        return False, "Book is not currently issued"
    
    # Return the book
    transaction.return_book()
    
    db.session.commit()
    
    return True, "Book returned successfully"
