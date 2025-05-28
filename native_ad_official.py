# 完整版，可以正常運作且有防呆 2025/03/10 測試可以正常運作，測試人 Ian

# ======== 腳本設定選項 ========
# 設置為 True 將不顯示瀏覽器界面，設置為 False 將顯示瀏覽器界面
HEADLESS_MODE = True

# 設置為 True 將放慢操作速度，便於觀察和調試
SLOW_MODE = False 

# 慢速模式下的操作延遲時間 (毫秒)
SLOW_MODE_DELAY = 1000

# 設置為 True 時，即使沒有 Google Sheet 寫入權限也繼續執行
IGNORE_SHEET_PERMISSION_ERROR = True
# =============================

import re
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from playwright.sync_api import Playwright, sync_playwright
import logging
import config
from gspread.exceptions import APIError
import time

        # 設置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

        # Google Sheet 的 URL 和範圍
sheet_url = 'https://docs.google.com/spreadsheets/d/1m4ZDj46ZdZMjXS30GA2nzn36s2CEqETrCp_rh4dTmbM/edit?gid=408679682#gid=408679682'
range_name = 'A1:AM100'
row_number = 2  # 開始讀取的行號
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

        # 慢速模式延遲函數
def slow_down(page):
    """當啟用慢速模式時，增加延遲以方便觀察"""
    if SLOW_MODE:
        page.wait_for_timeout(SLOW_MODE_DELAY)

        # Google Sheets 設置
def get_sheet_data(sheet_url, range_name, worksheet_index):
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

def log_message(message):
    logging.info(message)

# 防呆
def check_h_column(sheet_data, row_number):
    target_row = row_number - 1  # 因為索引從0開始
    # 確認是否為 native ad 或 banner ad
    ad_type = sheet_data[target_row][7].strip().lower()
    log_message(f"檢查第 {row_number} 行，廣告類型: {ad_type}")
    return ad_type == 'native' or ad_type == 'banner'  # 7 ad type

# 查看 A 列是否已經打 v 了
def check_a_column(worksheet, row_number):
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

def run(playwright: Playwright, row_number: int, sheet_data) -> bool:
    target_row = row_number - 1  # 因為索引從0開始
    browser = None
    context = None

    try:
        log_message(f"Processing row{row_number}")
        log_message("啟動 arm64 原生 Chrome 穩定版瀏覽器")
        browser = playwright.chromium.launch(
            executable_path="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",  # 指定 arm64 原生 Chrome 路徑
            headless=HEADLESS_MODE,
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
            ]
        )
        context = browser.new_context()
        
        # 增加頁面超時設定
        context.set_default_timeout(60000)  # 設置為 60 秒
        
        page = context.new_page()

        # 首先導航到登入頁面
        log_message("Navigating to login page")
        page.goto("https://account.aotter.net/login?r=https%3A%2F%2Ftrek.aotter.net%2Fme")
        
        # 等待頁面完全加載
        page.wait_for_load_state("networkidle")
        slow_down(page)
        
        log_message("Filling login form")
        # 等待輸入欄位出現
        page.get_by_placeholder("Email 帳號").wait_for(state="visible", timeout=10000)
        page.get_by_placeholder("Email 帳號").click()
        page.get_by_placeholder("Email 帳號").fill(config.EMAIL)
        page.get_by_placeholder("Email 帳號").press("Tab")
        page.get_by_placeholder("密碼").fill(config.PASSWORD)
        page.get_by_placeholder("密碼").press("Enter")
        slow_down(page)
        
        # 確保登入後頁面已完全加載
        log_message("Waiting for login to complete")
        
        # 等待登入完成，有兩種可能的情況：成功登入或登入失敗
        try:
            # 方法 1：等待成功登入後的按鈕出現
            log_message("等待登入成功指示...")
            success = page.get_by_role("button", name="ian.chen").wait_for(state="visible", timeout=30000)
            if success:
                log_message("登入成功！")
            
        except Exception as login_error:
            # 檢查是否為登入失敗
            log_message(f"登入按鈕未出現，檢查是否有錯誤訊息: {str(login_error)}")
            
            # 檢查是否有錯誤訊息
            try:
                error_message = page.get_by_text("帳號或密碼錯誤").is_visible(timeout=5000)
                if error_message:
                    log_message("登入失敗：帳號或密碼錯誤")
                    # 保存登入失敗的截圖
                    page.screenshot(path=f"login_failed_{int(time.time())}.png")
                    raise Exception("登入失敗：帳號或密碼錯誤")
            except:
                # 如果沒有找到錯誤訊息，可能是其他問題
                log_message("無法確定登入狀態，可能網頁結構已變更或網路問題")
                page.screenshot(path=f"login_unknown_{int(time.time())}.png")
                raise Exception("登入過程中遇到未知問題")
        
        # 每個操作後都等待網絡活動完成
        page.wait_for_load_state("networkidle", timeout=30000)
        # page.wait_for_timeout(2000)
        
        # 確保 ian.chen 按鈕可見
        page.get_by_role("button", name="ian.chen").wait_for(state="visible", timeout=10000)
        page.get_by_role("button", name="ian.chen").click()
        
        page.get_by_role("link", name="電豹股份有限公司").wait_for(state="visible", timeout=10000)
        page.get_by_role("link", name="電豹股份有限公司").click()
        # page.wait_for_timeout(2000)
        
        page.goto("https://trek.aotter.net/advertiser/show/campaign?campId=d0b61923-7c69-4c8c-a67a-8014d40e1694")
        # page.wait_for_load_state("networkidle")
        # page.wait_for_timeout(2000)
        
        # 等待 "+  建立廣告" 鏈接可見
        page.get_by_role("link", name="+  建立廣告").click()
        page.wait_for_load_state("networkidle")
        # page.wait_for_timeout(2000)
        
        page.locator(".el-input__inner").first.wait_for(state="visible", timeout=10000)
        page.locator(".el-input__inner").first.click()

            # 廣告-廣告名稱
        page.locator(".el-input__inner").first.fill(sheet_data[target_row][1])  # 1 adsetName 的值 正式 mode
        slow_down(page)
        # page.locator(".el-input__inner").first.fill("（test-native）")  # 測試 mode
        page.get_by_placeholder("開始時間").click()
        page.get_by_placeholder("開始時間").fill("2025-03-12 01:01")
        slow_down(page)
        page.get_by_placeholder("結束時間").click()
        page.get_by_placeholder("結束時間").fill("2025-03-18 16:01")
        slow_down(page)

            # 從 Google Sheet 中獲取對應行的值
        platform_text_1 = sheet_data[target_row][3]  # 3 裝置類型
        platform_text_2 = sheet_data[target_row][4]  # 4 裝置類型（可能為空）

        #             # 把選擇的平台都先去消掉
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
        page.locator("div:nth-child(5) > .col-md-10 > .el-select > .el-select__tags > .el-select__input").fill(sheet_data[target_row][19])  # 19 ClinetId 值
        slow_down(page)
        page.get_by_text(sheet_data[target_row][20]).nth(1).click()  # 20 包含應用程式名稱
        slow_down(page)
        page.locator("div:nth-child(12) > .form-group > div > div > .col-md-10 > .el-select > .el-select__tags > .el-select__input").click()

        #             # place
        log_message("Selecting place")
        page.locator("div:nth-child(12) > .form-group > div > div > .col-md-10 > .el-select > .el-select__tags > .el-select__input").fill(sheet_data[target_row][21]) # 21 UUID 的值
        slow_down(page)
        page.locator("ul").filter(has_text=re.compile(rf"^{sheet_data[target_row][21]}$")).get_by_role("listitem").click() # 21 UUID 的值
        slow_down(page)
        page.get_by_role("spinbutton").nth(1).click()

        page.locator("div").filter(has_text=re.compile(r"^投遞類型 平均投放加強投放$")).get_by_placeholder("請選擇").click()
        page.locator("li").filter(has_text="加強投放").click()
        slow_down(page)

                # 預算類型
        page.locator("div").filter(has_text=re.compile(r"^預算類型 CPCCPMCPV$")).get_by_placeholder("請選擇").click()
        page.locator("li.el-select-dropdown__item").filter(has_text=re.compile(r"^CPM$")).first.click()
        slow_down(page)

                    # 預算
        page.get_by_role("spinbutton").nth(1).fill("4") # 正式 mode
        # page.get_by_role("spinbutton").nth(1).fill("0.001") # 測試 mode
        page.get_by_role("spinbutton").nth(2).click()
        slow_down(page)

                    # 出價
        page.get_by_role("spinbutton").nth(2).fill("0.1") # 正式 mode
        # page.get_by_role("spinbutton").nth(2).fill("0.1") # 測試 mode
        slow_down(page)

        page.get_by_role("button", name="建立廣告").click()
        slow_down(page)
        page.get_by_role("button", name="確定").click()
        slow_down(page)

        page.get_by_role("link", name="建立廣告單元").click()
        slow_down(page)

                    # 廣告單元-廣告商
        page.get_by_role("textbox", name="廣告商").click()
        page.get_by_role("textbox", name="廣告商").fill(sheet_data[target_row][9]) # 9 廣告商
        slow_down(page)

                    # 廣告單元-主標題
        page.get_by_role("textbox", name="主標題").click()
        page.get_by_role("textbox", name="主標題").fill(sheet_data[target_row][10]) # 10 主標題
        slow_down(page)
        
        # 廣告單元-副標題
        log_message("填入副標題...")
        subtitle_value = sheet_data[target_row][11] if len(sheet_data[target_row]) > 11 and sheet_data[target_row][11] else ""
        if subtitle_value:
            # 使用更精確的選擇器，結合 role="textbox" 屬性
            page.get_by_role("textbox", name="副標題").click()
            page.get_by_role("textbox", name="副標題").fill(subtitle_value) # 11 副標題
            log_message(f"已填入副標題: {subtitle_value}")
        else:
            log_message("副標題為空，跳過填寫")
        slow_down(page)
        
        page.get_by_role("textbox", name="網址（請儘可能使用 HTTPS）").fill(sheet_data[target_row][27]) # 27 Landing Page
        page.get_by_role("textbox", name="網址（請儘可能使用 HTTPS）").click()
        page.get_by_role("textbox", name="自由輸入").fill("立即購買") # call to action

        
    # 新增可插入選項
        page.get_by_role("button", name="").first.click()
        page.get_by_role("button", name="").first.click()
        page.get_by_role("button", name="").first.click()
        page.get_by_role("button", name="").first.click()

    # 插入圖片 - 第一次
        absolute_image_path_1 = sheet_data[target_row][15]  # 15 1200x628 的值
        log_message(f"Setting input file for first image: {absolute_image_path_1}")
        page.locator('input[type="file"]').first.set_input_files(absolute_image_path_1)
        page.get_by_role("button", name="儲存").click()
        slow_down(page)

    # # 插入圖片 - 第二次
        page.get_by_placeholder("請選擇").nth(1).click()
        page.get_by_text("* 正方形圖片 (300 × 300)").nth(3).click()
        
        absolute_image_path_2 = sheet_data[target_row][16] # 16 300x300 的值
        log_message(f"Setting input file for second image: {absolute_image_path_2}")
        page.locator('input[type="file"]').nth(1).set_input_files(absolute_image_path_2)
        page.get_by_role("button", name="儲存").click()
        slow_down(page)

    # 插入圖片 - 第三次
        page.get_by_placeholder("請選擇").nth(2).click()
        page.get_by_text("* 橫幅640x100 (640 × 100)").nth(3).click()

        absolute_image_path_3 = sheet_data[target_row][17] # 17 640x100 的值
        log_message(f"Setting input file for third image: {absolute_image_path_3}")
        page.locator('input[type="file"]').nth(2).set_input_files(absolute_image_path_3)
        page.get_by_role("button", name="儲存").click()
        slow_down(page)

    # 插入圖片 - 第四次
        page.get_by_placeholder("請選擇").nth(3).click()
        page.get_by_text("* 橫幅336 (336 × 280)").nth(3).click()
        absolute_image_path_4 = sheet_data[target_row][18] # 18 336x280 的值
        log_message(f"Setting input file for fourth image: {absolute_image_path_4}")
        page.locator('input[type="file"]').nth(3).set_input_files(absolute_image_path_4)
        page.get_by_role("button", name="儲存").click()
        slow_down(page)

        page.get_by_role("button", name="新增廣告單元").click()
        slow_down(page)
        page.get_by_role("button", name="確定").click()
        slow_down(page)

        log_message(f"Successfully processed row {row_number}")
        return True
    except Exception as e:
        log_message(f"Error processing row {row_number}: {str(e)}")
        # 記錄更多詳細的錯誤信息
        import traceback
        log_message(f"詳細錯誤信息: {traceback.format_exc()}")
        
        # 嘗試截圖保存錯誤狀態
        try:
            if 'page' in locals() and page is not None:
                page.screenshot(path=f"error_row_{row_number}_{int(time.time())}.png")
                log_message(f"已保存錯誤截圖")
        except Exception as screenshot_error:
            log_message(f"保存錯誤截圖失敗: {str(screenshot_error)}")
            
        return False
    finally:
        # 確保所有資源都被正確關閉
        try:
            if 'context' in locals() and context is not None:
                context.close()
        except Exception as close_error:
            log_message(f"關閉 context 失敗: {str(close_error)}")
            
        try:
            if 'browser' in locals() and browser is not None:
                browser.close()
        except Exception as close_error:
            log_message(f"關閉 browser 失敗: {str(close_error)}")
            
        log_message(f"資源清理完成")

def main():
    try:
        # 獲取 Google Sheet 數據
        worksheet, sheet_data = get_sheet_data(sheet_url, range_name, worksheet_index)
        
        # 獲取最後一行的行號
        last_row = len(sheet_data)
        
        # 從指定的 row_number 開始循環
        current_row = row_number
        
        # 添加重試機制
        max_retries = 3
        
        log_message(f"總共有 {last_row} 行資料需要處理")
        
        while current_row <= last_row:
            log_message(f"正在檢查第 {current_row} 行")
            
            # 檢查廣告類型是否為 native 或 banner
            if check_h_column(sheet_data, current_row):
                # 檢查 A 列是否已標記完成
                if not check_a_column(worksheet, current_row):
                    log_message(f"開始處理第 {current_row} 行")
                    # 啟動 Playwright 進行自動化操作
                    
                    # 重試邏輯
                    retry_count = 0
                    success = False
                    
                    while retry_count < max_retries and not success:
                        if retry_count > 0:
                            log_message(f"第 {retry_count} 次重試處理第 {current_row} 行")
                        
                        # 啟動 Playwright 進行自動化操作
                        try:
                            with sync_playwright() as playwright:
                                success = run(playwright, current_row, sheet_data)
                                
                                if success:
                                    log_message(f"成功處理第 {current_row} 行")
                                    try:
                                        # 更新 Google Sheet 狀態
                                        update_sheet_status(worksheet, current_row, True)
                                    except Exception as e:
                                        if IGNORE_SHEET_PERMISSION_ERROR:
                                            log_message(f"忽略 Google Sheet 更新錯誤: {str(e)}")
                                            log_message(f"由於 IGNORE_SHEET_PERMISSION_ERROR=True，程序將繼續執行")
                                        else:
                                            raise e
                                else:
                                    log_message(f"處理第 {current_row} 行失敗")
                                    retry_count += 1
                                    
                                    # 在重試前等待一段時間
                                    if retry_count < max_retries:
                                        wait_time = retry_count * 5  # 每次重試增加等待時間
                                        log_message(f"等待 {wait_time} 秒後重試...")
                                        time.sleep(wait_time)
                        except Exception as e:
                            log_message(f"運行自動化時發生錯誤: {str(e)}")
                            retry_count += 1
                            
                            # 在重試前等待一段時間
                            if retry_count < max_retries:
                                wait_time = retry_count * 5  # 每次重試增加等待時間
                                log_message(f"等待 {wait_time} 秒後重試...")
                                time.sleep(wait_time)
                    
                    # 如果所有重試都失敗，更新狀態為失敗
                    if not success:
                        try:
                            update_sheet_status(worksheet, current_row, False)
                            log_message(f"已將第 {current_row} 行標記為失敗")
                        except Exception as e:
                            log_message(f"更新狀態失敗: {str(e)}")
                else:
                    log_message(f"第 {current_row} 行已標記為完成")
            else:
                log_message(f"第 {current_row} 行的廣告類型不是 native 或 banner，跳過處理")
            
            # 繼續處理下一行
            current_row += 1
            
            # 每處理 5 行暫停一下，避免頻繁操作
            if current_row % 5 == 0:
                log_message(f"已處理 {current_row - row_number} 行，暫停 1 秒...")
                time.sleep(1)

        log_message("所有行處理完畢")

    except Exception as e:
        logging.error(f"主函數出現錯誤: {str(e)}")
        import traceback
        logging.error(traceback.format_exc())

if __name__ == "__main__":
    main()
