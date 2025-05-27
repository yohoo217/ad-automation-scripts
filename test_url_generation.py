#!/usr/bin/env python3
"""
測試 app.py 中的 URL 生成邏輯
"""

from urllib.parse import quote_plus, urlparse, parse_qs

def build_native_screenshot_url_test(adunit_data, size, template):
    """測試版本的 build_native_screenshot_url 函數"""
    if not adunit_data:
        return None
        
    # 從 AdUnit 資料中取得相關欄位
    media_title = adunit_data.get('title', '')
    media_desc = adunit_data.get('text', '')
    media_sponsor = adunit_data.get('advertiserName', '')
    media_cta = adunit_data.get('callToAction', '')
    url_original = adunit_data.get('url_original', '')
    uuid = adunit_data.get('uuid', '')
    media_img = adunit_data.get('image_path_m', '')
    
    # 建構 catrun 網址
    catrun_url = f"https://tkcatrun.aotter.net/b/{uuid}/{size}"
    
    # 根據尺寸和模板類型選擇對應的 URL 模板
    url_templates = {
        '640x200': {
            'pnn-article': {
                'base_url': 'https://aotter.github.io/trek-ad-preview/pages/pnn-article/',
                'use_iframe': True
            }
        }
    }
    
    # 根據尺寸和模板決定使用哪個配置
    size_templates = url_templates.get(size, {})
    template_config = size_templates.get(template)
    
    if not template_config:
        return None
    
    base_url = template_config.get('base_url')
    if not base_url:
        return None
    
    # 根據不同模板類型建構參數
    if template == 'pnn-article' and size == '640x200':
        # PNN 使用特定參數格式，固定使用指定的 iframe 網址
        fixed_iframe_url = "https://moptt.tw/p/Baseball.M.1748234362.A.9E2"
        params = [
            f"iframe_title={quote_plus(media_title)}",
            f"iframe_desc={quote_plus(media_desc)}",
            f"iframe_sponsor={quote_plus(media_sponsor)}",
            f"iframe_cta={quote_plus(media_cta)}",
            f"iframe_url={quote_plus(fixed_iframe_url)}",
            f"iframe_img={quote_plus(media_img)}",
            f"trek-debug-place=5a41c4d0-b268-43b2-9536-d774f46c33bf",
            f"trek-debug-catrun={quote_plus(catrun_url)}"
        ]
    else:
        return None
    
    full_url = f"{base_url}?{'&'.join(params)}"
    return full_url

def main():
    """測試函數"""
    print("測試 640x200 PNN 頁面的 URL 生成邏輯...")
    print("=" * 60)
    
    # 模擬 AdUnit 資料
    test_adunit = {
        'uuid': '3a438fe7-2392-4291-878d-a4d043bb52fd',
        'title': '測試廣告標題',
        'text': '測試廣告描述',
        'advertiserName': '測試廣告主',
        'callToAction': '立即了解',
        'url_original': 'https://example.com/original-url',  # 這個應該被忽略
        'image_path_m': 'https://example.com/image.jpg'
    }
    
    # 測試 640x200 PNN 模板
    url = build_native_screenshot_url_test(test_adunit, '640x200', 'pnn-article')
    
    if url:
        print(f"生成的 URL:")
        print(url)
        print()
        
        # 解析並檢查參數
        parsed_url = urlparse(url)
        params = parse_qs(parsed_url.query)
        
        print("URL 參數檢查:")
        print(f"  基本 URL: {parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}")
        
        # 檢查關鍵參數
        key_params = [
            'iframe_title',
            'iframe_desc', 
            'iframe_sponsor',
            'iframe_cta',
            'iframe_url',
            'iframe_img',
            'trek-debug-place',
            'trek-debug-catrun'
        ]
        
        for param in key_params:
            value = params.get(param, [''])[0]
            if param == 'iframe_url':
                # 特別檢查 iframe_url 是否使用了固定的網址
                expected_url = "https://moptt.tw/p/Baseball.M.1748234362.A.9E2"
                is_correct = value == expected_url
                status = "✓ 正確" if is_correct else "✗ 錯誤"
                print(f"  {param}: {status}")
                print(f"    期望: {expected_url}")
                print(f"    實際: {value}")
            elif param == 'trek-debug-catrun':
                expected_catrun = f"https://tkcatrun.aotter.net/b/{test_adunit['uuid']}/640x200"
                is_correct = value == expected_catrun
                status = "✓ 正確" if is_correct else "✗ 錯誤"
                print(f"  {param}: {status}")
                print(f"    期望: {expected_catrun}")
                print(f"    實際: {value}")
            else:
                print(f"  {param}: {value}")
        
        print("\n重要檢查:")
        iframe_url = params.get('iframe_url', [''])[0]
        if "https://moptt.tw/p/Baseball.M.1748234362.A.9E2" in iframe_url:
            print("✓ iframe_url 正確使用了固定的網址")
        else:
            print("✗ iframe_url 沒有使用固定的網址")
        
        if test_adunit['url_original'] not in url:
            print("✓ 原始 URL 被正確忽略")
        else:
            print("✗ 原始 URL 仍然被使用")
            
    else:
        print("✗ URL 生成失敗")

if __name__ == "__main__":
    main() 