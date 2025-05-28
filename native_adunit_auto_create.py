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
        page.get_by_placeholder("Email 帳號").fill(config.EMAIL)
        page.get_by_placeholder("Email 帳號").press("Tab")
        page.get_by_placeholder("密碼").fill(config.PASSWORD)
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

        
    # 新增可插入選項
        for _ in range(4):
            page.get_by_role("button", name="").first.click()
            page.wait_for_timeout(300)  # 等待300毫秒，避免點擊太快

   # 插入圖片 - 第一次
        # 在點擊之前添加等待
        # 使用 JavaScript 找到並點擊包含特定文字的選項，不知道為什麼這會改到第一個圖片，所以第一個圖片會變成 336x280

        log_message(f"設置第一張圖片: {ad_data['image_path_m']}")
        page.locator('input[type="file"]').nth(0).set_input_files(ad_data['image_path_m'])
        page.get_by_role("button", name="儲存").click()

    # 插入圖片 - 第二次，因為 input 位置名稱都重複，位置順序又會因為新增插入選項而變動，所以順序現在看起來怪怪的，但可以 work
        log_message("插入第二張圖片 - 300x300")
        page.get_by_placeholder("請選擇").nth(1).click()
        page.wait_for_timeout(500)
        page.get_by_text("* 正方形圖片 (300 × 300)").nth(3).click()

        log_message(f"設置第二張圖片: {ad_data['image_path_p']}")
        page.locator('input[type="file"]').nth(1).set_input_files(ad_data['image_path_p'])
        page.get_by_role("button", name="儲存").click()
        page.wait_for_timeout(500)

    # 插入圖片 - 第三次
        log_message("插入第三張圖片 - 640x100")
        page.get_by_placeholder("請選擇").nth(2).click()
        page.get_by_text("* 橫幅640x100 (640 × 100)").nth(3).click()

        log_message(f"設置第三張圖片: {ad_data['image_path_o']}")
        page.locator('input[type="file"]').nth(2).set_input_files(ad_data['image_path_o'])
        page.get_by_role("button", name="儲存").click()

        # 插入圖片 - 第四次
        log_message("插入第四張圖片 - 336x280")
        page.get_by_placeholder("請選擇").nth(3).click()
        page.get_by_text("* 橫幅336 (336 × 280)").nth(3).click()

        log_message(f"設置第四張圖片: {ad_data['image_path_s']}")
        page.locator('input[type="file"]').nth(3).set_input_files(ad_data['image_path_s'])
        page.get_by_role("button", name="儲存").click()

        # Fill the tracking URL
        # 預設選 DCM
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

