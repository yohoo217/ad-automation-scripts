from flask import Flask
from dotenv import load_dotenv
import logging
import os

# 載入環境變數
load_dotenv()

def create_app():
    """應用工廠函數"""
    # 設置正確的模板和靜態檔案路徑
    template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'templates'))
    static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'static'))
    
    app = Flask(__name__, 
                template_folder=template_dir,
                static_folder=static_dir)
    app.secret_key = 'your_very_secret_key'  # 記得更換為一個安全的密鑰
    
    # 配置上傳文件夾
    UPLOAD_FOLDER = 'uploads'
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 限制上傳大小為 16MB
    
    # 配置日誌
    if not os.path.exists('logs'):
        os.makedirs('logs')
        
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/app.log'),
            logging.StreamHandler()
        ]
    )
    
    # 關閉 Werkzeug HTTP 請求日誌
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    
    # 註冊藍圖
    from app.routes import register_blueprints
    register_blueprints(app)
    
    return app 