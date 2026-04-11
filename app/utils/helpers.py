"""通用輔助函數"""

import os

def format_file_size(size_bytes):
    """格式化檔案大小"""
    if size_bytes > 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f}MB"
    elif size_bytes > 1024:
        return f"{size_bytes / 1024:.1f}KB"
    else:
        return f"{size_bytes}B"

def get_device_configs():
    """取得裝置配置"""
    return {
        'iphone_x': {'width': 375, 'height': 812, 'name': 'iPhone X'},
        'iphone_se': {'width': 375, 'height': 667, 'name': 'iPhone SE'},
        'iphone_plus': {'width': 414, 'height': 736, 'name': 'iPhone Plus'},
        'android': {'width': 360, 'height': 640, 'name': 'Android 標準'},
        'tablet': {'width': 768, 'height': 1024, 'name': '平板電腦'},
        'desktop': {'width': 1920, 'height': 1080, 'name': '桌上型電腦'}
    }

def get_default_cookie():
    """取得預設 cookie - 需要自行設定"""
    return os.getenv("PLATFORM_COOKIE", "")
