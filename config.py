import os
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

ALLOWED_EMAILS = [
    email.strip()
    for email in os.getenv(
        'ALLOWED_EMAILS',
        'portfolio-owner@example.com,reviewer@example.edu'
    ).split(',')
    if email.strip()
]


def get_platform_credentials():
    """動態獲取平台登入帳號密碼。"""
    env_email = os.getenv('PLATFORM_EMAIL')
    env_password = os.getenv('PLATFORM_PASSWORD')

    if env_email and env_password:
        return env_email, env_password

    try:
        from flask import session
        session_email = session.get('user_email')
        session_password = session.get('user_password')

        if session_email and session_password:
            return session_email, session_password
    except (RuntimeError, ImportError):
        pass

    return None, None

def get_email():
    """取得平台登入帳號。"""
    email, _ = get_platform_credentials()
    return email


def get_password():
    """取得平台登入密碼。"""
    _, password = get_platform_credentials()
    return password


EMAIL = os.getenv('PLATFORM_EMAIL')
PASSWORD = os.getenv('PLATFORM_PASSWORD')
