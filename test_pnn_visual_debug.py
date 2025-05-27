#!/usr/bin/env python3
"""
可視化調試 PNN 640x200 頁面載入過程
用於觀察瀏覽器實際載入狀況
"""

from playwright.sync_api import sync_playwright
import time
import os
from datetime import datetime
from urllib.parse import quote_plus

def build_pnn_debug_url(uuid):
    """建構 PNN 調試用 URL"""
    
    # 模擬廣告資料
    media_title = "測試廣告標題"
    media_desc = "測試廣告描述內容，這是一個測試用的描述"
    media_sponsor = "測試廣告主"
    media_cta = "立即了解"
    media_img = "https://via.placeholder.com/640x200/0066cc/ffffff?text=Test+Ad"
    
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

def visual_debug_pnn(uuid, description):
    """可視化調試 PNN 頁面載入過程"""
    print(f"\n=== 可視化調試: {description} ===")
    
    # 建構 URL
    url = build_pnn_debug_url(uuid)
    print(f"目標 URL: {url}")
    print(f"注意：瀏覽器將會以可視模式啟動，每個步驟間隔 2 秒")
    print("按 Enter 開始...")
    input()
    
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=False,  # 可視模式
            slow_mo=2000,    # 每個動作間隔 2 秒
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
            print("步驟 1: 開始載入頁面...")
            response = page.goto(url, wait_until='domcontentloaded', timeout=30000)
            
            if response:
                print(f"HTTP 狀態碼: {response.status}")
            
            print("步驟 2: 等待 3 秒讓頁面穩定...")
            page.wait_for_timeout(3000)
            
            # 檢查頁面標題
            title = page.title()
            print(f"頁面標題: {title}")
            
            print("步驟 3: 檢查所有 iframe...")
            iframes = page.query_selector_all('iframe')
            print(f"找到 {len(iframes)} 個 iframe")
            
            fixed_iframe_found = False
            tkcatrun_iframe = None
            
            for i, iframe in enumerate(iframes):
                try:
                    src = iframe.get_attribute('src')
                    if src:
                        print(f"  iframe {i+1}: {src[:80]}...")
                        if 'moptt.tw/p/Baseball.M.1748234362.A.9E2' in src:
                            print(f"    ✓ 這是固定的 iframe URL")
                            fixed_iframe_found = True
                        elif 'tkcatrun.aotter.net' in src:
                            print(f"    ✓ 這是 tkcatrun 廣告 iframe")
                            tkcatrun_iframe = iframe
                except Exception as e:
                    print(f"  iframe {i+1}: 檢查失敗 - {str(e)}")
            
            if tkcatrun_iframe:
                print("步驟 4: 檢查 tkcatrun 廣告 iframe 內容...")
                try:
                    ad_frame = tkcatrun_iframe.content_frame()
                    if ad_frame:
                        print("  ✓ 成功獲取廣告 iframe 內容")
                        
                        print("  步驟 4a: 在 iframe 內等待 2 秒讓 CatRun 初始化...")
                        ad_frame.wait_for_timeout(2000)
                        
                        print("  步驟 4b: 檢查廣告元素...")
                        ad_elements = ad_frame.query_selector_all('[data-trek-ad]')
                        print(f"  找到 {len(ad_elements)} 個廣告元素")
                        
                        if len(ad_elements) > 0:
                            print("  ✓ 找到廣告元素，準備截圖...")
                            
                            # 截圖準備
                            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                            safe_description = description.replace(' ', '_').replace('/', '_')
                            
                            # 截圖主頁面
                            print("步驟 5a: 截圖主頁面...")
                            main_screenshot = f"pnn_debug_main_{safe_description}_{timestamp}.png"
                            page.screenshot(path=main_screenshot, full_page=False)
                            print(f"主頁面截圖: {os.path.abspath(main_screenshot)}")
                            
                            # 截圖廣告 iframe
                            print("步驟 5b: 截圖廣告 iframe...")
                            iframe_screenshot = f"pnn_debug_iframe_{safe_description}_{timestamp}.png"
                            ad_elements[0].screenshot(path=iframe_screenshot)
                            print(f"廣告 iframe 截圖: {os.path.abspath(iframe_screenshot)}")
                            
                        else:
                            print("  ✗ 未找到廣告元素")
                    else:
                        print("  ✗ 無法獲取廣告 iframe 內容")
                except Exception as iframe_error:
                    print(f"  ✗ 廣告 iframe 檢查失敗: {str(iframe_error)}")
            else:
                print("步驟 4: 未找到 tkcatrun iframe，截圖主頁面...")
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                safe_description = description.replace(' ', '_').replace('/', '_')
                main_screenshot = f"pnn_debug_no_iframe_{safe_description}_{timestamp}.png"
                page.screenshot(path=main_screenshot, full_page=False)
                print(f"主頁面截圖: {os.path.abspath(main_screenshot)}")
            
            print("\n結果總結:")
            print(f"  固定 iframe URL: {'✓' if fixed_iframe_found else '✗'}")
            print(f"  tkcatrun 廣告 iframe: {'✓' if tkcatrun_iframe else '✗'}")
            
            print("\n偵錯完成！瀏覽器將保持開啟 10 秒讓您檢查...")
            page.wait_for_timeout(10000)
            
            return True
            
        except Exception as e:
            print(f"偵錯過程中發生錯誤: {str(e)}")
            
            # 截圖錯誤頁面
            try:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                safe_description = description.replace(' ', '_').replace('/', '_')
                error_screenshot = f"pnn_debug_error_{safe_description}_{timestamp}.png"
                page.screenshot(path=error_screenshot, full_page=False)
                print(f"錯誤頁面截圖: {os.path.abspath(error_screenshot)}")
            except:
                print("無法截圖錯誤頁面")
            
            print("瀏覽器將保持開啟 15 秒讓您檢查錯誤...")
            page.wait_for_timeout(15000)
            
            return False
        
        finally:
            print("關閉瀏覽器...")
            browser.close()

def main():
    """主函數"""
    print("PNN 640x200 可視化偵錯工具")
    print("=" * 50)
    print("此工具將開啟瀏覽器讓您觀察 PNN 頁面載入過程")
    print("每個步驟都會有 2 秒間隔，讓您清楚看到發生什麼事")
    print()
    
    # 測試案例
    test_cases = [
        ("3a438fe7-2392-4291-878d-a4d043bb52fd", "原始問題 UUID"),
        ("test-debug-001", "測試用 UUID")
    ]
    
    for uuid, description in test_cases:
        print(f"\n準備測試: {description}")
        print(f"UUID: {uuid}")
        success = visual_debug_pnn(uuid, description)
        
        if not success:
            print(f"測試 {description} 失敗")
            response = input("是否繼續下一個測試？(y/N): ")
            if response.lower() != 'y':
                break
        else:
            print(f"測試 {description} 完成")
    
    print("\n所有偵錯完成！")

if __name__ == "__main__":
    main() 