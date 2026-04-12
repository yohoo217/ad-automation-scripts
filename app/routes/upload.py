from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from datetime import datetime
import os

upload_bp = Blueprint('upload', __name__)

@upload_bp.route('/upload', methods=['POST'])
def upload_file():
    """File upload processing"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if file:
        # Create subdirectory based on date
        today = datetime.now().strftime('%Y%m%d')
        upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], today)

        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)

        # Save file
        filename = secure_filename(file.filename)
        file_path = os.path.join(upload_dir, filename)
        file.save(file_path)

        # Return file path
        return jsonify({
            'success': True,
            'file_path': os.path.abspath(file_path)
        })
