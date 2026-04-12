from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.utils.auth import is_email_allowed

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()

        if not email or not password:
            flash('Please enter email and password', 'error')
            return render_template('login.html')

        # Check if email is in allowed list
        if not is_email_allowed(email):
            flash('You do not have permission to use this system', 'error')
            return render_template('login.html')

        # Save user info to session
        session['user_email'] = email
        session['user_password'] = password  # Added: Save password for automation script use
        flash(f'Welcome back, {email}!', 'success')

        # Redirect to originally requested page
        next_page = request.args.get('next')
        return redirect(next_page) if next_page else redirect(url_for('main.index'))

    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    """Logout"""
    session.pop('user_email', None)
    session.pop('user_password', None)  # Added: Clear password
    flash('You have successfully logged out', 'info')
    return redirect(url_for('auth.login'))
