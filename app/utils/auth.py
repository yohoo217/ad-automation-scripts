from functools import wraps
from flask import session, redirect, url_for, flash
import config

def login_required(f):
    """登入驗證裝飾器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_email' not in session:
            flash('請先登入', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def is_email_allowed(email):
    """檢查電子郵件是否在允許清單中"""
    return email.lower() in [e.lower() for e in config.ALLOWED_EMAILS]

def get_current_user():
    """取得目前登入的使用者"""
    return session.get('user_email') 