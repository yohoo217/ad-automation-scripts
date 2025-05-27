#!/usr/bin/env python3
"""
測試使用固定 iframe URL 的 PNN 640x200 功能
"""

from playwright.sync_api import sync_playwright
import time
import os
from datetime import datetime
from urllib.parse import quote_plus

def build_pnn_url_with_fixed_iframe(uuid):
    """建構使用固定 iframe URL 的 PNN URL"""
    
    # 模擬廣告資料
    media_title = "測試廣告標題"
    media_desc = "測試廣告描述內容"
    media_sponsor = "測試廣告主"
    media_cta = "立即了解"
    media_img = "https://example.com/test-image.jpg"
    
    # 固定的 iframe URL
    fixed_iframe_url = "https://moptt.tw/p/Baseball.M.1748234362.A.9E2"
    
    # 建構 catrun 網址
    catrun_url = f"https://tkcatrun.aotter.net/b/{uuid}/640x200"
    
    # PNN 參數格式
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
    
    base_url = "https://aotter.github.io/trek-ad-preview/pages/pnn-article/"
    full_url = f"{base_url}?{'&'.join(params)}"
    return full_url

def test_pnn_with_fixed_iframe(uuid, description):
    """測試使用固定 iframe URL 的 PNN 頁面"""
    print(f"\n=== 測試 {description} ===")
    
    # 建構 URL
    url = build_pnn_url_with_fixed_iframe(uuid)
    print(f"URL: {url}")
    
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
        )
        
        # 設置手機版 viewport
        context = browser.new_context(
            viewport={'width': 375, 'height': 812},
            user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
            extra_http_headers={
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
        )
        
        page = context.new_page()
        
        try:
            print("正在載入頁面...")
            response = page.goto(url, wait_until='domcontentloaded', timeout=30000)
            
            if response:
                print(f"HTTP 狀態碼: {response.status}")
            
            # 等待 3 秒（按照要求）
            print("等待 3 秒...")
            page.wait_for_timeout(3000)
            
            # 檢查頁面標題
            title = page.title()
            print(f"頁面標題: {title}")
            
            # 檢查 iframe
            iframes = page.query_selector_all('iframe')
            print(f"找到 {len(iframes)} 個 iframe")
            
            fixed_iframe_found = False
            tkcatrun_iframe_found = False
            
            for i, iframe in enumerate(iframes):
                try:
                    src = iframe.get_attribute('src')
                    if src:
                        if 'moptt.tw/p/Baseball.M.1748234362.A.9E2' in src:
                            print(f"  ✓ iframe {i+1}: 找到固定的 iframe URL")
                            fixed_iframe_found = True
                        elif 'tkcatrun.aotter.net' in src:
                            print(f"  ✓ iframe {i+1}: 找到 tkcatrun 廣告 iframe")
                            tkcatrun_iframe_found = True
                            
                            # 檢查廣告 iframe 內容
                            try:
                                ad_frame = iframe.content_frame()
                                if ad_frame:
                                    print(f"    -> 成功獲取廣告 iframe 內容")
                                    ad_elements = ad_frame.query_selector_all('[data-trek-ad]')
                                    print(f"    -> 找到 {len(ad_elements)} 個廣告元素")
                                else:
                                    print(f"    -> 無法獲取廣告 iframe 內容")
                            except Exception as iframe_error:
                                print(f"    -> 廣告 iframe 檢查失敗: {str(iframe_error)}")
                        else:
                            print(f"  iframe {i+1}: {src[:60]}...")
                except Exception as e:
                    print(f"  iframe {i+1}: 檢查失敗 - {str(e)}")
            
            # 結果驗證
            print(f"\n驗證結果:")
            print(f"  固定 iframe URL: {'✓' if fixed_iframe_found else '✗'}")
            print(f"  tkcatrun 廣告 iframe: {'✓' if tkcatrun_iframe_found else '✗'}")
            
            # 截圖
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            safe_description = description.replace(' ', '_').replace('/', '_')
            screenshot_path = f"pnn_fixed_iframe_{safe_description}_{timestamp}.png"
            
            print(f"正在截圖...")
            page.screenshot(path=screenshot_path, full_page=False)
            print(f"截圖已儲存: {os.path.abspath(screenshot_path)}")
            
            return True
            
        except Exception as e:
            print(f"測試失敗: {str(e)}")
            
            # 嘗試截圖錯誤頁面
            try:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                safe_description = description.replace(' ', '_').replace('/', '_')
                screenshot_path = f"pnn_fixed_iframe_{safe_description}_error_{timestamp}.png"
                page.screenshot(path=screenshot_path, full_page=False)
                print(f"錯誤頁面截圖: {os.path.abspath(screenshot_path)}")
            except:
                print("無法截圖錯誤頁面")
            
            return False
        
        finally:
            browser.close()

def main():
    """主函數"""
    print("測試使用固定 iframe URL 的 PNN 640x200 功能...")
    print("固定 iframe URL: https://moptt.tw/p/Baseball.M.1748234362.A.9E2")
    print("=" * 60)
    
    # 測試不同的 UUID
    test_cases = [
        ("3a438fe7-2392-4291-878d-a4d043bb52fd", "原始測試 UUID"),
        ("test-uuid-001", "測試 UUID 1"),
        ("test-uuid-002", "測試 UUID 2")
    ]
    
    results = []
    for uuid, description in test_cases:
        success = test_pnn_with_fixed_iframe(uuid, description)
        results.append((description, success))
    
    # 總結結果
    print(f"\n" + "=" * 60)
    print("測試結果總結:")
    for description, success in results:
        status = "✓ 成功" if success else "✗ 失敗"
        print(f"  {description}: {status}")
    
    success_count = sum(1 for _, success in results if success)
    print(f"\n成功: {success_count}/{len(results)}")

if __name__ == "__main__":
    main() 