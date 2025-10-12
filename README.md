# Pustak Tracker - Library Management System

A comprehensive Flask-based Library Management System with both web interface and REST API support.

## 🚀 Features

### 📚 Core Functionality
- **Book Management**: Add, edit, delete, and search books
- **User Management**: Manage library members and librarians
- **Transaction Management**: Issue and return books with automatic tracking
- **Fine Calculation**: Automatic fine calculation for overdue books
- **Category Management**: Organize books by categories
- **Dashboard**: Real-time statistics and overview

### 🌐 Web Interface
- **Responsive Design**: Bootstrap 5 with modern UI
- **Librarian Dashboard**: Complete management interface
- **Search & Filter**: Advanced search capabilities
- **Real-time Updates**: Live statistics and notifications

### 🔌 REST API
- **JWT Authentication**: Secure API access
- **CRUD Operations**: Full REST API for all entities
- **Mobile Ready**: JSON responses for mobile apps
- **Documentation**: Well-structured API endpoints


## 📋 Requirements

- Python 3.11+
- MySQL 8.0+

## 🛠️ Installation

### Local Development

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd pustak-tracker
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp env.example .env
   # Edit .env with your configuration
   ```

5. **Initialize database**
   ```bash
   python run.py init-db
   ```

6. **Run the application**
   ```bash
   python run.py
   ```


## 🔑 Default Login

- **Email**: librarian@pustak.com
- **Password**: admin123

## 📖 API Documentation

### Authentication
```bash
POST /api/auth/login
{
  "email": "librarian@pustak.com",
  "password": "admin123"
}
```

### Books API
```bash
# Get all books
GET /api/books

# Create book
POST /api/books
{
  "title": "Book Title",
  "author": "Author Name",
  "category_id": 1,
  "total_copies": 5
}

# Update book
PUT /api/books/{id}

# Delete book
DELETE /api/books/{id}
```

### Transactions API
```bash
# Issue book
POST /api/transactions/issue
{
  "user_id": 1,
  "book_id": 1,
  "due_date": "2024-01-15"
}

# Return book
POST /api/transactions/return
{
  "transaction_id": 1
}

# Get overdue books
GET /api/transactions/overdue
```

## 🗂️ Project Structure

```
pustak_tracker/
├── app/
│   ├── __init__.py          # Flask app factory
│   ├── config.py            # Configuration settings
│   ├── models.py            # SQLAlchemy models
│   ├── forms.py             # Flask-WTF forms
│   ├── utils.py             # Utility functions
│   ├── routes/
│   │   ├── web_routes.py    # Web interface routes
│   │   └── api_routes.py    # REST API routes
│   ├── templates/           # Jinja2 templates
│   └── static/              # CSS, JS, images
├── requirements.txt         # Python dependencies
├── run.py                   # Application entry point
└── README.md               # This file
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `FLASK_ENV` | Flask environment | `development` |
| `SECRET_KEY` | Flask secret key | Required |
| `DATABASE_URL` | Database connection string | Required |
| `FINE_RATE` | Fine per day (₹) | `5` |
| `JWT_SECRET_KEY` | JWT secret key | Required |

### Database Configuration

The application supports MySQL with the following connection string format:
```
mysql+pymysql://username:password@host:port/database_name
```

## 🚀 Deployment

### Production Deployment

1. **Set production environment**
   ```bash
   export FLASK_ENV=production
   ```

2. **Use production database**
   ```bash
   export DATABASE_URL=mysql+pymysql://user:pass@prod-host/pustak_tracker
   ```

3. **Run with Gunicorn**
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5000 run:app
   ```


## 🧪 Testing

### Manual Testing Checklist

- [ ] Login/Logout functionality
- [ ] Add/Edit/Delete books
- [ ] Add/Edit/Delete users
- [ ] Issue and return books
- [ ] Fine calculation
- [ ] Overdue book tracking
- [ ] API endpoints
- [ ] Search functionality
- [ ] Responsive design

### API Testing

Use tools like Postman or curl to test API endpoints:

```bash
# Test login
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"librarian@pustak.com","password":"admin123"}'

# Test get books (with JWT token)
curl -X GET http://localhost:5000/api/books \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## 🔄 Maintenance

### Daily Tasks
- Calculate overdue fines: `python run.py calculate-fines`
- Check system health
- Monitor database performance

### Weekly Tasks
- Review overdue books
- Update book inventory
- Backup database

### Monthly Tasks
- Generate reports
- Update system dependencies
- Review user accounts

## 🐛 Troubleshooting

### Common Issues

1. **Database Connection Error**
   - Check MySQL service is running
   - Verify connection string in environment variables
   - Ensure database exists

2. **Import Errors**
   - Activate virtual environment
   - Install all requirements: `pip install -r requirements.txt`

3. **Permission Errors**
   - Check file permissions
   - Ensure proper user access

4. **Port Already in Use**
   - Change port in run.py or use different port
   - Kill existing process using the port

## 📝 License

This project is licensed under the MIT License.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📞 Support

For support and questions:
- Create an issue in the repository
- Check the documentation
- Review the troubleshooting section

---

**Pustak Tracker** - Making library management simple and efficient! 📚✨
