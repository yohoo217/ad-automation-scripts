# 完整版，可以正常運作且有防呆 2024/11/27 測試可以正常運作，測試人 Ian

import re
import platform,sys,subprocess,shlex,os
from playwright.sync_api import Playwright, sync_playwright
import logging
import config

        # 設置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def log_message(message):
    logging.info(message)



def run(playwright: Playwright, ad_data: dict) -> bool:
    # target_row = row_number - 1  # 因為索引從0開始 - Removed
    browser = None
    context = None
    try:
        log_message(f"Processing ad: {ad_data.get('display_name', 'N/A')}")
        log_message("啟動 arm64 原生 Chrome 穩定版瀏覽器")
        browser = playwright.chromium.launch(
            executable_path="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",  # 指定 arm64 原生 Chrome 路徑
            headless=False,           # 還是想跑 headless
            args=[
                "--disable-gpu",      # 保險起見先關 GPU
                "--no-sandbox",       # 禁用沙箱模式提高穩定性
                "--disable-dev-shm-usage",  # 避免共享記憶體問題
                "--disable-background-timer-throttling",  # 防止背景定時器被限制
                "--disable-backgrounding-occluded-windows",  # 防止背景視窗被限制
                "--disable-renderer-backgrounding",  # 防止渲染器背景化
                "--disable-features=TranslateUI",  # 禁用翻譯功能
                "--disable-extensions",  # 禁用擴充功能
                "--disable-plugins",    # 禁用插件
                "--disable-web-security",  # 禁用網頁安全限制
            ],
        )
        context = browser.new_context()
        
        
        page = context.new_page()

        page.goto("https://account.aotter.net/login?r=https%3A%2F%2Ftrek.aotter.net%2Fme")

        # 等待頁面完全加載
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_load_state("networkidle")

        page.get_by_placeholder("Email 帳號").click()
        # 動態獲取帳號密碼（優先使用函數）
        email = config.get_email()
        password = config.get_password()
        
        if not email or not password:
            # 如果函數沒有返回值，嘗試使用環境變數
            email = config.EMAIL
            password = config.PASSWORD
            
        if not email or not password:
            raise Exception("無法獲取 Trek 系統帳號密碼，請確保已在 .env 中設定或已登入網頁系統")
        
        page.get_by_placeholder("Email 帳號").fill(email)
        page.get_by_placeholder("Email 帳號").press("Tab")
        page.get_by_placeholder("密碼").fill(password)
        page.get_by_placeholder("密碼").press("Enter")

        # 等待登入完成
        page.wait_for_load_state("networkidle")
        
        page.get_by_role("button", name="ian.chen").click()
        page.get_by_role("link", name="電豹股份有限公司").click()
        # page.goto("https://trek.aotter.net/advertiser/show/adset?setId=00947c1b-f7cd-47c6-a23a-0639e9702cc7")
        page.goto(f"https://trek.aotter.net/advertiser/show/adset?setId={ad_data['adset_id']}")

        page.get_by_role("link", name="+  建立廣告單元").click()

        page.wait_for_load_state("domcontentloaded")
        page.wait_for_load_state("networkidle")

        #             # 廣告單元-顯示名稱
        page.get_by_role("textbox", name="顯示於後台").click()
        page.get_by_role("textbox", name="顯示於後台").fill(ad_data['display_name']) # AD 列 / 顯示名稱

                    # 廣告單元-廣告商
        page.get_by_role("textbox", name="廣告商").click()
        page.get_by_role("textbox", name="廣告商").fill(ad_data['advertiser']) # I 列 / 廣告商

                    # 廣告單元-主標題
        page.get_by_role("textbox", name="主標題").click()
        page.get_by_role("textbox", name="主標題").fill(ad_data['main_title']) # J 列 / 主標題

                    # 廣告單元-副標題
        page.get_by_role("textbox", name="副標題").click()
        page.get_by_role("textbox", name="副標題").fill(ad_data['subtitle']) # AA 列 / 副標題

        page.get_by_role("textbox", name="網址（請儘可能使用 HTTPS）").fill(ad_data['landing_page']) # Landing Page
        page.get_by_role("textbox", name="網址（請儘可能使用 HTTPS）").click()
        page.get_by_role("textbox", name="自由輸入").fill(ad_data.get('call_to_action', '瞭解詳情')) # call to action, with default

        
        # 檢查有哪些圖片需要上傳
        image_uploads = []
        
        if ad_data.get('image_path_m'):
            image_uploads.append({
                'path': ad_data['image_path_m'],
                'name': '1200x628',
                'selector_text': None,  # 第一個圖片不需要選擇器
                'description': '第一張圖片 (1200x628)'
            })
            
        if ad_data.get('image_path_p'):
            image_uploads.append({
                'path': ad_data['image_path_p'],
                'name': '300x300',
                'selector_text': '* 正方形圖片 (300 × 300)',
                'description': '正方形圖片 (300x300)'
            })
            
        if ad_data.get('image_path_o'):
            image_uploads.append({
                'path': ad_data['image_path_o'],
                'name': '640x100',
                'selector_text': '* 橫幅640x100 (640 × 100)',
                'description': '橫幅圖片 (640x100)'
            })
            
        if ad_data.get('image_path_s'):
            image_uploads.append({
                'path': ad_data['image_path_s'],
                'name': '336x280',
                'selector_text': '* 橫幅336 (336 × 280)',
                'description': '橫幅圖片 (336x280)'
            })

        # 確保至少有一張圖片
        if not image_uploads:
            raise Exception("至少需要提供一張圖片")

        log_message(f"準備上傳 {len(image_uploads)} 張圖片")

        # 新增可插入選項（根據需要上傳的圖片數量）
        for _ in range(len(image_uploads)):
            page.get_by_role("button", name="").first.click()
            page.wait_for_timeout(300)  # 等待300毫秒，避免點擊太快

        # 動態處理圖片上傳
        for i, upload_info in enumerate(image_uploads):
            log_message(f"設置{upload_info['description']}: {upload_info['path']}")
            
            # 第一張圖片不需要選擇類型（預設已經選好）
            if i > 0 and upload_info['selector_text']:
                page.get_by_placeholder("請選擇").nth(i).click()
                page.wait_for_timeout(500)
                page.get_by_text(upload_info['selector_text']).nth(3).click()
            
            # 上傳圖片檔案
            page.locator('input[type="file"]').nth(i).set_input_files(upload_info['path'])
            page.get_by_role("button", name="儲存").click()
            
            if i < len(image_uploads) - 1:  # 不是最後一張圖片時才等待
                page.wait_for_timeout(500)

        # Fill the tracking URL
        # 預設選 DCM
        if ad_data.get('tracking_url'):
            page.locator("button:has(i.fa-plus)").nth(1).click()  # 點擊第一個按鈕
            page.wait_for_selector("input[placeholder='https://...']")  # 確保元素已加載
            page.locator("input[placeholder='https://...']").nth(0).fill(ad_data['tracking_url'])

        page.get_by_role("button", name="新增廣告單元").click()
        page.get_by_role("button", name="確定").click()

        log_message(f"成功處理廣告: {ad_data.get('display_name', 'N/A')}")
        return True
    except Exception as e:
        log_message(f"處理廣告 {ad_data.get('display_name', 'N/A')} 時發生錯誤: {str(e)}")
        return False
    finally:
        # 確保始終關閉瀏覽器和上下文，即使發生異常
        try:
            if context:
                context.close()
            if browser:
                browser.close()
                log_message("瀏覽器已關閉")
        except Exception as e:
            log_message(f"關閉瀏覽器時發生錯誤: {str(e)}")

