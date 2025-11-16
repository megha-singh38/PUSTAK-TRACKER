#!/usr/bin/env python3
"""
Barcode generator for library books
"""

import sqlite3
import os
from PIL import Image, ImageDraw, ImageFont
from barcode import Code128
from barcode.writer import ImageWriter
import io

def generate_barcodes():
    """Generate barcode images for all books in database"""
    
    db_path = "../03_SHARED_RESOURCES/instance/pustak_tracker.db"
    
    if not os.path.exists(db_path):
        print("❌ Database not found")
        return
    
    # Create barcodes directory
    os.makedirs("barcodes", exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT id, title, author, barcode_id FROM books WHERE barcode_id IS NOT NULL")
        books = cursor.fetchall()
        
        print(f"📚 Generating barcodes for {len(books)} books...")
        
        for book in books:
            book_id, title, author, barcode_id = book
            
            # Generate Code128 barcode
            code = Code128(barcode_id, writer=ImageWriter())
            
            # Generate barcode image in memory
            buffer = io.BytesIO()
            code.write(buffer)
            buffer.seek(0)
            
            # Open barcode image
            barcode_img = Image.open(buffer)
            
            # Create a larger image with text
            img_width, img_height = 400, 300
            img = Image.new('RGB', (img_width, img_height), 'white')
            
            # Resize and paste barcode
            barcode_width, barcode_height = barcode_img.size
            scale = min(350 / barcode_width, 120 / barcode_height)
            new_width = int(barcode_width * scale)
            new_height = int(barcode_height * scale)
            
            barcode_img = barcode_img.resize((new_width, new_height))
            barcode_x = (img_width - new_width) // 2
            barcode_y = 50
            img.paste(barcode_img, (barcode_x, barcode_y))
            
            # Add text
            draw = ImageDraw.Draw(img)
            
            try:
                font = ImageFont.truetype("arial.ttf", 14)
                small_font = ImageFont.truetype("arial.ttf", 10)
            except:
                font = ImageFont.load_default()
                small_font = ImageFont.load_default()
            
            # Book title (truncated)
            title_text = title[:35] + "..." if len(title) > 35 else title
            draw.text((10, 10), title_text, fill="black", font=font)
            
            # Author
            author_text = f"by {author[:30]}..." if len(author) > 30 else f"by {author}"
            draw.text((10, 30), author_text, fill="gray", font=small_font)
            
            # Barcode ID below barcode
            text_y = barcode_y + new_height + 10
            draw.text((barcode_x, text_y), barcode_id, fill="black", font=font)
            
            # Library name
            draw.text((10, img_height - 30), "Pustak Tracker Library", fill="blue", font=small_font)
            
            # Save image
            filename = f"barcodes/{barcode_id}.png"
            img.save(filename)
            print(f"  ✅ {barcode_id} - {title[:30]}...")
        
        print(f"\n🎉 Generated {len(books)} barcode images in 'barcodes/' folder")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        conn.close()

def generate_barcode_sheet():
    """Generate a single sheet with multiple barcodes for printing"""
    
    db_path = "../03_SHARED_RESOURCES/instance/pustak_tracker.db"
    
    if not os.path.exists(db_path):
        print("❌ Database not found")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT barcode_id, title FROM books WHERE barcode_id IS NOT NULL LIMIT 12")
        books = cursor.fetchall()
        
        # Create A4 sheet (2480x3508 pixels at 300 DPI)
        sheet_width, sheet_height = 2480, 3508
        sheet = Image.new('RGB', (sheet_width, sheet_height), 'white')
        
        # Grid: 2 columns, 6 rows
        cols, rows = 2, 6
        cell_width = sheet_width // cols
        cell_height = sheet_height // rows
        
        for i, (barcode_id, title) in enumerate(books):
            if i >= 12:  # Max 12 per sheet
                break
                
            row = i // cols
            col = i % cols
            
            x = col * cell_width + 50
            y = row * cell_height + 50
            
            # Generate barcode for this book
            code = Code128(barcode_id, writer=ImageWriter())
            buffer = io.BytesIO()
            code.write(buffer)
            buffer.seek(0)
            barcode_img = Image.open(buffer)
            
            # Resize barcode to fit cell
            barcode_width = cell_width - 100
            barcode_height = 150
            barcode_img = barcode_img.resize((barcode_width, barcode_height))
            
            # Paste barcode
            sheet.paste(barcode_img, (x, y + 50))
            
            # Add text
            draw = ImageDraw.Draw(sheet)
            try:
                font = ImageFont.truetype("arial.ttf", 36)
                small_font = ImageFont.truetype("arial.ttf", 24)
            except:
                font = ImageFont.load_default()
                small_font = ImageFont.load_default()
            
            # Title
            title_text = title[:20] + "..." if len(title) > 20 else title
            draw.text((x, y), title_text, fill="black", font=small_font)
            
            # Barcode ID below barcode
            draw.text((x, y + 220), barcode_id, fill="blue", font=font)
        
        # Save sheet
        os.makedirs("barcodes", exist_ok=True)
        sheet.save("barcodes/barcode_sheet.png")
        print("📄 Generated printable barcode sheet: barcodes/barcode_sheet.png")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    print("🏷️ BARCODE GENERATOR")
    print("=" * 30)
    
    choice = input("Generate: (1) Individual barcodes (2) Print sheet (3) Both [1]: ").strip()
    
    if choice in ['2', 'sheet']:
        generate_barcode_sheet()
    elif choice in ['3', 'both']:
        generate_barcodes()
        generate_barcode_sheet()
    else:
        generate_barcodes()