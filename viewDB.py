#!/usr/bin/env python3
"""
Simple Database Viewer for Pustak Tracker
View all tables and their data
"""

import sqlite3
import os

# Database path
DB_PATH = "03_SHARED_RESOURCES/instance/pustak_tracker.db"

def view_database():
    if not os.path.exists(DB_PATH):
        print(f"❌ Database not found at: {DB_PATH}")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = cursor.fetchall()
    
    print("=" * 80)
    print("📚 PUSTAK TRACKER DATABASE VIEWER")
    print("=" * 80)
    print(f"\n📁 Database: {DB_PATH}\n")
    
    for (table_name,) in tables:
        print(f"\n{'='*80}")
        print(f"📋 TABLE: {table_name.upper()}")
        print(f"{'='*80}")
        
        # Get column info
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        col_names = [col[1] for col in columns]
        
        # Get row count
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        print(f"Total Records: {count}")
        
        if count > 0:
            # Get all data
            cursor.execute(f"SELECT * FROM {table_name}")
            rows = cursor.fetchall()
            
            # Print header
            print("\n" + " | ".join(col_names))
            print("-" * 80)
            
            # Print rows
            for row in rows:
                print(" | ".join(str(val) if val is not None else "NULL" for val in row))
        else:
            print("(Empty table)")
    
    conn.close()
    print("\n" + "=" * 80)
    print("✅ Database view complete!")
    print("=" * 80)

if __name__ == "__main__":
    view_database()
