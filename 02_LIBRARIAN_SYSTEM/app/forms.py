from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, IntegerField, SelectField, PasswordField, SubmitField, DateField
from wtforms.validators import DataRequired, Email, Length, NumberRange, Optional, ValidationError
from .models import Category

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class BookForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(min=1, max=200)])
    author = StringField('Author', validators=[DataRequired(), Length(min=1, max=100)])
    publisher = StringField('Publisher', validators=[Optional(), Length(max=100)])
    isbn = StringField('ISBN', validators=[Optional(), Length(max=20)])
    barcode_id = StringField('Barcode ID', validators=[Optional(), Length(max=50)])
    category_id = SelectField('Category', coerce=int, validators=[DataRequired()])
    total_copies = IntegerField('Total Copies', validators=[DataRequired(), NumberRange(min=1)])
    submit = SubmitField('Save Book')
    
    def __init__(self, *args, **kwargs):
        super(BookForm, self).__init__(*args, **kwargs)
        self.category_id.choices = [(c.id, c.name) for c in Category.query.all()]

class UserForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=1, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    role = SelectField('Role', choices=[('user', 'User'), ('librarian', 'Librarian')], default='user', validators=[DataRequired()])
    submit = SubmitField('Save User')
    
    def validate_role(self, field):
        if field.data not in ['user', 'librarian']:
            raise ValidationError('Invalid role selected')

class CategoryForm(FlaskForm):
    name = StringField('Category Name', validators=[DataRequired(), Length(min=1, max=50)])
    description = TextAreaField('Description', validators=[Optional()])
    submit = SubmitField('Save Category')

class IssueBookForm(FlaskForm):
    user_id = SelectField('User', coerce=int, validators=[DataRequired()])
    book_id = SelectField('Book', coerce=int, validators=[DataRequired()])
    due_date = DateField('Due Date', validators=[DataRequired()])
    submit = SubmitField('Issue Book')

class ReturnBookForm(FlaskForm):
    transaction_id = SelectField('Transaction', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Return Book')
