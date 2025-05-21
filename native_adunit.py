# 完整版，可以正常運作且有防呆 2024/11/27 測試可以正常運作，測試人 Ian

import re
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from playwright.sync_api import Playwright, sync_playwright
import logging
import config

        # 設置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

        # Google Sheet 的 URL 和範圍
sheet_url = 'https://docs.google.com/spreadsheets/d/1woVCnokdOxZbwN3kzqrO_DfENyZH-7ls84kvKxnysfw/edit?usp=sharing'
range_name = 'A1:AD80'
row_number = 11  # 開始讀取的行號(通常從 2 開始，1 是標題)
worksheet_index = 0  # 選擇工作表

        # Google Sheets 設置
def get_sheet_data(sheet_url, range_name, worksheet_index):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name('/Users/aotter/Documents/批次建廣告流程/booming-alchemy-384405-53ca11c6903d.json', scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_url(sheet_url)
    worksheet = sheet.get_worksheet(worksheet_index)  # 選擇工作表
    data = worksheet.get(range_name)
    return worksheet, data

def log_message(message):
    logging.info(message)

# 防呆
def check_g_column(sheet_data, row_number):
    target_row = row_number - 1  # 因為索引從0開始
    return sheet_data[target_row][6].strip().lower() == 'suprad'  # G列 / adtype 的索引為6

# 查看 A 列是否已經打 v 了
def check_a_column(worksheet, row_number):
    cell_value = worksheet.acell(f'A{row_number}').value
    return cell_value == 'v'

def update_sheet_status(worksheet, row_number, status):
    cell = f'A{row_number}'
    value = 'v' if status else 'x'
    try:
        worksheet.update(cell, [[value]], value_input_option='USER_ENTERED')
        if status:
            worksheet.format(cell, {"backgroundColor": {"red": 1,"green":0, "blue":0}})
        log_message(f"Updated row {row_number} status to {'success' if status else 'failure'}")
    except gspread.exceptions.APIError as e:
        log_message(f"Error updating cell {cell}: {str(e)}")
        # 嘗試替代方法
        try:
            worksheet.update_cell(row_number, 1, value)
            log_message(f"Successfully updated cell {cell} using alternative method")
        except Exception as e2:
            log_message(f"Failed to update cell {cell} using alternative method: {str(e2)}")

# 在文件頂部添加導入
from gspread.exceptions import APIError


def run(playwright: Playwright, row_number: int, sheet_data) -> bool:
    target_row = row_number - 1  # 因為索引從0開始

    try:
        log_message(f"Processing row{row_number}")
        log_message("Launching brower")
        browser = playwright.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        page.goto("https://account.aotter.net/login?r=https%3A%2F%2Ftrek.aotter.net%2Fme")

        page.get_by_placeholder("Email 帳號").click()
        page.get_by_placeholder("Email 帳號").fill(config.EMAIL)
        page.get_by_placeholder("Email 帳號").press("Tab")
        page.get_by_placeholder("密碼").fill(config.PASSWORD)
        page.get_by_placeholder("密碼").press("Enter")

        page.get_by_role("button", name="ian.chen").click()
        page.get_by_role("link", name="電豹股份有限公司").click()
        page.goto("https://trek.aotter.net/advertiser/show/adset?setId=00947c1b-f7cd-47c6-a23a-0639e9702cc7")

        page.get_by_role("link", name="+  建立廣告單元").click()

        page.wait_for_load_state("domcontentloaded")
        page.wait_for_load_state("networkidle")

        #             # 廣告單元-顯示名稱
        page.get_by_role("textbox", name="顯示於後台").click()
        page.get_by_role("textbox", name="顯示於後台").fill(sheet_data[target_row][29]) # AD 列 / 顯示名稱

                    # 廣告單元-廣告商
        page.get_by_role("textbox", name="廣告商").click()
        page.get_by_role("textbox", name="廣告商").fill(sheet_data[target_row][8]) # I 列 / 廣告商

                    # 廣告單元-主標題
        page.get_by_role("textbox", name="主標題").click()
        page.get_by_role("textbox", name="主標題").fill(sheet_data[target_row][9]) # J 列 / 主標題

                    # 廣告單元-副標題
        page.get_by_role("textbox", name="副標題").click()
        page.get_by_role("textbox", name="副標題").fill(sheet_data[target_row][26]) # AA 列 / 副標題

        page.get_by_role("textbox", name="網址（請儘可能使用 HTTPS）").fill(sheet_data[target_row][24]) # Landing Page
        page.get_by_role("textbox", name="網址（請儘可能使用 HTTPS）").click()
        page.get_by_role("textbox", name="自由輸入").fill("瞭解詳情") # call to action

        
    # 新增可插入選項
        page.get_by_role("button", name="").first.click()
        page.get_by_role("button", name="").first.click()
        page.get_by_role("button", name="").first.click()
        # page.get_by_role("button", name="").first.click()

   # 插入圖片 - 第一次
        # 在點擊之前添加等待
        page.get_by_placeholder("請選擇").nth(0).click()
        # 使用 JavaScript 找到並點擊包含特定文字的選項，不知道為什麼這會改到第一個圖片，所以第一個圖片會變成 336x280
        page.evaluate("""() => {
            // 先點擊第一個下拉選單
            const inputs = document.querySelectorAll('input[placeholder="請選擇"]');
            if (inputs.length > 1) {
                inputs[1].click();
                
                // 給一點時間讓下拉選單出現
                setTimeout(() => {
                    // 找到所有下拉選單
                    const dropdowns = document.querySelectorAll('.el-select-dropdown__list');
                    // 選擇第一個下拉選單（索引為1）
                    if (dropdowns.length > 1) {
                    // 選擇要選定的上傳項目，要改第一個就輸入 [1]，要改第二個就輸入 [2]
                        const items = dropdowns[1].querySelectorAll('li.el-select-dropdown__item');
                        for (let item of items) {
                            if (item.textContent.includes('* 橫幅336 (336 × 280)')) {
                                item.click();
                                break;
                            }
                        }
                    }
                }, 500); // 等待500毫秒
            }
        }""")
        page.wait_for_timeout(500)  # 等待1秒

        absolute_image_path_2 = sheet_data[target_row][15] # P 列 / 300x250 的值
        log_message(f"Setting input file for second image: {absolute_image_path_2}")
        page.locator('input[type="file"]').nth(1).set_input_files(absolute_image_path_2)
        page.get_by_role("button", name="儲存").click()
        page.wait_for_timeout(500)  # 等待1秒

    # 插入圖片 - 第二次，因為 input 位置名稱都重複，位置順序又會因為新增插入選項而變動，所以順序現在看起來怪怪的，但可以 work
        absolute_image_path_1 = sheet_data[target_row][12]  # 1200x628 的值
        log_message(f"Setting input file for first image: {absolute_image_path_1}")
        page.locator('input[type="file"]').nth(0).set_input_files(absolute_image_path_1)
        page.get_by_role("button", name="儲存").click()

        page.wait_for_timeout(500)  # 等待1秒


    # 插入圖片 - 第三次
        page.get_by_placeholder("請選擇").nth(2).click()
        page.locator("span").filter(has_text="橫幅640x100").nth(2).click()

        absolute_image_path_3 = sheet_data[target_row][14] # O 列 / 640x100 的值
        log_message(f"Setting input file for first image: {absolute_image_path_3}")
        page.locator('input[type="file"]').nth(2).set_input_files(absolute_image_path_3)
        page.get_by_role("button", name="儲存").click()

        
    # # 插入圖片 - 第四次
    #     page.get_by_placeholder("請選擇").nth(3).click()
    #     page.get_by_text("* 橫幅336 (336 × 280)").nth(3).click()

    #     absolute_image_path_4 = sheet_data[target_row][15] # 300x250 的值
    #     log_message(f"Setting input file for first image: {absolute_image_path_4}")
    #     page.locator('input[type="file"]').nth(3).set_input_files(absolute_image_path_4)
    #     page.get_by_role("button", name="儲存").click()


        # # Try different ways to click the add tracking URL button
        # try:
        #     # Try using text content
        #     page.get_by_role("button", name=" ").click()
        # except:
        #     try:
        #         # Try using a more specific selector
        #         page.locator("button.btn.btn-default.m-t-10").click()
        #     except:
        #         # Try using JavaScript as a fallback
        #         page.evaluate("""() => {
        #             const buttons = document.querySelectorAll('button.btn.btn-default.m-t-10');
        #             for (const button of buttons) {
        #                 if (button.querySelector('i.fa.fa-plus')) {
        #                     button.click();
        #                     break;
        #                 }
        #             }
        #         }""")

        # # Wait a bit after clicking
        # page.wait_for_timeout(1000)

        page.locator("button:has(i.fa-plus)").nth(1).click()  # 點擊第一個按鈕

        # Fill the tracking URL
        page.wait_for_selector("input[placeholder='https://...']")  # 確保元素已加載
        page.locator("input[placeholder='https://...']").nth(0).fill(sheet_data[target_row][28])


        page.get_by_role("button", name="新增廣告單元").click()
        page.get_by_role("button", name="確定").click()

        log_message(f"Successfully processed row {row_number}")
        return True
    except Exception as e:
        log_message(f"Error processing row {row_number}: {str(e)}")
        return False

                # 保持瀏覽器打開
    # print("Automation completed. You can now interact with the browser. Press Ctrl+C to close the script.")
    # while True:
    #     pass
    
    finally:
        if 'context' in locals():
            context.close()
        if 'browser' in locals():
            browser.close()

# 主程序
worksheet, sheet_data = get_sheet_data(sheet_url, range_name, worksheet_index)

with sync_playwright() as playwright:
    while row_number <= len(sheet_data):
        try:
            if check_a_column(worksheet, row_number):
                log_message(f"Row {row_number} already processed, skipping")
            elif check_g_column(sheet_data, row_number):
                log_message(f"Row {row_number} skipped as adtype 是 'suprad'")
            else:
                log_message(f"Starting to process row {row_number}")
                success = run(playwright, row_number, sheet_data)
                log_message(f"Finished processing row {row_number}, success: {success}")
                update_sheet_status(worksheet, row_number, success)

        except Exception as e:
            log_message(f"Unexpected error processing row {row_number}: {str(e)}")
            update_sheet_status(worksheet, row_number, False)
        finally:
            row_number += 1

log_message("所有行處理完畢")
