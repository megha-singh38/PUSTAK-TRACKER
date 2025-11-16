import http.server
import ssl
import socketserver
import os
import socket

PORT = 9000

class MobileHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()
    
    def do_GET(self):
        if self.path == '/' or self.path == '/scanner':
            self.path = '/mobile_scanner.html'
        super().do_GET()

def get_local_ip():
    """Get the local IP address"""
    try:
        # Connect to a remote server to determine local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except:
        return "localhost"

# Check if certificates exist
if not os.path.exists('cert.pem') or not os.path.exists('key.pem'):
    print("Certificates not found. Creating self-signed certificates...")
    print("Run this command to create certificates:")
    print("openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes")
    
    # Try to create certificates automatically (requires OpenSSL)
    try:
        import subprocess
        subprocess.run([
            'openssl', 'req', '-x509', '-newkey', 'rsa:4096', 
            '-keyout', 'key.pem', '-out', 'cert.pem', '-days', '365', '-nodes',
            '-subj', '/C=IN/ST=State/L=City/O=Library/CN=localhost'
        ], check=True)
        print("✓ Certificates created automatically")
    except:
        print("❌ Could not create certificates automatically")
        print("Please install OpenSSL and run the command above")
        exit(1)

# Get local IP
local_ip = get_local_ip()

with socketserver.TCPServer(("", PORT), MobileHTTPRequestHandler) as httpd:
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain('cert.pem', 'key.pem')
    httpd.socket = context.wrap_socket(httpd.socket, server_side=True)
    
    print("📱 MOBILE SCANNER SERVER READY")
    print("=" * 40)
    print(f"📱 Scanner URL: https://{local_ip}:{PORT}/scanner")
    print("⚠️  Accept security warning on phone")
    print("=" * 40)
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")