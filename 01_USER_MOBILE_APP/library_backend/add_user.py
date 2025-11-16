#!/usr/bin/env python3
"""
Add a new user to mobile backend database
"""
import sqlite3
import bcrypt

# User details
name = "Kittu"
email = "kittu@gmail.com"
password = "user123"
role = "user"

# Hash password
hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

# Connect to database
conn = sqlite3.connect('library.db')
cursor = conn.cursor()

# Check if user exists
cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
if cursor.fetchone():
    print(f"User {email} already exists. Updating password...")
    cursor.execute('UPDATE users SET password = ?, role = ? WHERE email = ?', 
                   (hashed_password.decode('utf-8'), role, email))
else:
    print(f"Creating new user {email}...")
    cursor.execute('''
        INSERT INTO users (name, email, password, role, membership_id)
        VALUES (?, ?, ?, ?, ?)
    ''', (name, email, hashed_password.decode('utf-8'), role, 'USR001'))

conn.commit()
conn.close()

print(f"\n✅ User created/updated successfully!")
print(f"Email: {email}")
print(f"Password: {password}")
print(f"Role: {role}")
