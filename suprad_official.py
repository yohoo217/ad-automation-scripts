# 完整版，可以正常運作且有防呆 2025/03/10 測試可以正常運作，測試人 Ian

import re
import time
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from playwright.sync_api import Playwright, sync_playwright, expect
import logging
import config
from playwright.sync_api import Page
from playwright.sync_api import expect
import os

# ======== 腳本設定選項 ========
# 設置為 True 將不顯示瀏覽器界面，設置為 False 將顯示瀏覽器界面
HEADLESS_MODE = True

# 設置為 True 將放慢操作速度，便於觀察和調試
SLOW_MODE = False 

# 設置為 True 時，即使沒有 Google Sheet 寫入權限也繼續執行
IGNORE_SHEET_PERMISSION_ERROR = False

# 慢速模式下的操作延遲時間 (毫秒)
SLOW_MODE_DELAY = 1000
# ============================

# 設置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 慢速模式延遲函數
def slow_down(page):
    """當啟用慢速模式時，增加延遲以方便觀察"""
    if SLOW_MODE:
        page.wait_for_timeout(SLOW_MODE_DELAY)

# Google Sheet 的 URL 和範圍
sheet_url = 'https://docs.google.com/spreadsheets/d/1m4ZDj46ZdZMjXS30GA2nzn36s2CEqETrCp_rh4dTmbM/edit?gid=408679682#gid=408679682'
range_name = 'A1:AM100'
row_number = 2  # 定義要讀取的起始行號
worksheet_index = 5  # 選擇工作表
worksheet_names = {
    0: "目錄",
    1: "1-MoPTT",
    2: "2-moptt-web", 
    3: "3-JPTT",
    4: "4-PiTT",
    5: "5-nPTT",
    6: "6-ptt now",
    7: "7-busplus",
    8: "8-meow ptt",
    9: "9-icook",
    10: "10-taipeifoodblogs-web",
    11: "11-taipeifoodblogs",
    12: "17-feebee",
    13: "18-disp",
    14: "19-knocktalk-web",
    15: "20-tvbshealth-Web",
    16: "21-tvbsnews-Web",
    17: "22-tvbssupertaste-Web",
    18: "23-pchomestock-Web",
    19: "12-taiwan17go-web",
    20: "13-kocpc",
    21: "14-PNN_",
    22: "15-agirls-web",
    23: "16-巨思-web",
    24: "範本",
    25: "素材庫"
}

# Google Sheets 設置
def get_sheet_data(sheet_url, range_name, worksheet_index):
    """連接到Google Sheets並獲取數據"""
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name('booming-alchemy-384405-53ca11c6903d.json', scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_url(sheet_url)
    worksheet = sheet.get_worksheet(worksheet_index)  # 選擇工作表
    
    # 取得並顯示工作表名稱
    worksheet_name = worksheet.title
    worksheet_desc = worksheet_names.get(worksheet_index, "未知工作表")
    log_message(f"已選擇工作表: 第{worksheet_index}個 - {worksheet_name} ")
    
    data = worksheet.get(range_name)
    return worksheet, data

def wait_for_page_transition(page, expected_url_pattern, timeout=60000):
    start_time = time.time()
    while time.time() - start_time < timeout / 1000:  # Convert timeout to seconds
        if re.search(expected_url_pattern, page.url):
            return True
        page.wait_for_timeout(1000)  # Wait for 1 second before checking again
    return False

def extract_last_36_chars_from_url(page):
    # 獲取當前頁面的 URL
    current_url = page.url
    # 提取 URL的最後 36 位字符
    last_36_chars = current_url[-36:]
    return last_36_chars

def log_message(message):
    logging.info(message)

# 防呆
def check_h_column(sheet_data, row_number):
    target_row = row_number - 1  # 因為索引從0開始
    # 確認是否為 6 size = suprad
    return sheet_data[target_row][7].strip().lower() == 'suprad'  # 7 ad type

def check_ad_type(sheet_data, row_number):
    target_row = row_number - 1  # 因為索引從0開始
    # 根據 Google Sheet 標題，索引 7 對應欄位 "7 ad type"
    # 由於索引從 0 開始，所以實際欄位索引是 7
    ad_type = sheet_data[target_row][7].strip().lower() if len(sheet_data[target_row]) > 7 else ""
    log_message(f"檢查廣告類型: {ad_type}")
    return ad_type

def check_a_column(worksheet, row_number):
    """檢查A列是否已經標記為完成"""
    cell_value = worksheet.acell(f'A{row_number}').value
    return cell_value == 'v'

def update_sheet_status(worksheet, row_number, status):
    cell = f'A{row_number}'
    value = 'v' if status else 'x'
    try:
        # 更新方法的參數順序已變更，按新的格式傳遞參數
        worksheet.update(values=[[value]], range_name=cell, value_input_option='USER_ENTERED')
        if status:
            try:
                worksheet.format(cell, {"backgroundColor": {"red": 1, "green": 0, "blue": 0}})
            except Exception as format_error:
                log_message(f"無法設定儲存格格式，但值已更新: {str(format_error)}")
        log_message(f"Updated row {row_number} status to {'success' if status else 'failure'}")
    except gspread.exceptions.APIError as e:
        log_message(f"Error updating cell {cell}: {str(e)}")
        log_message("請確保服務帳戶 booming-alchemy-384405-53ca11c6903d.json 有權限編輯試算表")
        log_message("解決方法: 在 Google Sheet 中點擊「共用」按鈕，然後將服務帳戶電子郵件添加為編輯者")
        # 嘗試替代方法
        try:
            worksheet.update_cell(row_number, 1, value)
            log_message(f"Successfully updated cell {cell} using alternative method")
        except Exception as e2:
            log_message(f"Failed to update cell {cell} using alternative method: {str(e2)}")
            log_message("程序將繼續執行，但不會標記已完成的行")

    # 避免按不到建立互動廣告單元的邏輯
def try_click_create_interactive_ad(page, max_attempts=3):
    for attempt in range(max_attempts):
        try:
            log_message(f"Attempt {attempt + 1} to click '建立互動廣告單元'")
            page.get_by_role("link", name="建立互動廣告單元").click(timeout=5000)
            log_message("Successfully clicked '建立互動廣告單元'")
            return True
        except Exception as e:
            log_message(f"Failed to click '建立互動廣告單元': {str(e)}")
            
            if attempt == 0:
                # 第一次失敗，縮放到 80%
                log_message("Zooming browser to 80%")
                page.evaluate("document.body.style.zoom = '80%'")
            elif attempt == 1:
                # 第二次失敗，重新加載頁面並縮放到 80%
                log_message("Reloading page and zooming to 80%")
                page.reload()
                page.wait_for_load_state('networkidle')
                page.evaluate("document.body.style.zoom = '80%'")
            
            # 等待一下，讓頁面有時間響應
            page.wait_for_timeout(2000)
    
    log_message("Failed to click '+ 建立互動廣告單元' after all attempts")
    return False


def run_automation(playwright: Playwright, row_number: int, sheet_data: list) -> bool:
    # 設置行號
    target_row = row_number - 1  # 因為索引從0開始

    log_message(f"Processing row {row_number}")
    browser = playwright.chromium.launch(headless=HEADLESS_MODE)
    context = browser.new_context()
    
    # 設置慢速模式
    if SLOW_MODE:
        context.set_default_timeout(120000)  # 增加超時時間，避免慢速模式下操作超時
    
    page = context.new_page()

    try:
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

        page.get_by_role("button", name="ian.chen").click()
        slow_down(page)
        page.get_by_role("link", name="電豹股份有限公司").click()
        slow_down(page)
        page.goto("https://trek.aotter.net/advertiser/show/campaign?campId=d0b61923-7c69-4c8c-a67a-8014d40e1694")
        slow_down(page)

        page.get_by_role("link", name="+  建立廣告").click()
        slow_down(page)
        page.locator(".el-input__inner").first.click()
        
        # 廣告-廣告名稱
        log_message("Filling ad form")
        page.locator(".el-input__inner").first.fill(sheet_data[target_row][1])  # 1 adsetName
        slow_down(page)
        page.get_by_placeholder("開始時間").click()
        page.get_by_placeholder("開始時間").fill("2025-03-12 01:00")
        slow_down(page)
        page.get_by_placeholder("結束時間").click()
        page.get_by_placeholder("結束時間").fill("2025-03-18 16:00")
        slow_down(page)
        page.locator("div").filter(has_text=re.compile(r"^\* 廣告類型 圖片廣告影音廣告原生互動廣告$")).get_by_placeholder("請選擇").click()
        page.get_by_text("原生互動廣告").click()
        slow_down(page)
        
        # 從 Google Sheet 中獲取對應行的值
        platform_text_1 = sheet_data[target_row][3]  # 3 裝置類型
        platform_text_2 = sheet_data[target_row][4]  # 4 裝置類型（可能為空）

        # 把選擇的平台都先去消掉
        log_message("Selecting platforms")
        page.locator("label").filter(has_text="iOS App").locator("span").nth(1).click()
        page.locator("label").filter(has_text="Android App").locator("span").nth(1).click()
        page.locator("label").filter(has_text="Mobile Web - iOS").locator("span").nth(1).click()
        page.locator("label").filter(has_text="Mobile Web - Android").locator("span").nth(1).click()
        slow_down(page)
            
        # 平台選擇 - 第一個平台
        page.locator("label").filter(has_text=platform_text_1).locator("span").nth(1).click()
        
        # 如果有第二個平台，也選擇它
        if platform_text_2 and platform_text_2.strip():
            log_message(f"Selecting second platform: {platform_text_2}")
            page.locator("label").filter(has_text=platform_text_2).locator("span").nth(1).click()
        slow_down(page)
            
        page.locator("div:nth-child(5) > .col-md-10 > .el-select > .el-select__tags > .el-select__input").click()

        # 渠道
        log_message("Filling channel information")
        page.locator("div:nth-child(5) > .col-md-10 > .el-select > .el-select__tags > .el-select__input").fill(sheet_data[target_row][19])  # 19 ClinetId
        slow_down(page)
        page.get_by_text(sheet_data[target_row][20]).nth(1).click()  # 20 包含應用程式名稱
        slow_down(page)
        page.locator("div:nth-child(12) > .form-group > div > div > .col-md-10 > .el-select > .el-select__tags > .el-select__input").click()
                
        # place
        log_message("Selecting place")
        page.locator("div:nth-child(12) > .form-group > div > div > .col-md-10 > .el-select > .el-select__tags > .el-select__input").fill(sheet_data[target_row][21]) # 21 UUID
        slow_down(page)
        page.locator("ul").filter(has_text=re.compile(rf"^{sheet_data[target_row][21]}$")).get_by_role("listitem").click() # 21 UUID
        slow_down(page)
        page.get_by_role("spinbutton").nth(1).click()
        
        page.locator("div").filter(has_text=re.compile(r"^投遞類型 平均投放加強投放$")).get_by_placeholder("請選擇").click()
        page.locator("li").filter(has_text="加強投放").click()
        slow_down(page)

        # 預算
        log_message("Filling budget and bidding information")
        page.get_by_role("spinbutton").nth(1).fill("4") # 正式 mode
        page.get_by_role("spinbutton").nth(2).click()
        slow_down(page)
        
        # 預算類型
        page.locator("div").filter(has_text=re.compile(r"^預算類型 CPCCPMCPV$")).get_by_placeholder("請選擇").click()
        page.locator("li").filter(has_text="CPM").click()
        slow_down(page)

        # 出價
        page.get_by_role("spinbutton").nth(2).fill("0.1") # 正式 mode
        slow_down(page)
        page.get_by_role("button", name="建立廣告").click()
        slow_down(page)
        page.get_by_role("button", name="確定").click()

        # 等待頁面加載完成
        log_message("Waiting for page to load")
        page.wait_for_load_state('networkidle')
        slow_down(page)

        page.evaluate("""
            const buttons = document.querySelectorAll('a.btn.btn-success.m-b-30.waves-light');
            if (buttons.length > 1) {
                buttons[1].click();
            } else {
                console.error('Second button not found');
            }
        """)
        slow_down(page)        

        # 確保頁面已穩定後再進行縮放操作
        log_message("等待頁面穩定後進行縮放...")
        page.wait_for_load_state('networkidle', timeout=30000)
        page.wait_for_timeout(2000)  # 額外等待 2 秒確保頁面完全穩定
        
        try:
            # 將頁面縮放到 80% 再嘗試點擊
            page.evaluate("document.body.style.zoom = '80%'")
            log_message("成功將頁面縮放到 80%")
        except Exception as e:
            log_message(f"縮放頁面時發生錯誤: {str(e)}")
            # 重新嘗試縮放操作
            page.wait_for_timeout(3000)  # 再多等待一些時間
            try:
                page.evaluate("document.body.style.zoom = '80%'")
                log_message("第二次嘗試縮放頁面成功")
            except Exception as e2:
                log_message(f"第二次嘗試縮放頁面失敗: {str(e2)}")
                # 繼續執行，希望頁面可以正常操作
        
        # 在點擊之前再等待一下，確保縮放已經應用
        page.wait_for_timeout(1000)
        
        try:
            page.locator("input[name=\"advertiserName\"]").click()
            log_message("成功點擊 advertiserName 輸入框")
        except Exception as e:
            log_message(f"點擊 advertiserName 輸入框失敗: {str(e)}")
            # 嘗試使用 JavaScript 直接點擊
            try:
                page.evaluate("""
                    document.querySelector("input[name='advertiserName']").focus();
                """)
                log_message("使用 JavaScript 成功聚焦 advertiserName 輸入框")
            except Exception as e2:
                log_message(f"使用 JavaScript 聚焦 advertiserName 輸入框失敗: {str(e2)}")
                # 最後嘗試重新載入頁面並再試一次
                page.reload()
                page.wait_for_load_state('networkidle')
                page.wait_for_timeout(3000)
                page.evaluate("document.body.style.zoom = '80%'")
                page.wait_for_timeout(1000)
                page.locator("input[name=\"advertiserName\"]").click()
                log_message("頁面重載後成功點擊 advertiserName 輸入框")

        # 廣告單元-廣告商
        log_message("Filling ad unit information")
        page.locator("input[name=\"advertiserName\"]").fill(sheet_data[target_row][9])  # 9 廣告商
        slow_down(page)
        page.locator("input[name=\"title\"]").click()
        
        # 廣告單元-主標題
        page.locator("input[name=\"title\"]").fill(sheet_data[target_row][10])  # 10 主標題
        slow_down(page)
        page.get_by_placeholder("Mobile loading page for Ad").click()
        
        # 選擇 1200x628 圖片
        log_message("Selecting 1200x628 image button")

        # 使用絕對路徑來上傳圖片
        absolute_image_path_1 = sheet_data[target_row][15]  # 15 1200x628
        log_message(f"Setting input file for first image: {absolute_image_path_1}")
        
        # 確保文件存在
        if not os.path.exists(absolute_image_path_1):
            log_message(f"警告：圖片文件不存在: {absolute_image_path_1}")
            # 繼續執行，但記錄警告
        
        # 設置文件上傳
        page.set_input_files('input[type="file"]', absolute_image_path_1)
        slow_down(page)
        page.wait_for_timeout(2000)  # 確保文件上傳完成
        
        # 等待上傳按鈕出現
        log_message("等待圖片上傳完成...")
        try:
            page.get_by_text("上傳選取的區域").wait_for(state="visible", timeout=60000)
            # 等待按鈕可用
            page.wait_for_timeout(1500)  # 給予更長的等待時間
            page.get_by_text("上傳選取的區域").click()
            log_message("成功點擊上傳按鈕")
        except Exception as e:
            log_message(f"警告：上傳按鈕點擊失敗: {str(e)}")
            # 嘗試另一種方式
            try:
                page.get_by_role("button", name="上傳選取的區域").click()
                log_message("使用替代方式點擊上傳按鈕")
            except Exception as e2:
                log_message(f"警告：無法點擊上傳按鈕: {str(e2)}")
                # 繼續執行，但已記錄警告
        
        # 等待網絡活動完成
        log_message("等待圖片處理完成...")
        page.wait_for_timeout(3000)  # 先等待一固定時間
        page.wait_for_load_state('networkidle', timeout=60000)
        slow_down(page)

        # 選擇 300x300 圖片
        log_message("Selecting 300x300 image button")

        # 使用絕對路徑來上傳圖片
        absolute_image_path_2 = sheet_data[target_row][16]
        log_message(f"Setting input file for second image: {absolute_image_path_2}")
        
        # 確保文件存在
        if not os.path.exists(absolute_image_path_2):
            log_message(f"警告：300x300圖片文件不存在: {absolute_image_path_2}")
            # 繼續執行，但記錄警告
            
        # 設置文件上傳
        page.locator('input[type="file"]').nth(1).set_input_files(absolute_image_path_2)
        slow_down(page)
        page.wait_for_timeout(2000)  # 確保文件上傳完成
        
        # 等待上傳按鈕出現
        log_message("等待 300x300 圖片上傳完成...")
        try:
            page.get_by_text("上傳選取的區域").wait_for(state="visible", timeout=60000)
            # 等待按鈕可用
            page.wait_for_timeout(1500)  # 給予更長的等待時間
            page.get_by_text("上傳選取的區域").click()
            log_message("成功點擊 300x300 上傳按鈕")
        except Exception as e:
            log_message(f"警告：300x300 上傳按鈕點擊失敗: {str(e)}")
            # 嘗試另一種方式
            try:
                page.get_by_role("button", name="上傳選取的區域").click()
                log_message("使用替代方式點擊 300x300 上傳按鈕")
            except Exception as e2:
                log_message(f"警告：無法點擊 300x300 上傳按鈕: {str(e2)}")
                # 繼續執行，但已記錄警告
        
        # 等待網絡活動完成
        log_message("等待 300x300 圖片處理完成...")
        page.wait_for_timeout(3000)  # 先等待一固定時間
        page.wait_for_load_state('networkidle', timeout=60000)
        slow_down(page)

        # 網址
        page.get_by_placeholder("Mobile loading page for Ad").fill(sheet_data[target_row][27])  # 27 Landing page
        slow_down(page)
        
        # 文字敘述 - 使用已確認成功的方法（name 屬性）
        log_message("填入文字敘述...")
        text_input = page.locator('input[name="text"]')
        text_input.click()
        text_input.fill(sheet_data[target_row][11])  # 11 副標題
        log_message("已填入文字敘述")
        slow_down(page)
        
        page.get_by_placeholder("bg_placeholder: background").click()
        
        # call to action - 使用已確認成功的方法（直接輸入）
        log_message("設定 Call to Action...")
        cta_input = page.locator('input[name="callToAction"]')
        cta_input.click()
        cta_input.fill("立即購買")
        log_message("已填入「立即購買」")
        slow_down(page)
        
        # 遊戲套件預設背景
        page.get_by_placeholder("bg_placeholder: background").fill(sheet_data[target_row][12])  # 12 圖一
        slow_down(page)
        page.once("dialog", lambda dialog: dialog.dismiss())
        page.get_by_placeholder("urlInteractivePopup: url to").click()
        
        # 多目標popup網址 - 固定使用特定網址
        urlInteractivePopups = "https://tkcatrun.aotter.net/popup/"  # 使用固定的 popup 網址
        page.get_by_placeholder("urlInteractivePopup: url to").fill(urlInteractivePopups)
        slow_down(page)
        page.locator("textarea[name=\"payload_gameWidgetJson\"]").click()
        page.locator("textarea[name=\"payload_gameWidgetJson\"]").press("ControlOrMeta+a")
        
        # payload_gameWidget
        payload_gameWidget = sheet_data[target_row][29]  # 29 payload_gameWidget (to CatWalk)
        page.locator("textarea[name=\"payload_gameWidgetJson\"]").fill(payload_gameWidget)
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

        # 獲取另一个 placeholder 的當前值
        target_placeholder = page.get_by_placeholder("urlInteractivePopup: url to")
        current_value = target_placeholder.input_value()

        # 將最後 36 位字符添加到當前值的末尾
        new_value = current_value + last_36_chars

        # 填充新的值
        target_placeholder.fill(new_value)
        slow_down(page)

        page.get_by_role("button", name="修改").wait_for(state="visible")
        page.get_by_role("button", name="修改").click()
        slow_down(page)

        # Wait for any final page transitions or loading states
        page.wait_for_load_state('networkidle')

        log_message(f"Successfully processed row {row_number}")
        return True

    except Exception as e:
        logging.error(f"Error processing row {row_number}: {str(e)}")
        page.screenshot(path=f"error_screenshot_row_{row_number}.png")
        return False

    finally:
        context.close()
        browser.close()

def main():
    try:
        # 獲取 Google Sheet 數據
        worksheet, sheet_data = get_sheet_data(sheet_url, range_name, worksheet_index)
        
        # 獲取最後一行的行號
        last_row = len(sheet_data)
        
        # 從指定的 row_number 開始循環
        current_row = row_number
        while current_row <= last_row:
            log_message(f"正在檢查第 {current_row} 行")
            
            # 檢查 size 欄位是否為 suprad
            if check_h_column(sheet_data, current_row):
                # 檢查 ad type 欄位的值
                ad_type = check_ad_type(sheet_data, current_row)
                log_message(f"第 {current_row} 行廣告類型: {ad_type}")
                
                # 檢查 A 列是否已標記完成
                if not check_a_column(worksheet, current_row):
                    # 啟動 Playwright 進行自動化操作
                    with sync_playwright() as playwright:
                        status = run_automation(playwright, current_row, sheet_data)
                        try:
                            # 更新 Google Sheet 狀態
                            update_sheet_status(worksheet, current_row, status)
                        except Exception as e:
                            if IGNORE_SHEET_PERMISSION_ERROR:
                                log_message(f"忽略 Google Sheet 更新錯誤: {str(e)}")
                                log_message(f"由於 IGNORE_SHEET_PERMISSION_ERROR=True，程序將繼續執行")
                            else:
                                raise e
                else:
                    log_message(f"第 {current_row} 行已標記為完成")
            else:
                log_message(f"第 {current_row} 行的 '6 size' 欄位不是 suprad，跳過處理")
            current_row += 1

    except Exception as e:
        logging.error(f"主函數出現錯誤: {str(e)}")
        import traceback
        logging.error(traceback.format_exc())

if __name__ == "__main__":
    main()
