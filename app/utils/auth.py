from functools import wraps
from flask import session, redirect, url_for, flash
import config

def login_required(f):
    """Login verification decorator"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_email' not in session:
            flash('Please log in first', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def is_email_allowed(email):
    """Check if email is in allowed list"""
    return email.lower() in [e.lower() for e in config.ALLOWED_EMAILS]

def get_current_user():
    """Get current logged in user"""
    return session.get('user_email')
