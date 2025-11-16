from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from ..models import Book
from .. import db

barcode_bp = Blueprint('barcode', __name__)

@barcode_bp.route('/scan')
def scanner():
    """Render the barcode scanner page"""
    if 'user_id' not in session:
        return redirect(url_for('web.login'))
    
    return render_template('pages/scanner.html')

@barcode_bp.route('/api/barcode/<barcode>')
def lookup_barcode(barcode):
    """Look up a book by barcode/ISBN"""
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        # Clean the barcode (remove spaces, dashes, etc.)
        clean_barcode = barcode.strip().replace('-', '').replace(' ', '')
        
        # Search for book by ISBN
        book = Book.query.filter_by(isbn=clean_barcode).first()
        
        if book:
            return jsonify({
                'found': True,
                'book': {
                    'id': book.id,
                    'title': book.title,
                    'author': book.author,
                    'publisher': book.publisher,
                    'isbn': book.isbn,
                    'category_name': book.category.name if book.category else None,
                    'total_copies': book.total_copies,
                    'available_copies': book.available_copies,
                    'is_available': book.is_available(),
                    'status': 'Available' if book.is_available() else 'Not Available'
                }
            })
        else:
            return jsonify({
                'found': False,
                'message': f'No book found with ISBN: {barcode}'
            })
            
    except Exception as e:
        return jsonify({
            'found': False,
            'error': f'Error looking up barcode: {str(e)}'
        }), 500
