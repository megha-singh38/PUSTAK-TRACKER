#!/usr/bin/env python3
"""
Script to get Book IDs and User IDs
"""
from app import create_app, db
from app.models import User, Book

app = create_app()

with app.app_context():
    print("=== BOOK IDs ===")
    books = Book.query.all()
    for book in books:
        print(f"ID: {book.id} - {book.title} by {book.author} (Available: {book.available_copies}/{book.total_copies})")
    
    print(f"\n=== USER IDs ===")
    users = User.query.all()
    for user in users:
        print(f"ID: {user.id} - {user.name} ({user.email}) - Role: {user.role}")
    
    print(f"\n=== ACTIVE USERS (for issuing books) ===")
    active_users = User.query.filter_by(role='user', is_active=True).all()
    for user in active_users:
        print(f"ID: {user.id} - {user.name} ({user.email})")
    
    print(f"\n=== AVAILABLE BOOKS (for issuing) ===")
    available_books = Book.query.filter(Book.available_copies > 0).all()
    for book in available_books:
        print(f"ID: {book.id} - {book.title} by {book.author} (Available: {book.available_copies})")
