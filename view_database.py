#!/usr/bin/env python3
"""
Script to view database contents
"""
from app import create_app, db
from app.models import User, Book, Transaction, Category

app = create_app()

with app.app_context():
    print("=== DATABASE CONTENTS ===\n")
    
    print("BOOKS:")
    books = Book.query.all()
    for book in books:
        print(f"  - {book.title} by {book.author} (Available: {book.available_copies}/{book.total_copies})")
    
    print(f"\nUSERS:")
    users = User.query.all()
    for user in users:
        print(f"  - {user.name} ({user.email}) - Role: {user.role} - Active: {user.is_active}")
    
    print(f"\nCATEGORIES:")
    categories = Category.query.all()
    for cat in categories:
        print(f"  - {cat.name}: {cat.description}")
    
    print(f"\nTRANSACTIONS:")
    transactions = Transaction.query.all()
    for trans in transactions:
        print(f"  - {trans.user.name} borrowed '{trans.book.title}' - Status: {trans.status}")
    
    print(f"\nSTATISTICS:")
    print(f"  - Total Books: {Book.query.count()}")
    print(f"  - Total Users: {User.query.count()}")
    print(f"  - Total Transactions: {Transaction.query.count()}")
    print(f"  - Active Transactions: {Transaction.query.filter_by(status='issued').count()}")