import os
import time
import random  # 新增 random 模組
from playwright.sync_api import Page, Playwright
import logging
import config # 增加導入 config
import re

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def log_message(message: str):
    """記錄訊息到日誌"""
    logger.info(message)

def slow_down(page: Page, min_delay: float = 0.5, max_delay: float = 1.5):
    """隨機延遲，模擬人類操作"""
    delay = min_delay + (max_delay - min_delay) * random.random()  # 使用 random.random() 替代 time.random()
    time.sleep(delay)

def extract_last_36_chars_from_url(page: Page) -> str:
    """從當前頁面 URL 中提取最後 36 個字符"""
    current_url = page.url
    return current_url[-36:]

def run(playwright: Playwright, ad_data: dict) -> bool:
    """
    執行廣告創建流程，支援 GIF 廣告和水平滑動廣告
    
    Args:
        playwright: Playwright 實例
        ad_data: 包含廣告數據的字典
    
    Returns:
        bool: 操作是否成功
    """
    try:
        browser = playwright.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        
        # 登入流程
        log_message("Navigating to login page")
        page.goto("https://account.aotter.net/login?r=https%3A%2F%2Ftrek.aotter.net%2Fme")
        slow_down(page)

        log_message("Filling login form")
        page.get_by_placeholder("Email 帳號").click()
        page.get_by_placeholder("Email 帳號").fill(config.EMAIL)
        page.get_by_placeholder("Email 帳號").press("Tab")
        page.get_by_placeholder("密碼").fill(config.PASSWORD)
        page.get_by_placeholder("密碼").press("Enter")
        slow_down(page)
        
        # 導航到 Suprad 建立頁面
        page.get_by_role("button", name="ian.chen").click()
        slow_down(page)
        page.get_by_role("link", name="電豹股份有限公司").click()
        slow_down(page)
        page.goto(f"https://trek.aotter.net/advertiser/show/adset?setId={ad_data['adset_id']}")

        page.get_by_role("link", name="+  建立互動廣告單元").click()

        page.wait_for_load_state("domcontentloaded")
        page.wait_for_load_state("networkidle")
        
        # 廣告單元-廣告商
        log_message("Filling ad unit information")
        page.locator("input[name=\"advertiserName\"]").fill(ad_data['advertiser'])
        slow_down(page)
        page.locator("input[name=\"title\"]").click()
        
        # 廣告單元-主標題
        page.locator("input[name=\"title\"]").fill(ad_data['main_title'])
        slow_down(page)
        page.get_by_placeholder("Mobile loading page for Ad").click()
        
        # 選擇 1200x628 圖片
        log_message("Selecting 1200x628 image button")
        absolute_image_path_1 = ad_data['image_path_m']
        log_message(f"Setting input file for first image: {absolute_image_path_1}")
        
        if not os.path.exists(absolute_image_path_1):
            log_message(f"警告：圖片文件不存在: {absolute_image_path_1}")
            return False
        
        page.set_input_files('input[type="file"]', absolute_image_path_1)
        slow_down(page)
        page.wait_for_timeout(2000)
        
        # 等待上傳按鈕出現並點擊
        log_message("等待圖片上傳完成...")
        try:
            page.get_by_text("上傳選取的區域").wait_for(state="visible", timeout=60000)
            page.wait_for_timeout(1500)
            page.get_by_text("上傳選取的區域").click()
            log_message("成功點擊上傳按鈕")
        except Exception as e:
            log_message(f"警告：上傳按鈕點擊失敗: {str(e)}")
            try:
                page.get_by_role("button", name="上傳選取的區域").click()
                log_message("使用替代方式點擊上傳按鈕")
            except Exception as e2:
                log_message(f"警告：無法點擊上傳按鈕: {str(e2)}")
                return False
        
        page.wait_for_timeout(3000)
        page.wait_for_load_state('networkidle', timeout=60000)
        slow_down(page)

        # 選擇 300x300 圖片
        log_message("Selecting 300x300 image button")
        absolute_image_path_2 = ad_data['image_path_s']
        log_message(f"Setting input file for second image: {absolute_image_path_2}")
        
        if not os.path.exists(absolute_image_path_2):
            log_message(f"警告：300x300圖片文件不存在: {absolute_image_path_2}")
            return False
            
        page.locator('input[type="file"]').nth(1).set_input_files(absolute_image_path_2)
        slow_down(page)
        page.wait_for_timeout(2000)
        
        # 等待上傳按鈕出現並點擊
        log_message("等待 300x300 圖片上傳完成...")
        try:
            page.get_by_text("上傳選取的區域").wait_for(state="visible", timeout=60000)
            page.wait_for_timeout(1500)
            page.get_by_text("上傳選取的區域").click()
            log_message("成功點擊 300x300 上傳按鈕")
        except Exception as e:
            log_message(f"警告：300x300 上傳按鈕點擊失敗: {str(e)}")
            try:
                page.get_by_role("button", name="上傳選取的區域").click()
                log_message("使用替代方式點擊 300x300 上傳按鈕")
            except Exception as e2:
                log_message(f"警告：無法點擊 300x300 上傳按鈕: {str(e2)}")
                return False
        
        page.wait_for_timeout(3000)
        page.wait_for_load_state('networkidle', timeout=60000)
        slow_down(page)

        # 網址
        page.get_by_placeholder("Mobile loading page for Ad").fill(ad_data['landing_page'])
        slow_down(page)
        
        # 文字敘述
        log_message("填入文字敘述...")
        text_input = page.locator('input[name="text"]')
        text_input.click()
        text_input.fill(ad_data['subtitle'])
        log_message("已填入文字敘述")
        slow_down(page)
        
        page.get_by_placeholder("bg_placeholder: background").click()
        
        # call to action
        log_message("設定 Call to Action...")
        cta_input = page.locator('input[name="callToAction"]')
        cta_input.click()
        cta_input.fill(ad_data['call_to_action'])
        log_message(f"已填入「{ad_data['call_to_action']}」")
        slow_down(page)
        
        # 遊戲套件預設背景
        page.get_by_placeholder("bg_placeholder: background").fill(ad_data['background_image'])
        slow_down(page)
        page.once("dialog", lambda dialog: dialog.dismiss())
        page.get_by_placeholder("urlInteractivePopup: url to").click()
        
        # 多目標popup網址
        urlInteractivePopups = "https://tkcatrun.aotter.net/popup/"
        page.get_by_placeholder("urlInteractivePopup: url to").fill(urlInteractivePopups)
        slow_down(page)
        page.locator("textarea[name=\"payload_gameWidgetJson\"]").click()
        page.locator("textarea[name=\"payload_gameWidgetJson\"]").press("ControlOrMeta+a")
        
        # payload_gameWidget
        page.locator("textarea[name=\"payload_gameWidgetJson\"]").fill(ad_data['payload_game_widget'])
        slow_down(page)
        page.wait_for_timeout(2000)

        page.get_by_role("button", name="新增").click()
        slow_down(page)
        page.get_by_role("button", name="OK").wait_for(state="visible")
        page.wait_for_timeout(2000)
        page.get_by_role("button", name="OK").click()
        slow_down(page)

        page.wait_for_timeout(2000)
        page.get_by_role("link", name="  互動廣告編輯").wait_for(state="visible")
        page.get_by_role("link", name="  互動廣告編輯").click()
        slow_down(page)

        page.wait_for_load_state('networkidle')
        slow_down(page)
            
        last_36_chars = extract_last_36_chars_from_url(page)

        # 獲取並更新 popup URL
        target_placeholder = page.get_by_placeholder("urlInteractivePopup: url to")
        current_value = target_placeholder.input_value()
        new_value = current_value + last_36_chars
        target_placeholder.fill(new_value)
        slow_down(page)

        page.get_by_role("button", name="修改").wait_for(state="visible")
        page.get_by_role("button", name="修改").click()
        slow_down(page)

        page.wait_for_load_state('networkidle')
        
        log_message("Successfully created GIF ad")
        return True

    except Exception as e:
        log_message(f"Error creating GIF ad: {str(e)}")
        return False
    finally:
        if 'browser' in locals():
            browser.close() 