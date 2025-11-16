#!/usr/bin/env python
"""
Simple script to run the Flask application
"""
from app import app, init_db, get_local_ip
import socket
import ssl
import os

if __name__ == '__main__':
    print("Initializing database...")
    init_db()
    print("Database initialized successfully!")
    
    local_ip = get_local_ip()
    port = 5001
    
    # Check for SSL certificates in library_backend folder
    cert_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cert.pem')
    key_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'key.pem')
    
    use_https = os.path.exists(cert_path) and os.path.exists(key_path)
    protocol = 'https' if use_https else 'http'
    
    print("\n" + "="*70)
    print("Library Management System - Mobile Backend API")
    print("="*70)
    print(f"\n📱 Mobile App API URLs:")
    print(f"   Login:    {protocol}://{local_ip}:{port}/api/auth/login")
    print(f"   Health:   {protocol}://{local_ip}:{port}/api/health")
    print(f"   Base URL: {protocol}://{local_ip}:{port}/api")
    print(f"\n👤 Test User Credentials:")
    print(f"   Email: john@example.com")
    print(f"   Password: password123")
    print(f"\n📦 Flutter App Config:")
    print(f"   static const String baseUrl = '{protocol}://{local_ip}:{port}/api';")
    print(f"\n🔧 Test with curl:")
    print(f"   curl {protocol}://{local_ip}:{port}/api/health")
    
    if use_https:
        print(f"\n✅ Running with HTTPS (SSL enabled)")
    else:
        print(f"\n⚠️  Running with HTTP (SSL not found)")
    
    print("\nPress Ctrl+C to stop the server")
    print("="*70 + "\n")
    
    # Enable request logging
    import logging
    logging.basicConfig(level=logging.DEBUG)
    app.logger.setLevel(logging.DEBUG)
    
    if use_https:
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(cert_path, key_path)
        app.run(host='0.0.0.0', port=port, debug=True, ssl_context=context)
    else:
        app.run(host='0.0.0.0', port=port, debug=True)

