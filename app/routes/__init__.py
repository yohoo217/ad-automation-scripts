def register_blueprints(app):
    """註冊所有藍圖"""
    from .main import main_bp
    from .native_ad import native_ad_bp
    from .screenshot import screenshot_bp
    from .upload import upload_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(native_ad_bp)
    app.register_blueprint(screenshot_bp)
    app.register_blueprint(upload_bp) 