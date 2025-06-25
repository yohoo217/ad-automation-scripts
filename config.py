import os
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

# 允許登入的帳號白名單
ALLOWED_EMAILS = [
    'ian.chen@aotter.net',
    'cjay@aotter.net', 
    'coki.lu@aotter.net',
    'john.chiu@aotter.net',
    'phsu@aotter.net',
    'robert.hsueh@aotter.net',
    'smallmouth@aotter.net'
]

def get_trek_credentials():
    """動態獲取 Trek 系統帳號密碼"""
    # 優先從環境變數獲取
    env_email = os.getenv('TREK_EMAIL')
    env_password = os.getenv('TREK_PASSWORD')
    
    if env_email and env_password:
        return env_email, env_password
    
    # 如果環境變數沒有，從 session 獲取（網頁登入的帳號密碼）
    try:
        from flask import session
        session_email = session.get('user_email')
        session_password = session.get('user_password')
        
        if session_email and session_password:
            return session_email, session_password
    except (RuntimeError, ImportError):
        # 在非 Flask 請求上下文中調用時會出現此錯誤
        pass
    
    # 如果都沒有，返回空值
    return None, None

def get_email():
    """獲取 Trek 系統帳號"""
    email, _ = get_trek_credentials()
    return email

def get_password():
    """獲取 Trek 系統密碼"""
    _, password = get_trek_credentials()
    return password

# 為了向後兼容，提供靜態值（用於非 Flask 環境）
EMAIL = os.getenv('TREK_EMAIL')
PASSWORD = os.getenv('TREK_PASSWORD')
