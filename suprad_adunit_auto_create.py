import os
import time
import random  # 新增 random 模組
import json  # 增加 json 模組
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

def slow_down(page: Page, min_delay: float = 0.3, max_delay: float = 0.8):
    """隨機延遲，模擬人類操作
    減少延遲時間以降低超時風險，但仍保持一定的間隔
    """
    delay = min_delay + (max_delay - min_delay) * random.random()
    time.sleep(delay)

def extract_last_36_chars_from_url(page: Page) -> str:
    """從當前頁面 URL 中提取最後 36 個字符"""
    current_url = page.url
    return current_url[-36:]

def run(playwright: Playwright, ad_data: dict, ad_type: str = 'gif') -> bool:
    """
    執行廣告創建流程，支援多種互動廣告類型
    
    Args:
        playwright: Playwright 實例
        ad_data: 包含廣告數據的字典
        ad_type: 廣告類型 (gif, slide, countdown等)
    
    Returns:
        bool: 操作是否成功
    """
    # 強制使用傳入的 ad_type 參數，確保不會被覆蓋
    actual_ad_type = ad_type
    # 將 ad_type 存入 ad_data 中，以便後續使用
    ad_data['ad_type'] = actual_ad_type
        
    log_message(f"開始創建 {actual_ad_type} 類型廣告 - 接收到資料: {str(ad_data)}")
    
    try:
        log_message("啟動 arm64 原生 Chrome 穩定版瀏覽器")
        # 使用 arm64 原生 Chrome 穩定版
        browser = playwright.chromium.launch(
            executable_path="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",  # 指定 arm64 原生 Chrome 路徑
            headless=False,  # 改為非 headless 模式以便觀察
            slow_mo=250,  # 添加 slow_mo 參數，每個操作延遲 250 毫秒
            args=[
                '--disable-dev-shm-usage',  # 禁用 /dev/shm 使用，在某些系統上更穩定
                '--no-sandbox',  # 禁用沙箱模式
                '--disable-setuid-sandbox',  # 禁用 setuid 沙箱
                '--disable-gpu',  # 禁用 GPU 加速
                '--disable-software-rasterizer',  # 禁用軟件光柵化
                '--disable-background-timer-throttling',  # 防止背景定時器被限制
                '--disable-backgrounding-occluded-windows',  # 防止背景視窗被限制
                '--disable-renderer-backgrounding',  # 防止渲染器背景化
                '--disable-features=TranslateUI',  # 禁用翻譯功能
                '--disable-extensions',  # 禁用擴充功能
                '--disable-plugins',    # 禁用插件
            ]
        )
        # 增加超時時間並忽略 HTTPS 錯誤
        context = browser.new_context(
            ignore_https_errors=True,
            viewport={'width': 1280, 'height': 800}
        )
        log_message("瀏覽器上下文創建成功")
        page = context.new_page()
        log_message("新頁面創建成功")
        
        # 登入流程
        log_message("導航到登入頁面")
        try:
            # 增加超時設置，確保頁面完全加載
            page.goto("https://account.aotter.net/login?r=https%3A%2F%2Ftrek.aotter.net%2Fme", 
                      timeout=60000,  # 60秒超時
                      wait_until="networkidle")  # 等待網絡空閒
            log_message("登入頁面加載完成")
        except Exception as nav_error:
            log_message(f"頁面導航錯誤: {str(nav_error)}")
            return False

        # 確保表單元素存在
        try:
            log_message("等待登入表單出現")
            page.wait_for_selector('input[placeholder="Email 帳號"]', state="visible", timeout=20000)
            log_message("登入表單已出現")
        except Exception as wait_error:
            log_message(f"等待表單元素錯誤: {str(wait_error)}")
            return False
            
        # 嘗試填寫表單
        try:
            log_message("填寫登入表單")
            page.get_by_placeholder("Email 帳號").fill(config.EMAIL)
            log_message(f"已填寫郵箱: {config.EMAIL}")
            page.get_by_placeholder("密碼").fill(config.PASSWORD)
            log_message("已填寫密碼")
            
            # 點擊登入按鈕而不是按 Enter 鍵，更穩定
            page.get_by_role("button", name="登入").click()
            log_message("已點擊登入按鈕")
            
            # 等待登入成功
            page.wait_for_load_state("networkidle", timeout=30000)
            log_message("登入流程完成")
        except Exception as login_error:
            log_message(f"登入過程錯誤: {str(login_error)}")
            return False
        
        # 導航到 Suprad 建立頁面
        page.get_by_role("button", name="ian.chen").click()
        slow_down(page)
        page.get_by_role("link", name="電豹股份有限公司").click()
        slow_down(page)
        log_message(f"導航到廣告組頁面，adset_id: {ad_data['adset_id']}")
        page.goto(f"https://trek.aotter.net/advertiser/show/adset?setId={ad_data['adset_id']}")
        log_message("成功到達廣告組頁面")

        log_message("點擊「建立互動廣告單元」按鈕")
        page.get_by_role("link", name="+  建立互動廣告單元").click()
        log_message("已點擊建立按鈕")

        log_message("等待頁面載入")
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_load_state("networkidle")
        log_message("頁面已完全載入")
        
        # 廣告單元-廣告商
        log_message("開始填寫廣告單元資訊")
        log_message(f"填寫廣告商名稱: {ad_data['advertiser']}")
        page.locator("input[name=\"advertiserName\"]").fill(ad_data['advertiser'])
        slow_down(page)
        page.locator("input[name=\"title\"]").click()
        
        # 廣告單元-主標題
        log_message(f"填寫廣告主標題: {ad_data['main_title']}")
        page.locator("input[name=\"title\"]").fill(ad_data['main_title'])
        slow_down(page)
        page.get_by_placeholder("Mobile loading page for Ad").click()
        
        # 選擇 1200x628 圖片
        log_message("準備上傳 1200x628 圖片")
        absolute_image_path_1 = ad_data['image_path_m']
        log_message(f"1200x628 圖片路徑: {absolute_image_path_1}")
        
        if not os.path.exists(absolute_image_path_1):
            log_message(f"錯誤: 1200x628 圖片文件不存在: {absolute_image_path_1}")
            return False
        
        log_message("檢查圖片路徑存在，開始上傳")
        
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
        page.locator("input[name=\"text\"]").fill(ad_data['subtitle'])
        log_message("已填入文字敘述")
        slow_down(page)
        
        # call to action
        log_message("設定 Call to Action...")
        cta_input = page.locator('input[name="callToAction"]')
        cta_input.fill(ad_data['call_to_action'])
        log_message(f"已填入「{ad_data['call_to_action']}」")
        slow_down(page)
        
        # 遊戲套件預設背景
        page.get_by_placeholder("bg_placeholder: background").fill(ad_data['background_url'])
        slow_down(page)
        page.once("dialog", lambda dialog: dialog.dismiss())
        
        # 跳出視窗網址
        LandingPageurl = "https://tkcatrun.aotter.net/popup/"
        page.get_by_placeholder("urlInteractivePopup: url to").fill(LandingPageurl)
        slow_down(page)
        
        # urlInteractivePopups
        log_message("填入 urlInteractivePopups...")
        page.locator("textarea[name=\"urlInteractivePopups\"]").fill('[]')
        slow_down(page)

        # 跳出視窗寬與高，根據廣告類型設定
        if ad_data.get('ad_type') == 'native_video':
            log_message("偵測到 native_video 廣告類型，設定彈窗寬高")
            page.locator("input[name=\"popupWidth\"]").fill("1200")
            slow_down(page)
            page.locator("input[name=\"popupHeight\"]").fill("2050")
            slow_down(page)
        else:
            log_message("非 native_video 廣告類型，不設定彈窗寬高")

        # payload_gameWidget
        page.locator("textarea[name=\"payload_gameWidgetJson\"]").fill(ad_data['payload_game_widget'])

        # payload_popupJson
        log_message("填入 payload_popupJson...")
        page.locator("textarea[name=\"payload_popupJson\"]").fill(ad_data.get('payload_popupJson') or '[]')


        slow_down(page)
        page.wait_for_timeout(2000)

        log_message("點擊「新增」按鈕")
        page.get_by_text("新增").click()
        log_message("已點擊「新增」按鈕")
        slow_down(page)
        
        log_message("等待確認對話框出現")
        page.get_by_role("button", name="OK").wait_for(state="visible")
        page.wait_for_timeout(2000)
        log_message("點擊「OK」按鈕確認")
        page.get_by_role("button", name="OK").click()
        log_message("已點擊「OK」按鈕")
        slow_down(page)

        log_message("等待互動廣告編輯連結出現")
        page.wait_for_timeout(2000)
        page.get_by_role("link", name="  互動廣告編輯").wait_for(state="visible", timeout=60000)
        log_message("點擊「互動廣告編輯」連結")
        page.get_by_role("link", name="  互動廣告編輯").click()
        log_message("已點擊「互動廣告編輯」連結")
        slow_down(page)

        log_message("等待頁面載入完成")
        page.wait_for_load_state('networkidle')
        slow_down(page)
            
        log_message("從 URL 提取 ID")
        last_36_chars = extract_last_36_chars_from_url(page)
        log_message(f"提取到的 ID: {last_36_chars}")

        # 獲取並更新 popup URL
        log_message("更新 popup URL")
        target_placeholder = page.get_by_placeholder("urlInteractivePopup: url to")
        current_value = target_placeholder.input_value()
        new_value = current_value + last_36_chars
        log_message(f"更新後的 URL: {new_value}")
        target_placeholder.fill(new_value)
        log_message("已填入更新後的 URL")
        slow_down(page)

        # 更新 urlInteractivePopups
        log_message("更新 urlInteractivePopups")
        try:
            # 這些廣告類型不需要填入 urlInteractivePopups，因為它們的互動邏輯在 payload_game_widget 中
            skip_popup_ad_types = ['slide', 'vertical_slide', 'vertical_cube_slide', 'vote', 'countdown']
            if ad_data.get('ad_type') in skip_popup_ad_types:
                log_message(f"偵測到 {ad_data.get('ad_type')} 廣告類型，不需要更新 urlInteractivePopups")
            else:
                url_interactive_popups_textarea = page.locator("textarea[name=\"urlInteractivePopups\"]")
                
                # 根據廣告類型決定 urlInteractivePopups 的格式
                if ad_data.get('ad_type') == 'treasure_box':
                    log_message("偵測到 treasure_box 廣告類型，使用特殊的 urlInteractivePopups 格式")
                    # 寶箱廣告使用 a、b、c 三個 key，每個都有對應的 query parameter
                    popups_list = [
                        {
                            "key": "a",
                            "url": new_value + "?key=a"
                        },
                        {
                            "key": "b",
                            "url": new_value + "?key=b"
                        },
                        {
                            "key": "c",
                            "url": new_value + "?key=c"
                        }
                    ]
                else:
                    # 其他廣告類型使用原本的格式
                    log_message("使用標準的 urlInteractivePopups 格式")
                    popups_list = [
                        {
                            "key": "a",
                            "url": new_value
                        },
                        {
                            "key": "a", 
                            "url": new_value
                        }
                    ]
                
                updated_popups_json = json.dumps(popups_list, indent=2)
                log_message(f"更新後的 urlInteractivePopups: {updated_popups_json}")
                
                url_interactive_popups_textarea.fill(updated_popups_json)
                log_message("已填入更新後的 urlInteractivePopups")
                slow_down(page)
            
        except Exception as e:
            log_message(f"更新 urlInteractivePopups 時發生錯誤: {str(e)}")
            # 根據需求看是否要返回 False 或繼續

        log_message("等待「修改」按鈕出現")
        page.get_by_role("button", name="修改").wait_for(state="visible", timeout=60000)
        log_message("點擊「修改」按鈕")
        page.get_by_role("button", name="修改").click()
        log_message("已點擊「修改」按鈕")
        slow_down(page)

        log_message("等待頁面載入完成")
        page.wait_for_load_state('networkidle')
        
        # 使用函數參數中指定的廣告類型，這才是準確的
        log_message(f"成功創建 {ad_type} 廣告，顯示名稱: {ad_data.get('display_name', '無名稱')}")
        return True

    except Exception as e:
        log_message(f"創建 {ad_type} 廣告時發生錯誤: {str(e)}")
        # 記錄堆疊跟踪以獲取更多信息
        import traceback
        log_message(f"錯誤詳情：\n{traceback.format_exc()}")
        return False
    finally:
        log_message("執行結束，準備關閉資源")
        try:
            # 先關閉頁面
            if 'page' in locals() and page:
                try:
                    log_message("關閉頁面")
                    page.close(run_before_unload=False)
                    log_message("頁面關閉成功")
                except Exception as page_close_error:
                    log_message(f"關閉頁面時出錯 (忽略): {str(page_close_error)}")
            
            # 再關閉上下文
            if 'context' in locals() and context:
                try:
                    log_message("關閉瀏覽器上下文")
                    context.close()
                    log_message("瀏覽器上下文關閉成功")
                except Exception as context_close_error:
                    log_message(f"關閉上下文時出錯 (忽略): {str(context_close_error)}")
            
            # 最後關閉瀏覽器
            if 'browser' in locals() and browser:
                try:
                    log_message("關閉瀏覽器")
                    browser.close()
                    log_message("瀏覽器關閉成功")
                except Exception as browser_close_error:
                    log_message(f"關閉瀏覽器時出錯 (忽略): {str(browser_close_error)}")
            
            log_message("所有資源已關閉")
        except Exception as final_error:
            log_message(f"最終資源清理過程中發生錯誤 (忽略): {str(final_error)}") 