from flask import Flask
from dotenv import load_dotenv
import logging
import os

# Load environment variables
load_dotenv()

def create_app():
    """Application factory function"""
    # Set correct template and static file paths
    template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'templates'))
    static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'static'))

    app = Flask(__name__,
                template_folder=template_dir,
                static_folder=static_dir)
    app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

    # Configure upload folder
    UPLOAD_FOLDER = 'uploads'
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Limit upload size to 16MB

    # Configure logging
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

    # Disable Werkzeug HTTP request logging
    logging.getLogger('werkzeug').setLevel(logging.WARNING)

    # Register blueprints
    from app.routes import register_blueprints
    register_blueprints(app)

    return app
