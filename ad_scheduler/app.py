import os
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
import json
import re
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from playwright.sync_api import sync_playwright
import logging
import threading
import config
from datetime import datetime

# 設置日誌
log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)
log_file = os.path.join(log_dir, f"ad_scheduler_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler(log_file),
                        logging.StreamHandler()
                    ])

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # 用於flash消息

# 存儲可用的廣告集合
ad_sets = {}
processing_status = {"running": False, "current_row": 0, "total_rows": 0, "success_count": 0, "error_count": 0}

# Google Sheets 設置
def get_sheet_data(sheet_url, range_name, worksheet_index):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(config.GOOGLE_CREDENTIALS_FILE, scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_url(sheet_url)
    worksheet = sheet.get_worksheet(worksheet_index)  # 選擇工作表
    data = worksheet.get(range_name)
    return worksheet, data

def log_message(message):
    logging.info(message)

def fetch_ad_sets():
    """抓取廣告集合列表"""
    ad_sets_list = []
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()

            # 登入
            page.goto("https://account.aotter.net/login?r=https%3A%2F%2Ftrek.aotter.net%2Fme")
            page.get_by_placeholder("Email 帳號").fill(config.EMAIL)
            page.get_by_placeholder("密碼").fill(config.PASSWORD)
            page.get_by_placeholder("密碼").press("Enter")
            
            # 等待登入成功並進入廣告管理頁面
            page.wait_for_load_state("networkidle")
            
            # 點擊用戶名按鈕
            page.get_by_role("button", name="ian.chen").click()
            page.get_by_role("link", name="電豹股份有限公司").click()
            
            # 進入廣告集合頁面
            page.goto("https://trek.aotter.net/advertiser/show/adsets")
            page.wait_for_load_state("networkidle")
            
            # 抓取所有廣告集合
            ad_set_elements = page.locator('a[href^="/advertiser/show/adset?setId="]').all()
            
            for element in ad_set_elements:
                href = element.get_attribute('href')
                set_id = re.search(r'setId=([^&]+)', href).group(1)
                name = element.inner_text().strip()
                ad_sets_list.append({"id": set_id, "name": name})
            
            context.close()
            browser.close()
    except Exception as e:
        log_message(f"Error fetching ad sets: {str(e)}")
    
    return ad_sets_list

def run_ad_creation(ad_data, set_id):
    """執行廣告創建流程"""
    try:
        with sync_playwright() as playwright:
            log_message("Launching browser")
            browser = playwright.chromium.launch(headless=False)
            context = browser.new_context()
            page = context.new_page()

            # 登入
            page.goto("https://account.aotter.net/login?r=https%3A%2F%2Ftrek.aotter.net%2Fme")
            page.get_by_placeholder("Email 帳號").click()
            page.get_by_placeholder("Email 帳號").fill(config.EMAIL)
            page.get_by_placeholder("Email 帳號").press("Tab")
            page.get_by_placeholder("密碼").fill(config.PASSWORD)
            page.get_by_placeholder("密碼").press("Enter")

            # 選擇公司
            page.get_by_role("button", name="ian.chen").click()
            page.get_by_role("link", name="電豹股份有限公司").click()
            
            # 進入指定的廣告集合
            page.goto(f"https://trek.aotter.net/advertiser/show/adset?setId={set_id}")

            # 創建廣告單元
            page.get_by_role("link", name="+  建立廣告單元").click()
            page.wait_for_load_state("domcontentloaded")
            page.wait_for_load_state("networkidle")

            # 填寫廣告單元資料
            page.get_by_role("textbox", name="顯示於後台").click()
            page.get_by_role("textbox", name="顯示於後台").fill(ad_data['display_name'])

            page.get_by_role("textbox", name="廣告商").click()
            page.get_by_role("textbox", name="廣告商").fill(ad_data['advertiser'])

            page.get_by_role("textbox", name="主標題").click()
            page.get_by_role("textbox", name="主標題").fill(ad_data['main_title'])

            page.get_by_role("textbox", name="副標題").click()
            page.get_by_role("textbox", name="副標題").fill(ad_data['subtitle'])

            page.get_by_role("textbox", name="網址（請儘可能使用 HTTPS）").fill(ad_data['landing_page'])
            page.get_by_role("textbox", name="網址（請儘可能使用 HTTPS）").click()
            page.get_by_role("textbox", name="自由輸入").fill(ad_data['call_to_action'])

            # 新增可插入選項
            for _ in range(3):
                page.get_by_role("button", name="").first.click()

            # 插入圖片 - 第一次 (336x280)
            page.get_by_placeholder("請選擇").nth(0).click()
            page.evaluate("""() => {
                const inputs = document.querySelectorAll('input[placeholder="請選擇"]');
                if (inputs.length > 1) {
                    inputs[1].click();
                    setTimeout(() => {
                        const dropdowns = document.querySelectorAll('.el-select-dropdown__list');
                        if (dropdowns.length > 1) {
                            const items = dropdowns[1].querySelectorAll('li.el-select-dropdown__item');
                            for (let item of items) {
                                if (item.textContent.includes('* 橫幅336 (336 × 280)')) {
                                    item.click();
                                    break;
                                }
                            }
                        }
                    }, 500);
                }
            }""")
            page.wait_for_timeout(500)
            
            page.locator('input[type="file"]').nth(1).set_input_files(ad_data['image_336x280'])
            page.get_by_role("button", name="儲存").click()
            page.wait_for_timeout(500)

            # 插入圖片 - 第二次 (1200x628)
            page.locator('input[type="file"]').nth(0).set_input_files(ad_data['image_1200x628'])
            page.get_by_role("button", name="儲存").click()
            page.wait_for_timeout(500)

            # 插入圖片 - 第三次 (640x100)
            page.get_by_placeholder("請選擇").nth(2).click()
            page.locator("span").filter(has_text="橫幅640x100").nth(2).click()
            
            page.locator('input[type="file"]').nth(2).set_input_files(ad_data['image_640x100'])
            page.get_by_role("button", name="儲存").click()

            # 添加追蹤 URL
            if ad_data.get('tracking_url'):
                page.locator("button:has(i.fa-plus)").nth(1).click()
                page.wait_for_selector("input[placeholder='https://...']")
                page.locator("input[placeholder='https://...']").nth(0).fill(ad_data['tracking_url'])

            # 提交廣告
            page.get_by_role("button", name="新增廣告單元").click()
            page.get_by_role("button", name="確定").click()
            
            log_message(f"成功創建廣告: {ad_data['display_name']}")
            context.close()
            browser.close()
            return True
    except Exception as e:
        log_message(f"創建廣告時發生錯誤: {str(e)}")
        return False

def process_bulk_ads(ads_data, set_id):
    """處理批量廣告創建"""
    global processing_status
    processing_status = {
        "running": True,
        "current_row": 0,
        "total_rows": len(ads_data),
        "success_count": 0,
        "error_count": 0
    }
    
    try:
        for i, ad_data in enumerate(ads_data):
            processing_status["current_row"] = i + 1
            success = run_ad_creation(ad_data, set_id)
            
            if success:
                processing_status["success_count"] += 1
            else:
                processing_status["error_count"] += 1
    finally:
        processing_status["running"] = False

@app.route('/')
def index():
    global ad_sets
    # 每次進入主頁面時刷新廣告集合
    ad_sets = fetch_ad_sets()
    return render_template('index.html', ad_sets=ad_sets)

@app.route('/status')
def status():
    return jsonify(processing_status)

@app.route('/create_ad', methods=['POST'])
def create_ad():
    # 取得表單數據
    ad_data = {
        'display_name': request.form.get('display_name'),
        'advertiser': request.form.get('advertiser'),
        'main_title': request.form.get('main_title'),
        'subtitle': request.form.get('subtitle'),
        'landing_page': request.form.get('landing_page'),
        'call_to_action': request.form.get('call_to_action', '瞭解詳情'),
        'tracking_url': request.form.get('tracking_url', ''),
    }
    
    # 取得上傳的圖片
    image_1200x628 = request.files.get('image_1200x628')
    image_640x100 = request.files.get('image_640x100')
    image_336x280 = request.files.get('image_336x280')
    set_id = request.form.get('set_id')
    
    # 確保上傳目錄存在
    upload_dir = "uploads"
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
    
    # 儲存上傳的圖片
    if image_1200x628:
        image_1200x628_path = os.path.join(upload_dir, image_1200x628.filename)
        image_1200x628.save(image_1200x628_path)
        ad_data['image_1200x628'] = image_1200x628_path
    
    if image_640x100:
        image_640x100_path = os.path.join(upload_dir, image_640x100.filename)
        image_640x100.save(image_640x100_path)
        ad_data['image_640x100'] = image_640x100_path
    
    if image_336x280:
        image_336x280_path = os.path.join(upload_dir, image_336x280.filename)
        image_336x280.save(image_336x280_path)
        ad_data['image_336x280'] = image_336x280_path
    
    # 執行廣告創建
    success = run_ad_creation(ad_data, set_id)
    
    if success:
        flash('廣告創建成功！', 'success')
    else:
        flash('廣告創建失敗，請查看日誌檔案。', 'error')
    
    return redirect(url_for('index'))

@app.route('/upload_bulk', methods=['POST'])
def upload_bulk():
    if 'bulk_file' not in request.files:
        flash('未選擇文件', 'error')
        return redirect(url_for('index'))
    
    file = request.files['bulk_file']
    set_id = request.form.get('set_id_bulk')
    
    if file.filename == '':
        flash('未選擇文件', 'error')
        return redirect(url_for('index'))
    
    if file:
        try:
            # 解析上傳的JSON文件
            ads_data = json.loads(file.read())
            
            # 檢查廣告數據
            if not isinstance(ads_data, list):
                flash('無效的JSON格式，必須是廣告數據的數組', 'error')
                return redirect(url_for('index'))
            
            # 啟動後台處理
            thread = threading.Thread(target=process_bulk_ads, args=(ads_data, set_id))
            thread.daemon = True
            thread.start()
            
            flash(f'開始處理{len(ads_data)}個廣告，請查看狀態頁面', 'info')
            return redirect(url_for('index'))
        
        except Exception as e:
            flash(f'處理批量上傳時發生錯誤: {str(e)}', 'error')
            return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True) 