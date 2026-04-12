"""Utility helper functions"""

import os

def format_file_size(size_bytes):
    """Format file size"""
    if size_bytes > 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f}MB"
    elif size_bytes > 1024:
        return f"{size_bytes / 1024:.1f}KB"
    else:
        return f"{size_bytes}B"

def get_device_configs():
    """Get device configurations"""
    return {
        'iphone_x': {'width': 375, 'height': 812, 'name': 'iPhone X'},
        'iphone_se': {'width': 375, 'height': 667, 'name': 'iPhone SE'},
        'iphone_plus': {'width': 414, 'height': 736, 'name': 'iPhone Plus'},
        'android': {'width': 360, 'height': 640, 'name': 'Android Standard'},
        'tablet': {'width': 768, 'height': 1024, 'name': 'Tablet'},
        'desktop': {'width': 1920, 'height': 1080, 'name': 'Desktop'}
    }

def get_default_cookie():
    """Get default cookie - needs to be set by user"""
    return os.getenv("PLATFORM_COOKIE", "")
