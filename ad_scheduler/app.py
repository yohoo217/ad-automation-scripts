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

# Configure logging
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
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

# Store available ad sets
ad_sets = {}
processing_status = {"running": False, "current_row": 0, "total_rows": 0, "success_count": 0, "error_count": 0}

# Google Sheets setup
def get_sheet_data(sheet_url, range_name, worksheet_index):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(config.GOOGLE_CREDENTIALS_FILE, scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_url(sheet_url)
    worksheet = sheet.get_worksheet(worksheet_index)  # Select worksheet
    data = worksheet.get(range_name)
    return worksheet, data

def log_message(message):
    logging.info(message)

def fetch_ad_sets():
    """Fetch ad set list"""
    ad_sets_list = []
    try:
        with sync_playwright() as playwright:
            log_message("Launching arm64 native Chrome stable browser")
            browser = playwright.chromium.launch(
                executable_path="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",  # Specify arm64 native Chrome path
                headless=False,
                args=[
                    "--disable-gpu",      # Disable GPU for stability
                    "--no-sandbox",       # Disable sandbox for better stability
                    "--disable-dev-shm-usage",  # Avoid shared memory issues
                    "--disable-background-timer-throttling",  # Prevent background timer throttling
                    "--disable-backgrounding-occluded-windows",  # Prevent background window limiting
                    "--disable-renderer-backgrounding",  # Prevent renderer backgrounding
                    "--disable-features=TranslateUI",  # Disable translation UI
                    "--disable-extensions",  # Disable extensions
                    "--disable-plugins",    # Disable plugins
                    "--disable-web-security",  # Disable web security restrictions
                ]
            )
            context = browser.new_context()
            page = context.new_page()

            # Login
            page.goto("https://account.example.com/login?r=https%3A%2F%2Fadplatform.example.com%2Fme")
            # Playwright selector targeting external platform UI - keep as-is
            page.get_by_placeholder("Email").fill(config.EMAIL)
            # Playwright selector targeting external platform UI - keep as-is
            page.get_by_placeholder("Password").fill(config.PASSWORD)
            page.get_by_placeholder("Password").press("Enter")

            # Wait for login to complete and go to ad management page
            page.wait_for_load_state("networkidle")

            # Click username button
            page.get_by_role("button", name="user_account").click()
            page.get_by_role("link", name="Example Organization").click()

            # Go to ad set page
            page.goto("https://adplatform.example.com/advertiser/show/adsets")
            page.wait_for_load_state("networkidle")

            # Fetch all ad sets
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
    """Execute ad creation workflow"""
    try:
        with sync_playwright() as playwright:
            log_message("Launching browser")
            browser = playwright.chromium.launch(headless=False)
            context = browser.new_context()
            page = context.new_page()

            # Login
            page.goto("https://account.example.com/login?r=https%3A%2F%2Fadplatform.example.com%2Fme")
            # Playwright selector targeting external platform UI - keep as-is
            page.get_by_placeholder("Email").click()
            page.get_by_placeholder("Email").fill(config.EMAIL)
            page.get_by_placeholder("Email").press("Tab")
            # Playwright selector targeting external platform UI - keep as-is
            page.get_by_placeholder("Password").fill(config.PASSWORD)
            page.get_by_placeholder("Password").press("Enter")

            # Select company
            page.get_by_role("button", name="user_account").click()
            page.get_by_role("link", name="Example Organization").click()

            # Go to specified ad set
            page.goto(f"https://adplatform.example.com/advertiser/show/adset?setId={set_id}")

            # Create ad unit
            # Playwright selector targeting external platform UI - keep as-is
            page.get_by_role("link", name="+  Create Ad Unit").click()
            page.wait_for_load_state("domcontentloaded")
            page.wait_for_load_state("networkidle")

            # Fill ad unit data
            # Playwright selector targeting external platform UI - keep as-is
            page.get_by_role("textbox", name="Display Name").click()
            page.get_by_role("textbox", name="Display Name").fill(ad_data['display_name'])

            # Playwright selector targeting external platform UI - keep as-is
            page.get_by_role("textbox", name="Advertiser").click()
            page.get_by_role("textbox", name="Advertiser").fill(ad_data['advertiser'])

            # Playwright selector targeting external platform UI - keep as-is
            page.get_by_role("textbox", name="Main Title").click()
            page.get_by_role("textbox", name="Main Title").fill(ad_data['main_title'])

            # Playwright selector targeting external platform UI - keep as-is
            page.get_by_role("textbox", name="Subtitle").click()
            page.get_by_role("textbox", name="Subtitle").fill(ad_data['subtitle'])

            # Playwright selector targeting external platform UI - keep as-is
            page.get_by_role("textbox", name="Landing Page URL (HTTPS preferred)").fill(ad_data['landing_page'])
            page.get_by_role("textbox", name="Landing Page URL (HTTPS preferred)").click()
            # Playwright selector targeting external platform UI - keep as-is
            page.get_by_role("textbox", name="Free Input").fill(ad_data['call_to_action'])

            # Add insertable options
            for _ in range(3):
                page.get_by_role("button", name="").first.click()

            # Insert image - First time (336x280)
            # Playwright selector targeting external platform UI - keep as-is
            page.get_by_placeholder("Select").nth(0).click()
            page.evaluate("""() => {
                const inputs = document.querySelectorAll('input[placeholder="Select"]');
                if (inputs.length > 1) {
                    inputs[1].click();
                    setTimeout(() => {
                        const dropdowns = document.querySelectorAll('.el-select-dropdown__list');
                        if (dropdowns.length > 1) {
                            const items = dropdowns[1].querySelectorAll('li.el-select-dropdown__item');
                            for (let item of items) {
                                if (item.textContent.includes('* Banner336 (336 × 280)')) {
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
            # Playwright selector targeting external platform UI - keep as-is
            page.get_by_role("button", name="Save").click()
            page.wait_for_timeout(500)

            # Insert image - Second time (1200x628)
            page.locator('input[type="file"]').nth(0).set_input_files(ad_data['image_1200x628'])
            # Playwright selector targeting external platform UI - keep as-is
            page.get_by_role("button", name="Save").click()
            page.wait_for_timeout(500)

            # Insert image - Third time (640x100)
            # Playwright selector targeting external platform UI - keep as-is
            page.get_by_placeholder("Select").nth(2).click()
            page.locator("span").filter(has_text="Banner640x100").nth(2).click()

            page.locator('input[type="file"]').nth(2).set_input_files(ad_data['image_640x100'])
            # Playwright selector targeting external platform UI - keep as-is
            page.get_by_role("button", name="Save").click()

            # Add tracking URL
            if ad_data.get('tracking_url'):
                page.locator("button:has(i.fa-plus)").nth(1).click()
                page.wait_for_selector("input[placeholder='https://...']")
                page.locator("input[placeholder='https://...']").nth(0).fill(ad_data['tracking_url'])

            # Submit ad
            # Playwright selector targeting external platform UI - keep as-is
            page.get_by_role("button", name="Add New Ad Unit").click()
            # Playwright selector targeting external platform UI - keep as-is
            page.get_by_role("button", name="Confirm").click()

            log_message(f"Successfully created ad: {ad_data['display_name']}")
            context.close()
            browser.close()
            return True
    except Exception as e:
        log_message(f"Error creating ad: {str(e)}")
        return False

def process_bulk_ads(ads_data, set_id):
    """Process batch ad creation"""
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
    # Refresh ad sets every time main page is accessed
    ad_sets = fetch_ad_sets()
    return render_template('index.html', ad_sets=ad_sets)

@app.route('/status')
def status():
    return jsonify(processing_status)

@app.route('/create_ad', methods=['POST'])
def create_ad():
    # Get form data
    ad_data = {
        'display_name': request.form.get('display_name'),
        'advertiser': request.form.get('advertiser'),
        'main_title': request.form.get('main_title'),
        'subtitle': request.form.get('subtitle'),
        'landing_page': request.form.get('landing_page'),
        'call_to_action': request.form.get('call_to_action', 'Learn more'),
        'tracking_url': request.form.get('tracking_url', ''),
    }

    # Get uploaded images
    image_1200x628 = request.files.get('image_1200x628')
    image_640x100 = request.files.get('image_640x100')
    image_336x280 = request.files.get('image_336x280')
    set_id = request.form.get('set_id')

    # Ensure upload directory exists
    upload_dir = "uploads"
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)

    # Save uploaded images
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

    # Execute ad creation
    success = run_ad_creation(ad_data, set_id)

    if success:
        flash('Ad created successfully!', 'success')
    else:
        flash('Ad creation failed, please check log file.', 'error')

    return redirect(url_for('index'))

@app.route('/upload_bulk', methods=['POST'])
def upload_bulk():
    if 'bulk_file' not in request.files:
        flash('No file selected', 'error')
        return redirect(url_for('index'))

    file = request.files['bulk_file']
    set_id = request.form.get('set_id_bulk')

    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(url_for('index'))

    if file:
        try:
            # Parse uploaded JSON file
            ads_data = json.loads(file.read())

            # Check ad data
            if not isinstance(ads_data, list):
                flash('Invalid JSON format, must be an array of ad data', 'error')
                return redirect(url_for('index'))

            # Start background processing
            thread = threading.Thread(target=process_bulk_ads, args=(ads_data, set_id))
            thread.daemon = True
            thread.start()

            flash(f'Start processing {len(ads_data)} ads, please check status page', 'info')
            return redirect(url_for('index'))

        except Exception as e:
            flash(f'Error processing bulk upload: {str(e)}', 'error')
            return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
