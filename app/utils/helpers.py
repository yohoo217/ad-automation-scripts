"""通用輔助函數"""

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
    """取得預設 cookie"""
    return "AOTTERBD_SESSION=757418f543a95a889184e798ec5ab66d4fad04e5-lats=1724229220332&sso=PIg4zu/Vdnn/A15vMEimFlVAGliNhoWlVd5FTvtEMRAFpk/VvBGvAetanw8DLATSLexy9pee/t52uNojvoFS2Q==;aotter=eyJ1c2VyIjp7ImlkIjoiNjNkYjRkNDBjOTFiNTUyMmViMjk4YjBkIiwiZW1haWwiOiJpYW4uY2hlbkBhb3R0ZXIubmV0IiwiY3JlYXRlZEF0IjoxNjc1MzE2NTQ0LCJlbWFpbFZlcmlmaWVkIjp0cnVlLCJsZWdhY3lJZCI6bnVsbCwibGVnYWN5U2VxSWQiOjE2NzUzMTY1NDQ3ODI5NzQwMDB9LCJhY2Nlc3NUb2tlbiI6IjJkYjQyZTNkOTM5MDUzMjdmODgyZmYwMDRiZmI4YmEzZjBhNTlmMDQwYzhiN2Y4NGY5MmZmZTIzYTU0ZTQ2MDQiLCJ1ZWEiOm51bGx9; _Secure-1PSID=vlPPgXupFroiSjP1/A02minugZVZDgIG4K; _Secure-1PSIDCC=g.a000mwhavReSVd1vN09AVTswXkPAhyuW7Tgj8-JFhj-FZya9I_l1B6W2gqTIWAtQUTQMkTxoAwACgYKAW0SARISFQHGX2MiC--NJ2PzCzDpJ0m3odxHhxoVAUF8yKr8r49abq8oe4UxCA0t_QCW0076; _Secure-3PSID=AKEyXzUuXI1zywmFmkEBEBHfg6GRkRM9cJ9BiJZxmaR46x5im_krhaPtmL4Jhw8gQsz5uFFkfbc; _Secure-3PSIDCC=sidts-CjEBUFGohzUF6oK3ZMACCk2peoDBDp6djBwJhGc4Lxgu2zOlzbVFeVpXF4q1TYZ5ba6cEAA" 