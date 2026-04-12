# Full version with error handling - verified 2025/03/10

# ======== Script configuration options ========
# Set to True to hide browser, False to show browser
HEADLESS_MODE = True

# Set to True to slow down operations for debugging
SLOW_MODE = False

# Slow mode delay in milliseconds
SLOW_MODE_DELAY = 1000

# Set to True to continue even without Google Sheet write permission
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

        # Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

        # Google Sheet URL and range
sheet_url = 'https://docs.google.com/spreadsheets/d/1m4ZDj46ZdZMjXS30GA2nzn36s2CEqETrCp_rh4dTmbM/edit?gid=408679682#gid=408679682'
range_name = 'A1:AM100'
row_number = 2  # Start reading from row number
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

        # Slow mode delay function
def slow_down(page):
    """Add delay when slow mode is enabled for observation"""
    if SLOW_MODE:
        page.wait_for_timeout(SLOW_MODE_DELAY)

        # Google Sheets setup
def get_sheet_data(sheet_url, range_name, worksheet_index):
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

def log_message(message):
    logging.info(message)

# Error prevention
def check_h_column(sheet_data, row_number):
    target_row = row_number - 1  # Index starts at 0
    # Verify if is native ad or banner ad
    ad_type = sheet_data[target_row][7].strip().lower()
    log_message(f"Checking row {row_number}, ad type: {ad_type}")
    return ad_type == 'native' or ad_type == 'banner'  # Column H / ad type

# Check if column A is marked complete
def check_a_column(worksheet, row_number):
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
            log_message("Program will continue executing, but will not mark completed rows")

def run(playwright: Playwright, row_number: int, sheet_data) -> bool:
    target_row = row_number - 1  # Index starts at 0
    browser = None
    context = None

    try:
        log_message(f"Processing row {row_number}")
        log_message("Launching arm64 native Chrome stable browser")
        browser = playwright.chromium.launch(
            executable_path="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",  # Specify arm64 native Chrome path
            headless=HEADLESS_MODE,
            args=[
                "--disable-gpu",      # Disable GPU for stability
                "--no-sandbox",       # Disable sandbox mode for better stability
                "--disable-dev-shm-usage",  # Avoid shared memory issues
                "--disable-background-timer-throttling",  # Prevent background timer throttling
                "--disable-backgrounding-occluded-windows",  # Prevent background window limiting
                "--disable-renderer-backgrounding",  # Prevent renderer backgrounding
                "--disable-features=TranslateUI",  # Disable translation feature
                "--disable-extensions",  # Disable extensions
                "--disable-plugins",    # Disable plugins
                "--disable-web-security",  # Disable web security restrictions
            ]
        )
        context = browser.new_context()

        # Increase page timeout setting
        context.set_default_timeout(60000)  # Set to 60 seconds

        page = context.new_page()

        # First navigate to login page
        log_message("Navigating to login page")
        page.goto("https://account.example.com/login?r=https%3A%2F%2Fadplatform.example.com%2Fme")

        # Wait for page to fully load
        page.wait_for_load_state("networkidle")
        slow_down(page)

        log_message("Filling login form")
        # Wait for input field to appear
        # Playwright selector targeting external platform UI - keep as-is
        page.get_by_placeholder("Email").wait_for(state="visible", timeout=10000)
        page.get_by_placeholder("Email").click()
        page.get_by_placeholder("Email").fill(config.EMAIL)
        page.get_by_placeholder("Email").press("Tab")
        # Playwright selector targeting external platform UI - keep as-is
        page.get_by_placeholder("Password").fill(config.PASSWORD)
        page.get_by_placeholder("Password").press("Enter")
        slow_down(page)

        # Ensure login completed
        log_message("Waiting for login to complete")

        # Wait for login completion, two possible scenarios: successful login or login failure
        try:
            # Method 1: Wait for success login button to appear
            log_message("Waiting for login success indicator...")
            success = page.get_by_role("button", name="user_account").wait_for(state="visible", timeout=30000)
            if success:
                log_message("Login successful!")

        except Exception as login_error:
            # Check if login failed
            log_message(f"Login button not appeared, checking for error message: {str(login_error)}")

            # Check for error message
            try:
                # Playwright selector targeting external platform UI - keep as-is
                error_message = page.get_by_text("Invalid Email or Password").is_visible(timeout=5000)
                if error_message:
                    log_message("Login failed: Account or password incorrect")
                    # Save login failure screenshot
                    page.screenshot(path=f"login_failed_{int(time.time())}.png")
                    raise Exception("Login failed: Account or password incorrect")
            except:
                # If no error message found, might be other issues
                log_message("Cannot determine login status, page structure may have changed or network issue")
                page.screenshot(path=f"login_unknown_{int(time.time())}.png")
                raise Exception("Encountered unknown issue during login")

        # Wait for network activity to complete after each operation
        page.wait_for_load_state("networkidle", timeout=30000)
        # page.wait_for_timeout(2000)

        # Ensure user_account button is visible
        page.get_by_role("button", name="user_account").wait_for(state="visible", timeout=10000)
        page.get_by_role("button", name="user_account").click()

        page.get_by_role("link", name="Example Organization").wait_for(state="visible", timeout=10000)
        page.get_by_role("link", name="Example Organization").click()
        # page.wait_for_timeout(2000)

        page.goto("https://adplatform.example.com/advertiser/show/campaign?campId=EXAMPLE_CAMPAIGN_ID")
        # page.wait_for_load_state("networkidle")
        # page.wait_for_timeout(2000)

        # Wait for "Create Ad" link to be visible
        # Playwright selector targeting external platform UI - keep as-is
        page.get_by_role("link", name="+  Create Ad").click()
        page.wait_for_load_state("networkidle")
        # page.wait_for_timeout(2000)

        page.locator(".el-input__inner").first.wait_for(state="visible", timeout=10000)
        page.locator(".el-input__inner").first.click()

            # Ad - Ad name
        page.locator(".el-input__inner").first.fill(sheet_data[target_row][1])  # 1 adsetName value Production mode
        slow_down(page)
        # page.locator(".el-input__inner").first.fill("(test-native)")  # Test mode
        # Playwright selector targeting external platform UI - keep as-is
        page.get_by_placeholder("Start Date").click()
        page.get_by_placeholder("Start Date").fill("2025-03-12 01:01")
        slow_down(page)
        # Playwright selector targeting external platform UI - keep as-is
        page.get_by_placeholder("End Date").click()
        page.get_by_placeholder("End Date").fill("2025-03-18 16:01")
        slow_down(page)

            # Get values for corresponding row from Google Sheet
        platform_text_1 = sheet_data[target_row][3]  # Column 3 Device type
        platform_text_2 = sheet_data[target_row][4]  # Column 4 Device type (may be empty)

        #  Uncheck all selected platforms first
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
        page.locator("div:nth-child(5) > .col-md-10 > .el-select > .el-select__tags > .el-select__input").fill(sheet_data[target_row][19])  # 19 ClinetId value
        slow_down(page)
        page.get_by_text(sheet_data[target_row][20]).nth(1).click()  # 20 Contains app name
        slow_down(page)
        page.locator("div:nth-child(12) > .form-group > div > div > .col-md-10 > .el-select > .el-select__tags > .el-select__input").click()

        #  Place
        log_message("Selecting place")
        page.locator("div:nth-child(12) > .form-group > div > div > .col-md-10 > .el-select > .el-select__tags > .el-select__input").fill(sheet_data[target_row][21]) # 21 UUID value
        slow_down(page)
        page.locator("ul").filter(has_text=re.compile(rf"^{sheet_data[target_row][21]}$")).get_by_role("listitem").click() # 21 UUID value
        slow_down(page)
        page.get_by_role("spinbutton").nth(1).click()

        page.locator("div").filter(has_text=re.compile(r"^Delivery Type Average Enhanced$")).get_by_placeholder("Select").click()
        page.locator("li").filter(has_text="Enhanced Delivery").click()
        slow_down(page)

                # Budget type
        page.locator("div").filter(has_text=re.compile(r"^Budget Type CPCCPMCPV$")).get_by_placeholder("Select").click()
        page.locator("li.el-select-dropdown__item").filter(has_text=re.compile(r"^CPM$")).first.click()
        slow_down(page)

                    # Budget
        page.get_by_role("spinbutton").nth(1).fill("4") # Production mode
        # page.get_by_role("spinbutton").nth(1).fill("0.001") # Test mode
        page.get_by_role("spinbutton").nth(2).click()
        slow_down(page)

                    # Bid
        page.get_by_role("spinbutton").nth(2).fill("0.1") # Production mode
        # page.get_by_role("spinbutton").nth(2).fill("0.1") # Test mode
        slow_down(page)

        # Playwright selector targeting external platform UI - keep as-is
        page.get_by_role("button", name="Create Ad").click()
        slow_down(page)
        # Playwright selector targeting external platform UI - keep as-is
        page.get_by_role("button", name="Confirm").click()
        slow_down(page)

        # Playwright selector targeting external platform UI - keep as-is
        page.get_by_role("link", name="Create Ad Unit").click()
        slow_down(page)

                    # Ad Unit - Advertiser
        # Playwright selector targeting external platform UI - keep as-is
        page.get_by_role("textbox", name="Advertiser").click()
        page.get_by_role("textbox", name="Advertiser").fill(sheet_data[target_row][9]) # 9 Advertiser
        slow_down(page)

                    # Ad Unit - Main title
        # Playwright selector targeting external platform UI - keep as-is
        page.get_by_role("textbox", name="Main Title").click()
        page.get_by_role("textbox", name="Main Title").fill(sheet_data[target_row][10]) # 10 Main title
        slow_down(page)

        # Ad Unit - Subtitle
        log_message("Filling subtitle...")
        subtitle_value = sheet_data[target_row][11] if len(sheet_data[target_row]) > 11 and sheet_data[target_row][11] else ""
        if subtitle_value:
            # Use more precise selector combining role="textbox" attribute
            # Playwright selector targeting external platform UI - keep as-is
            page.get_by_role("textbox", name="Subtitle").click()
            page.get_by_role("textbox", name="Subtitle").fill(subtitle_value) # 11 Subtitle
            log_message(f"Subtitle filled: {subtitle_value}")
        else:
            log_message("Subtitle is empty, skipping")
        slow_down(page)

        # Playwright selector targeting external platform UI - keep as-is
        page.get_by_role("textbox", name="Landing Page URL (HTTPS preferred)").fill(sheet_data[target_row][27]) # 27 Landing Page
        page.get_by_role("textbox", name="Landing Page URL (HTTPS preferred)").click()
        # Playwright selector targeting external platform UI - keep as-is
        page.get_by_role("textbox", name="Free Input").fill("Buy Now") # call to action


    # Add insertable options
        page.get_by_role("button", name="").first.click()
        page.get_by_role("button", name="").first.click()
        page.get_by_role("button", name="").first.click()
        page.get_by_role("button", name="").first.click()

    # Insert image - first time
        absolute_image_path_1 = sheet_data[target_row][15]  # 15 1200x628 value
        log_message(f"Setting input file for first image: {absolute_image_path_1}")
        page.locator('input[type="file"]').first.set_input_files(absolute_image_path_1)
        # Playwright selector targeting external platform UI - keep as-is
        page.get_by_role("button", name="Save").click()
        slow_down(page)

    # Insert image - second time
        # Playwright selector targeting external platform UI - keep as-is
        page.get_by_placeholder("Select").nth(1).click()
        page.get_by_text("* Square image (300 × 300)").nth(3).click()

        absolute_image_path_2 = sheet_data[target_row][16] # 16 300x300 value
        log_message(f"Setting input file for second image: {absolute_image_path_2}")
        page.locator('input[type="file"]').nth(1).set_input_files(absolute_image_path_2)
        # Playwright selector targeting external platform UI - keep as-is
        page.get_by_role("button", name="Save").click()
        slow_down(page)

    # Insert image - third time
        # Playwright selector targeting external platform UI - keep as-is
        page.get_by_placeholder("Select").nth(2).click()
        page.get_by_text("* Banner 640x100 (640 × 100)").nth(3).click()

        absolute_image_path_3 = sheet_data[target_row][17] # 17 640x100 value
        log_message(f"Setting input file for third image: {absolute_image_path_3}")
        page.locator('input[type="file"]').nth(2).set_input_files(absolute_image_path_3)
        # Playwright selector targeting external platform UI - keep as-is
        page.get_by_role("button", name="Save").click()
        slow_down(page)

    # Insert image - fourth time
        # Playwright selector targeting external platform UI - keep as-is
        page.get_by_placeholder("Select").nth(3).click()
        page.get_by_text("* Banner 336 (336 × 280)").nth(3).click()
        absolute_image_path_4 = sheet_data[target_row][18] # 18 336x280 value
        log_message(f"Setting input file for fourth image: {absolute_image_path_4}")
        page.locator('input[type="file"]').nth(3).set_input_files(absolute_image_path_4)
        # Playwright selector targeting external platform UI - keep as-is
        page.get_by_role("button", name="Save").click()
        slow_down(page)

        # Playwright selector targeting external platform UI - keep as-is
        page.get_by_role("button", name="Add New Ad Unit").click()
        slow_down(page)
        # Playwright selector targeting external platform UI - keep as-is
        page.get_by_role("button", name="Confirm").click()
        slow_down(page)

        log_message(f"Successfully processed row {row_number}")
        return True
    except Exception as e:
        log_message(f"Error processing row {row_number}: {str(e)}")
        # Record detailed error information
        import traceback
        log_message(f"Detailed error info: {traceback.format_exc()}")

        # Try to save error screenshot
        try:
            if 'page' in locals() and page is not None:
                page.screenshot(path=f"error_row_{row_number}_{int(time.time())}.png")
                log_message(f"Error screenshot saved")
        except Exception as screenshot_error:
            log_message(f"Failed to save error screenshot: {str(screenshot_error)}")

        return False
    finally:
        # Ensure all resources are properly closed
        try:
            if 'context' in locals() and context is not None:
                context.close()
        except Exception as close_error:
            log_message(f"Failed to close context: {str(close_error)}")

        try:
            if 'browser' in locals() and browser is not None:
                browser.close()
        except Exception as close_error:
            log_message(f"Failed to close browser: {str(close_error)}")

        log_message(f"Resource cleanup completed")

def main():
    try:
        # Get Google Sheet data
        worksheet, sheet_data = get_sheet_data(sheet_url, range_name, worksheet_index)

        # Get the last row number
        last_row = len(sheet_data)

        # Start looping from specified row_number
        current_row = row_number

        # Add retry mechanism
        max_retries = 3

        log_message(f"Total {last_row} rows of data to process")

        while current_row <= last_row:
            log_message(f"Checking row {current_row}")

            # Check if ad type is native or banner
            if check_h_column(sheet_data, current_row):
                # Check if column A is marked complete
                if not check_a_column(worksheet, current_row):
                    log_message(f"Starting to process row {current_row}")
                    # Launch Playwright for automation

                    # Retry logic
                    retry_count = 0
                    success = False

                    while retry_count < max_retries and not success:
                        if retry_count > 0:
                            log_message(f"Retry {retry_count} processing row {current_row}")

                        # Launch Playwright for automation
                        try:
                            with sync_playwright() as playwright:
                                success = run(playwright, current_row, sheet_data)

                                if success:
                                    log_message(f"Successfully processed row {current_row}")
                                    try:
                                        # Update Google Sheet status
                                        update_sheet_status(worksheet, current_row, True)
                                    except Exception as e:
                                        if IGNORE_SHEET_PERMISSION_ERROR:
                                            log_message(f"Ignoring Google Sheet update error: {str(e)}")
                                            log_message(f"Because IGNORE_SHEET_PERMISSION_ERROR=True, program will continue")
                                        else:
                                            raise e
                                else:
                                    log_message(f"Failed to process row {current_row}")
                                    retry_count += 1

                                    # Wait a bit before retrying
                                    if retry_count < max_retries:
                                        wait_time = retry_count * 5  # Increase wait time for each retry
                                        log_message(f"Waiting {wait_time} seconds before retry...")
                                        time.sleep(wait_time)
                        except Exception as e:
                            log_message(f"Error running automation: {str(e)}")
                            retry_count += 1

                            # Wait a bit before retrying
                            if retry_count < max_retries:
                                wait_time = retry_count * 5  # Increase wait time for each retry
                                log_message(f"Waiting {wait_time} seconds before retry...")
                                time.sleep(wait_time)

                    # If all retries failed, update status as failure
                    if not success:
                        try:
                            update_sheet_status(worksheet, current_row, False)
                            log_message(f"Marked row {current_row} as failed")
                        except Exception as e:
                            log_message(f"Failed to update status: {str(e)}")
                else:
                    log_message(f"Row {current_row} marked as completed")
            else:
                log_message(f"Row {current_row} ad type is not native or banner, skipping")

            # Continue processing next row
            current_row += 1

            # Pause briefly every 5 rows to avoid frequent operations
            if current_row % 5 == 0:
                log_message(f"Processed {current_row - row_number} rows, pausing 1 second...")
                time.sleep(1)

        log_message("All rows processing completed")

    except Exception as e:
        logging.error(f"Main function error: {str(e)}")
        import traceback
        logging.error(traceback.format_exc())

if __name__ == "__main__":
    main()
