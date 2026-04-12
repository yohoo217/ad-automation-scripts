# Full version with validation - tested and verified 2025/03/10

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

# ======== Script configuration options ========
# Set to True to hide browser, False to show browser
HEADLESS_MODE = True

# Set to True to slow down operations for debugging
SLOW_MODE = False

# Set to True to continue even without Google Sheet write permission
IGNORE_SHEET_PERMISSION_ERROR = False

# Delay time in slow mode (milliseconds)
SLOW_MODE_DELAY = 1000
# ============================

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Slow mode delay function
def slow_down(page):
    """Add delay when slow mode is enabled for observation"""
    if SLOW_MODE:
        page.wait_for_timeout(SLOW_MODE_DELAY)

# Google Sheet URL and range
sheet_url = 'https://docs.google.com/spreadsheets/d/1m4ZDj46ZdZMjXS30GA2nzn36s2CEqETrCp_rh4dTmbM/edit?gid=408679682#gid=408679682'
range_name = 'A1:AM100'
row_number = 2  # Define starting row number to read
worksheet_index = 5  # Select worksheet
worksheet_names = {
    0: "Directory",
    1: "1-SocialForum",
    2: "2-social-forum-web",
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
    23: "16-enterprise-web",
    24: "Template",
    25: "Material Library"
}

# Google Sheets setup
def get_sheet_data(sheet_url, range_name, worksheet_index):
    """Connect to Google Sheets and retrieve data"""
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name('google-credentials.json', scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_url(sheet_url)
    worksheet = sheet.get_worksheet(worksheet_index)  # Select worksheet

    # Get and display worksheet name
    worksheet_name = worksheet.title
    worksheet_desc = worksheet_names.get(worksheet_index, "Unknown worksheet")
    log_message(f"Selected worksheet: Row {worksheet_index} - {worksheet_name}")

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
    # Get current page URL
    current_url = page.url
    # Extract last 36 characters from URL
    last_36_chars = current_url[-36:]
    return last_36_chars

def log_message(message):
    logging.info(message)

# Error prevention
def check_h_column(sheet_data, row_number):
    target_row = row_number - 1  # Index starts at 0
    # Check if is 6 size = rich_media
    return sheet_data[target_row][7].strip().lower() == 'rich_media'  # Column H / ad type

def check_ad_type(sheet_data, row_number):
    target_row = row_number - 1  # Index starts at 0
    # According to Google Sheet title, index 7 corresponds to "Column 7 ad type"
    # Since index starts at 0, actual field index is 7
    ad_type = sheet_data[target_row][7].strip().lower() if len(sheet_data[target_row]) > 7 else ""
    log_message(f"Checking ad type: {ad_type}")
    return ad_type

def check_a_column(worksheet, row_number):
    """Check if column A is marked complete"""
    cell_value = worksheet.acell(f'A{row_number}').value
    return cell_value == 'v'

def update_sheet_status(worksheet, row_number, status):
    cell = f'A{row_number}'
    value = 'v' if status else 'x'
    try:
        # Update method parameter order changed, use new format
        worksheet.update(values=[[value]], range_name=cell, value_input_option='USER_ENTERED')
        if status:
            try:
                worksheet.format(cell, {"backgroundColor": {"red": 1, "green": 0, "blue": 0}})
            except Exception as format_error:
                log_message(f"Unable to set cell format, but value updated: {str(format_error)}")
        log_message(f"Updated row {row_number} status to {'success' if status else 'failure'}")
    except gspread.exceptions.APIError as e:
        log_message(f"Error updating cell {cell}: {str(e)}")
        log_message("Ensure service account in google-credentials.json has edit permission")
        log_message("Solution: In Google Sheet, click Share button and add service account email as editor")
        # Try alternative method
        try:
            worksheet.update_cell(row_number, 1, value)
            log_message(f"Successfully updated cell {cell} using alternative method")
        except Exception as e2:
            log_message(f"Failed to update cell {cell} using alternative method: {str(e2)}")
            log_message("Program will continue but won't mark completed rows")

    # Logic to avoid missing interactive ad unit creation button
def try_click_create_interactive_ad(page, max_attempts=3):
    for attempt in range(max_attempts):
        try:
            log_message(f"Attempt {attempt + 1} to click 'Create Interactive Ad Unit'")
            # Playwright selector targeting external platform UI - keep as-is
            page.get_by_role("link", name="Create Interactive Ad Unit").click(timeout=5000)
            log_message("Successfully clicked 'Create Interactive Ad Unit'")
            return True
        except Exception as e:
            log_message(f"Failed to click 'Create Interactive Ad Unit': {str(e)}")

            if attempt == 0:
                # First failure, zoom to 80%
                log_message("Zooming browser to 80%")
                page.evaluate("document.body.style.zoom = '80%'")
            elif attempt == 1:
                # Second failure, reload page and zoom to 80%
                log_message("Reloading page and zooming to 80%")
                page.reload()
                page.wait_for_load_state('networkidle')
                page.evaluate("document.body.style.zoom = '80%'")

            # Wait a bit for page to respond
            page.wait_for_timeout(2000)

    log_message("Failed to click '+ Create Interactive Ad Unit' after all attempts")
    return False


def run_automation(playwright: Playwright, row_number: int, sheet_data: list) -> bool:
    # Set row number
    target_row = row_number - 1  # Index starts at 0

    log_message(f"Processing row {row_number}")
    log_message("Launching arm64 native Chrome stable browser")
    browser = playwright.chromium.launch(
        executable_path="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",  # Specify arm64 native Chrome path
        headless=HEADLESS_MODE,
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

    # Set slow mode
    if SLOW_MODE:
        context.set_default_timeout(120000)  # Increase timeout to avoid operation timeout in slow mode

    page = context.new_page()

    try:
        log_message("Navigating to login page")
        page.goto("https://account.example.com/login?r=https%3A%2F%2Fadplatform.example.com%2Fme")
        slow_down(page)

        log_message("Filling login form")
        # Playwright selector targeting external platform UI - keep as-is
        page.get_by_placeholder("Email").click()
        page.get_by_placeholder("Email").fill(config.EMAIL)
        page.get_by_placeholder("Email").press("Tab")
        # Playwright selector targeting external platform UI - keep as-is
        page.get_by_placeholder("Password").fill(config.PASSWORD)
        page.get_by_placeholder("Password").press("Enter")
        slow_down(page)

        page.get_by_role("button", name="user_account").click()
        slow_down(page)
        page.get_by_role("link", name="Example Organization").click()
        slow_down(page)
        page.goto("https://adplatform.example.com/advertiser/show/campaign?campId=EXAMPLE_CAMPAIGN_ID")
        slow_down(page)

        # Playwright selector targeting external platform UI - keep as-is
        page.get_by_role("link", name="+  Create Ad").click()
        slow_down(page)
        page.locator(".el-input__inner").first.click()

        # Ad - Ad name
        log_message("Filling ad form")
        page.locator(".el-input__inner").first.fill(sheet_data[target_row][1])  # Column 1 adsetName
        slow_down(page)
        # Playwright selector targeting external platform UI - keep as-is
        page.get_by_placeholder("Start Date").click()
        page.get_by_placeholder("Start Date").fill("2025-03-12 01:00")
        slow_down(page)
        # Playwright selector targeting external platform UI - keep as-is
        page.get_by_placeholder("End Date").click()
        page.get_by_placeholder("End Date").fill("2025-03-18 16:00")
        slow_down(page)
        page.locator("div").filter(has_text=re.compile(r"^\* Ad Type  Image Ad Video Ad Native Interactive Ad$")).get_by_placeholder("Select").click()
        page.get_by_text("Native Interactive Ad").click()
        slow_down(page)

        # Get values for corresponding row from Google Sheet
        platform_text_1 = sheet_data[target_row][3]  # Column 3 Device type
        platform_text_2 = sheet_data[target_row][4]  # Column 4 Device type (may be empty)

        # Uncheck all selected platforms first
        log_message("Selecting platforms")
        page.locator("label").filter(has_text="iOS App").locator("span").nth(1).click()
        page.locator("label").filter(has_text="Android App").locator("span").nth(1).click()
        page.locator("label").filter(has_text="Mobile Web - iOS").locator("span").nth(1).click()
        page.locator("label").filter(has_text="Mobile Web - Android").locator("span").nth(1).click()
        slow_down(page)

        # Platform selection - First platform
        page.locator("label").filter(has_text=platform_text_1).locator("span").nth(1).click()

        # If there is a second platform, select it too
        if platform_text_2 and platform_text_2.strip():
            log_message(f"Selecting second platform: {platform_text_2}")
            page.locator("label").filter(has_text=platform_text_2).locator("span").nth(1).click()
        slow_down(page)

        page.locator("div:nth-child(5) > .col-md-10 > .el-select > .el-select__tags > .el-select__input").click()

        # Channel
        log_message("Filling channel information")
        page.locator("div:nth-child(5) > .col-md-10 > .el-select > .el-select__tags > .el-select__input").fill(sheet_data[target_row][19])  # 19 ClinetId
        slow_down(page)
        page.get_by_text(sheet_data[target_row][20]).nth(1).click()  # 20 Contains app name
        slow_down(page)
        page.locator("div:nth-child(12) > .form-group > div > div > .col-md-10 > .el-select > .el-select__tags > .el-select__input").click()

        # Place
        log_message("Selecting place")
        page.locator("div:nth-child(12) > .form-group > div > div > .col-md-10 > .el-select > .el-select__tags > .el-select__input").fill(sheet_data[target_row][21]) # 21 UUID
        slow_down(page)
        page.locator("ul").filter(has_text=re.compile(rf"^{sheet_data[target_row][21]}$")).get_by_role("listitem").click() # 21 UUID
        slow_down(page)
        page.get_by_role("spinbutton").nth(1).click()

        page.locator("div").filter(has_text=re.compile(r"^Delivery Type  Average Delivery Enhanced Delivery$")).get_by_placeholder("Select").click()
        page.locator("li").filter(has_text="Enhanced Delivery").click()
        slow_down(page)

        # Budget
        log_message("Filling budget and bidding information")
        page.get_by_role("spinbutton").nth(1).fill("4") # Production mode
        page.get_by_role("spinbutton").nth(2).click()
        slow_down(page)

        # Budget type
        page.locator("div").filter(has_text=re.compile(r"^Budget Type  CPCCPMCPV$")).get_by_placeholder("Select").click()
        page.locator("li").filter(has_text="CPM").click()
        slow_down(page)

        # Bid
        page.get_by_role("spinbutton").nth(2).fill("0.1") # Production mode
        slow_down(page)
        # Playwright selector targeting external platform UI - keep as-is
        page.get_by_role("button", name="Create Ad").click()
        slow_down(page)
        # Playwright selector targeting external platform UI - keep as-is
        page.get_by_role("button", name="Confirm").click()

        # Waiting for page load to complete
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

        # Ensure page is stable before zooming operations
        log_message("Waiting for page to stabilize before zooming...")
        page.wait_for_load_state('networkidle', timeout=30000)
        page.wait_for_timeout(2000)  # Additional wait for 2 seconds to ensure page is completely stable

        try:
            # Zoom page to 80% and then try to click
            page.evaluate("document.body.style.zoom = '80%'")
            log_message("Successfully zoomed page to 80%")
        except Exception as e:
            log_message(f"Error zooming page: {str(e)}")
            # Retry zoom operation
            page.wait_for_timeout(3000)  # Wait additional time
            try:
                page.evaluate("document.body.style.zoom = '80%'")
                log_message("Second attempt to zoom page successful")
            except Exception as e2:
                log_message(f"Second attempt to zoom page failed: {str(e2)}")
                # Continue anyway, hoping page can be operated normally

        # Wait before clicking to ensure zoom has been applied
        page.wait_for_timeout(1000)

        try:
            page.locator("input[name=\"advertiserName\"]").click()
            log_message("Successfully clicked advertiserName input box")
        except Exception as e:
            log_message(f"Failed to click advertiserName input box: {str(e)}")
            # Try using JavaScript to directly click
            try:
                page.evaluate("""
                    document.querySelector("input[name='advertiserName']").focus();
                """)
                log_message("Successfully focused advertiserName input box using JavaScript")
            except Exception as e2:
                log_message(f"Failed to focus advertiserName input box using JavaScript: {str(e2)}")
                # Finally try reloading page and trying again
                page.reload()
                page.wait_for_load_state('networkidle')
                page.wait_for_timeout(3000)
                page.evaluate("document.body.style.zoom = '80%'")
                page.wait_for_timeout(1000)
                page.locator("input[name=\"advertiserName\"]").click()
                log_message("Successfully clicked advertiserName input box after page reload")

        # Ad Unit - Advertiser
        log_message("Filling ad unit information")
        page.locator("input[name=\"advertiserName\"]").fill(sheet_data[target_row][9])  # 9 Advertiser
        slow_down(page)
        page.locator("input[name=\"title\"]").click()

        # Ad Unit - Main title
        page.locator("input[name=\"title\"]").fill(sheet_data[target_row][10])  # 10 Main title
        slow_down(page)
        # Playwright selector targeting external platform UI - keep as-is
        page.get_by_placeholder("Mobile loading page for Ad").click()

        # Select 1200x628 image
        log_message("Selecting 1200x628 image button")

        # Use absolute path to upload image
        absolute_image_path_1 = sheet_data[target_row][15]  # 15 1200x628
        log_message(f"Setting input file for first image: {absolute_image_path_1}")

        # Ensure file exists
        if not os.path.exists(absolute_image_path_1):
            log_message(f"Warning: Image file does not exist: {absolute_image_path_1}")
            # Continue anyway, but record warning

        # Set file upload
        page.set_input_files('input[type="file"]', absolute_image_path_1)
        slow_down(page)
        page.wait_for_timeout(2000)  # Ensure file upload complete

        # Wait for upload button to appear
        log_message("Waiting for image upload to complete...")
        try:
            page.get_by_text("Upload selected area").wait_for(state="visible", timeout=60000)
            # Wait for button to be available
            page.wait_for_timeout(1500)  # Give longer wait time
            page.get_by_text("Upload selected area").click()
            log_message("Successfully clicked upload button")
        except Exception as e:
            log_message(f"Warning: Upload button click failed: {str(e)}")
            # Try alternative method
            try:
                # Playwright selector targeting external platform UI - keep as-is
                page.get_by_role("button", name="Upload Selected Area").click()
                log_message("Use alternative method to click upload button")
            except Exception as e2:
                log_message(f"Warning: Unable to click upload button: {str(e2)}")
                # Continue anyway, but record warning

        # Wait for network activity to complete
        log_message("Waiting for image processing...")
        page.wait_for_timeout(3000)  # Wait fixed time first
        page.wait_for_load_state('networkidle', timeout=60000)
        slow_down(page)

        # Select 300x300 image
        log_message("Selecting 300x300 image button")

        # Use absolute path to upload image
        absolute_image_path_2 = sheet_data[target_row][16]
        log_message(f"Setting input file for second image: {absolute_image_path_2}")

        # Ensure file exists
        if not os.path.exists(absolute_image_path_2):
            log_message(f"Warning: 300x300 image file does not exist: {absolute_image_path_2}")
            # Continue anyway, but record warning

        # Set file upload
        page.locator('input[type="file"]').nth(1).set_input_files(absolute_image_path_2)
        slow_down(page)
        page.wait_for_timeout(2000)  # Ensure file upload complete

        # Wait for upload button to appear
        log_message("Waiting for 300x300 image upload...")
        try:
            page.get_by_text("Upload selected area").wait_for(state="visible", timeout=60000)
            # Wait for button to be available
            page.wait_for_timeout(1500)  # Give longer wait time
            page.get_by_text("Upload selected area").click()
            log_message("Successfully clicked 300x300 upload button")
        except Exception as e:
            log_message(f"Warning: 300x300 upload button click failed: {str(e)}")
            # Try alternative method
            try:
                # Playwright selector targeting external platform UI - keep as-is
                page.get_by_role("button", name="Upload Selected Area").click()
                log_message("Use alternative method to click 300x300 upload button")
            except Exception as e2:
                log_message(f"Warning: Unable to click 300x300 upload button: {str(e2)}")
                # Continue anyway, but record warning

        # Wait for network activity to complete
        log_message("Waiting for 300x300 image processing...")
        page.wait_for_timeout(3000)  # Wait fixed time first
        page.wait_for_load_state('networkidle', timeout=60000)
        slow_down(page)

        # URL
        # Playwright selector targeting external platform UI - keep as-is
        page.get_by_placeholder("Mobile loading page for Ad").fill(sheet_data[target_row][27])  # 27 Landing page
        slow_down(page)

        # Text description - use already verified method (name attribute)
        log_message("Filling text description...")
        text_input = page.locator('input[name="text"]')
        text_input.click()
        text_input.fill(sheet_data[target_row][11])  # 11 Subtitle
        log_message("Text description filled")
        slow_down(page)

        # Playwright selector targeting external platform UI - keep as-is
        page.get_by_placeholder("bg_placeholder: background").click()

        # Call to action - use already verified method (direct input)
        log_message("Set call to action...")
        cta_input = page.locator('input[name="callToAction"]')
        cta_input.click()
        cta_input.fill("Buy Now")
        log_message("Filled 'Buy Now'")
        slow_down(page)

        # Game kit default background
        # Playwright selector targeting external platform UI - keep as-is
        page.get_by_placeholder("bg_placeholder: background").fill(sheet_data[target_row][12])  # 12 Image 1
        slow_down(page)
        page.once("dialog", lambda dialog: dialog.dismiss())
        # Playwright selector targeting external platform UI - keep as-is
        page.get_by_placeholder("urlInteractivePopup: url to").click()

        # Multi-target popup URL - use fixed popup URL
        urlInteractivePopups = "https://cdn.example.com/popup/"  # Use fixed popup URL
        # Playwright selector targeting external platform UI - keep as-is
        page.get_by_placeholder("urlInteractivePopup: url to").fill(urlInteractivePopups)
        slow_down(page)
        page.locator("textarea[name=\"payload_gameWidgetJson\"]").click()
        page.locator("textarea[name=\"payload_gameWidgetJson\"]").press("ControlOrMeta+a")

        # payload_gameWidget
        payload_gameWidget = sheet_data[target_row][29]  # 29 payload_gameWidget (to CatWalk)
        page.locator("textarea[name=\"payload_gameWidgetJson\"]").fill(payload_gameWidget)
        slow_down(page)
        page.wait_for_timeout(2000)

        # Playwright selector targeting external platform UI - keep as-is
        page.get_by_role("button", name="Add New").click()
        slow_down(page)
        # Playwright selector targeting external platform UI - keep as-is
        page.get_by_role("button", name="OK").wait_for(state="visible")
        page.wait_for_timeout(2000)
        page.get_by_role("button", name="OK").click()
        slow_down(page)

        page.wait_for_timeout(2000)
        # Playwright selector targeting external platform UI - keep as-is
        page.get_by_role("link", name="  Interactive Ad Editor").wait_for(state="visible")
        page.get_by_role("link", name="  Interactive Ad Editor").click()
        slow_down(page)

        page.wait_for_load_state('networkidle')
        slow_down(page)

        last_36_chars = extract_last_36_chars_from_url(page)

        # Get current value of another placeholder
        target_placeholder = page.get_by_placeholder("urlInteractivePopup: url to")
        current_value = target_placeholder.input_value()

        # Add last 36 characters to end of current value
        new_value = current_value + last_36_chars

        # Fill new value
        target_placeholder.fill(new_value)
        slow_down(page)

        # Playwright selector targeting external platform UI - keep as-is
        page.get_by_role("button", name="Edit").wait_for(state="visible")
        page.get_by_role("button", name="Edit").click()
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
        # Get Google Sheet data
        worksheet, sheet_data = get_sheet_data(sheet_url, range_name, worksheet_index)

        # Get last row number
        last_row = len(sheet_data)

        # Start looping from specified row_number
        current_row = row_number
        while current_row <= last_row:
            log_message(f"Checking row {current_row}")

            # Check if Column 6 size field is rich_media
            if check_h_column(sheet_data, current_row):
                # Check if Column H field indicates rich_media
                ad_type = check_ad_type(sheet_data, current_row)
                log_message(f"Row {current_row} ad type: {ad_type}")

                # Check if Column A is marked as complete
                if not check_a_column(worksheet, current_row):
                    # Launch Playwright for automation
                    with sync_playwright() as playwright:
                        status = run_automation(playwright, current_row, sheet_data)
                        try:
                            # Update Google Sheet status
                            update_sheet_status(worksheet, current_row, status)
                        except Exception as e:
                            if IGNORE_SHEET_PERMISSION_ERROR:
                                log_message(f"Ignoring Google Sheet update error: {str(e)}")
                                log_message(f"Because IGNORE_SHEET_PERMISSION_ERROR=True, program will continue")
                            else:
                                raise e
                else:
                    log_message(f"Row {current_row} marked as complete")
            else:
                log_message(f"Row {current_row} Column '6 size' field is not rich_media, skipping")
            current_row += 1

    except Exception as e:
        logging.error(f"Main function error: {str(e)}")
        import traceback
        logging.error(traceback.format_exc())

if __name__ == "__main__":
    main()
