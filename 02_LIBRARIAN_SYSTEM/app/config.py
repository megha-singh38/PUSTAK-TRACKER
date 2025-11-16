import os
from datetime import timedelta

# Get absolute path to shared database
# This file is at: 02_LIBRARIAN_SYSTEM/app/config.py
# We need to go up 2 levels to get to the root, then into 03_SHARED_RESOURCES
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SHARED_DB_PATH = os.path.join(BASE_DIR, '03_SHARED_RESOURCES', 'instance', 'pustak_tracker.db')

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'supersecret-key-change-in-production')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    FINE_RATE = int(os.getenv('FINE_RATE', 5))  # Rs per day
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{SHARED_DB_PATH}'

class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{SHARED_DB_PATH}'
