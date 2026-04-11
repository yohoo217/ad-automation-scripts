from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.utils.auth import is_email_allowed

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """登入頁面"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        
        if not email or not password:
            flash('請輸入電子郵件和密碼', 'error')
            return render_template('login.html')
        
        # 檢查電子郵件是否在允許清單中
        if not is_email_allowed(email):
            flash('您沒有權限使用此系統', 'error')
            return render_template('login.html')
        
        # 儲存使用者資訊到 session
        session['user_email'] = email
        session['user_password'] = password  # 新增：儲存密碼供自動化腳本使用
        flash(f'歡迎回來, {email}!', 'success')
        
        # 重定向到原本想要訪問的頁面
        next_page = request.args.get('next')
        return redirect(next_page) if next_page else redirect(url_for('main.index'))
    
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    """登出"""
    session.pop('user_email', None)
    session.pop('user_password', None)  # 新增：清除密碼
    flash('您已成功登出', 'info')
    return redirect(url_for('auth.login')) 