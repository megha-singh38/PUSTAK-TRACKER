from flask import Blueprint, render_template_string
from ..models import User, Book, Transaction, Category
from .. import db

db_viewer_bp = Blueprint('db_viewer', __name__)

@db_viewer_bp.route('/db-viewer')
def view_database():
    """Simple web interface to view database contents"""
    
    books = Book.query.all()
    users = User.query.all()
    categories = Category.query.all()
    transactions = Transaction.query.order_by(Transaction.created_at.desc()).limit(20).all()
    
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Database Viewer</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
        <div class="container mt-4">
            <h1>📊 Database Contents</h1>
            
            <div class="row">
                <div class="col-md-6">
                    <h3>📚 Books ({{ books|length }})</h3>
                    <div class="table-responsive">
                        <table class="table table-sm">
                            <thead><tr><th>Title</th><th>Author</th><th>Available</th></tr></thead>
                            <tbody>
                                {% for book in books %}
                                <tr>
                                    <td>{{ book.title }}</td>
                                    <td>{{ book.author }}</td>
                                    <td>{{ book.available_copies }}/{{ book.total_copies }}</td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>
                </div>
                
                <div class="col-md-6">
                    <h3>👥 Users ({{ users|length }})</h3>
                    <div class="table-responsive">
                        <table class="table table-sm">
                            <thead><tr><th>Name</th><th>Email</th><th>Role</th></tr></thead>
                            <tbody>
                                {% for user in users %}
                                <tr>
                                    <td>{{ user.name }}</td>
                                    <td>{{ user.email }}</td>
                                    <td><span class="badge bg-{{ 'primary' if user.role == 'librarian' else 'secondary' }}">{{ user.role }}</span></td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
            
            <div class="row mt-4">
                <div class="col-md-6">
                    <h3>📋 Categories ({{ categories|length }})</h3>
                    <div class="table-responsive">
                        <table class="table table-sm">
                            <thead><tr><th>Name</th><th>Description</th></tr></thead>
                            <tbody>
                                {% for cat in categories %}
                                <tr>
                                    <td>{{ cat.name }}</td>
                                    <td>{{ cat.description }}</td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>
                </div>
                
                <div class="col-md-6">
                    <h3>🔄 Recent Transactions</h3>
                    <div class="table-responsive">
                        <table class="table table-sm">
                            <thead><tr><th>User</th><th>Book</th><th>Status</th></tr></thead>
                            <tbody>
                                {% for trans in transactions %}
                                <tr>
                                    <td>{{ trans.user.name }}</td>
                                    <td>{{ trans.book.title }}</td>
                                    <td><span class="badge bg-{{ 'success' if trans.status == 'returned' else 'warning' if trans.status == 'issued' else 'danger' }}">{{ trans.status }}</span></td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
            
            <div class="mt-4">
                <a href="{{ url_for('web.dashboard') }}" class="btn btn-primary">← Back to Dashboard</a>
            </div>
        </div>
    </body>
    </html>
    """
    
    return render_template_string(html, books=books, users=users, categories=categories, transactions=transactions)