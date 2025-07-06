import os
import ssl
import sys
from app import create_app, socketio, db
from flask import redirect, url_for, request, flash
from sqlalchemy.exc import IntegrityError, OperationalError
from app.models import User, Role
from app.utils.database_init import initialize_database, check_database_health

app = create_app()

# Setup auth redirect handler
@app.before_request
def check_first_run():
    # File integrity is now always in warning-only mode - no redirection needed
    
    # Check if database needs initialization
    if not User.query.first() and request.path != '/auth/login':
        # No users exist, database needs initialization
        flash('Database is being initialized. Please wait...', 'info')
        return redirect(url_for('auth.login'))

# Custom error handler for database issues
@app.errorhandler(IntegrityError)
def handle_integrity_error(error):
    if "UNIQUE constraint failed: user.email" in str(error):
        flash("Error: Email address must be unique. If you're trying to create a user without an email, " 
              "run 'python fix_emails.py' to fix database issues.", 'error')
    else:
        flash(f"Database integrity error: {str(error)}", 'error')
    return redirect(url_for('auth.manage_users'))

@app.errorhandler(OperationalError)
def handle_operational_error(error):
    flash(f"Database error: {str(error)}", 'error')
    return redirect(url_for('main.index'))

if __name__ == '__main__':
    # Initialize database first
    print("Starting FRC Scouting Platform...")
    with app.app_context():
        try:
            # Check if database needs initialization
            if not check_database_health():
                print("Database needs initialization...")
                initialize_database()
            else:
                print("Database is healthy and ready.")
        except Exception as e:
            print(f"Database initialization error: {e}")
            print("Attempting to initialize database...")
            initialize_database()
    
    # Initialize file integrity monitoring
    print("Initializing file integrity monitoring...")
    if hasattr(app, 'file_integrity_monitor'):
        monitor = app.file_integrity_monitor
        
        # Initialize checksums if not already done
        if not monitor.checksums:
            monitor.initialize_checksums()
            print(f"File integrity monitoring initialized with {len(monitor.checksums)} files.")
        else:
            print(f"File integrity monitoring loaded with {len(monitor.checksums)} files.")
        
        # Perform integrity check (only at startup)
        if not monitor.check_integrity():
            print("WARNING: File integrity compromised detected on startup!")
            print("Warning-only mode is enabled - you can continue using the application.")
            monitor.integrity_compromised = True  # Mark as compromised for the warning banner
        else:
            print("File integrity verified - all files are intact.")
    
    # Check if SSL certificate files exist
    cert_file = os.path.join(os.path.dirname(__file__), 'ssl', 'cert.pem')
    key_file = os.path.join(os.path.dirname(__file__), 'ssl', 'key.pem')
    
    # Check if we have SSL certificates
    use_ssl = os.path.exists(cert_file) and os.path.exists(key_file)
    
    if not use_ssl:
        # Create directory for SSL certificates if it doesn't exist
        ssl_dir = os.path.join(os.path.dirname(__file__), 'ssl')
        if not os.path.exists(ssl_dir):
            os.makedirs(ssl_dir)
            
        print("SSL certificates not found. Generating self-signed certificates...")
        try:
            # Try to generate self-signed certificates
            from OpenSSL import crypto
            
            # Create a key pair
            k = crypto.PKey()
            k.generate_key(crypto.TYPE_RSA, 2048)
            
            # Create a self-signed certificate
            cert = crypto.X509()
            cert.get_subject().C = "US"
            cert.get_subject().ST = "State"
            cert.get_subject().L = "City"
            cert.get_subject().O = "Team 5454"
            cert.get_subject().OU = "Scouting App"
            cert.get_subject().CN = "0.0.0.0"
            cert.set_serial_number(1000)
            cert.gmtime_adj_notBefore(0)
            cert.gmtime_adj_notAfter(10*365*24*60*60)  # 10 years
            cert.set_issuer(cert.get_subject())
            cert.set_pubkey(k)
            cert.sign(k, 'sha256')
            
            # Save the certificate and key
            with open(cert_file, "wb") as cf:
                cf.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))
            with open(key_file, "wb") as kf:
                kf.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, k))
                
            use_ssl = True
            print("Self-signed SSL certificates generated successfully.")
            
        except ImportError:
            print("Warning: pyOpenSSL not installed. Unable to generate SSL certificates.")
            print("To enable SSL, install pyOpenSSL or manually add cert.pem and key.pem to the ssl directory.")
            print("Running in HTTP mode (camera features may not work in some browsers).")
        except Exception as e:
            print(f"Error generating SSL certificates: {e}")
            print("Running in HTTP mode (camera features may not work in some browsers).")
    
    if use_ssl:
        print("Starting server with SSL support (HTTPS)...")
        try:
            socketio.run(
                app, 
                debug=True, 
                host='0.0.0.0',
                port=5000,
                ssl_context=(cert_file, key_file),
                allow_unsafe_werkzeug=True
            )
        except KeyboardInterrupt:
            print("\nShutting down server...")
            sys.exit(0)
    else:
        print("Starting server without SSL (HTTP)...")
        print("Warning: Camera access for QR scanning may not work without HTTPS.")
        print("For development, access the application at http://localhost:5000")
        try:
            socketio.run(
                app, 
                debug=True, 
                host='0.0.0.0',
                port=5000,
                allow_unsafe_werkzeug=True
            )
        except KeyboardInterrupt:
            print("\nShutting down server...")
            sys.exit(0)