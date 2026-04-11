from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from datetime import datetime
import os

upload_bp = Blueprint('upload', __name__)

@upload_bp.route('/upload', methods=['POST'])
def upload_file():
    """檔案上傳處理"""
    if 'file' not in request.files:
        return jsonify({'error': '沒有檔案被上傳'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '沒有選擇檔案'}), 400
    
    if file:
        # 創建基於日期的子目錄
        today = datetime.now().strftime('%Y%m%d')
        upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], today)
        
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)
        
        # 保存文件
        filename = secure_filename(file.filename)
        file_path = os.path.join(upload_dir, filename)
        file.save(file_path)
        
        # 返回文件路徑
        return jsonify({
            'success': True,
            'file_path': os.path.abspath(file_path)
        }) 