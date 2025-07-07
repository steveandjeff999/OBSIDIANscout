# Authentication Setup Instructions

## Steps to initialize and test the authentication system:

1. Make sure you have installed all dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Initialize the authentication system by running:
   ```
   python init_auth.py
   ```
   This will create:
   - Admin user: admin (password: password)
   - Roles: admin, analytics, scout
   
3. If you encounter any email-related errors, run the email fix script:
   ```
   python fix_emails.py
   ```
   This will fix any issues with empty email fields in the database.

3. Start the application:
   ```
   python run.py
   ```

4. Open your browser and navigate to http://127.0.0.1:5000/

5. You will be redirected to the login page. Log in with:
   - Username: admin
   - Password: password

6. Once logged in as admin, you can:
   - Access the User Management page from your user dropdown menu
   - Add new users with different roles
   - Test the system by logging in with different user accounts

7. **Important:** Set up your first API credentials:
   - Navigate to the API configuration section in game_config.json
   - Enter your first API username and key
   - This is required for the application to function properly with external data sources
   - Restart the program for changes to take effect

## Role-based access:

- **Admin users** can access everything
- **Analytics users** can access all data and reports but not user management
- **Scout users** can only access scouting features and cannot access the main dashboard

## Windows users:

Run the `setup_auth.bat` script for a guided setup process:
```
setup_auth.bat
```

## Troubleshooting:

If you encounter any issues:

1. Make sure the database file exists at `instance/scouting.db`
2. Check that Flask-Login is installed (`pip install Flask-Login`)
3. If login isn't working, try resetting the admin password:
   ```python
   from app import create_app, db
   from app.models import User
   
   app = create_app()
   with app.app_context():
       user = User.query.filter_by(username="admin").first()
       if user:
           user.set_password("password")
           db.session.commit()
           print("Password reset successfully")
   ```

4. If all else fails, you can reset the database:
   ```
   rm instance/scouting.db
   python init_auth.py
   ```
