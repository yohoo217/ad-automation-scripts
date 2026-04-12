# Full version with validation - tested and verified 2024/11/27

import re
import gspread
import platform,sys,subprocess,shlex,os
from oauth2client.service_account import ServiceAccountCredentials
from playwright.sync_api import Playwright, sync_playwright
import logging
import config

        # Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

        # Google Sheet URL and range
sheet_url = 'https://docs.google.com/spreadsheets/d/1woVCnokdOxZbwN3kzqrO_DfENyZH-7ls84kvKxnysfw/edit?usp=sharing'
range_name = 'A1:AD80'
row_number = 11  # Start reading from row number (normally 2 for data, 1 is header)
worksheet_index = 0  # Select worksheet

        # Google Sheets setup
def get_sheet_data(sheet_url, range_name, worksheet_index):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name('/path/to/your/google-credentials.json', scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_url(sheet_url)
    worksheet = sheet.get_worksheet(worksheet_index)  # Select worksheet
    data = worksheet.get(range_name)
    return worksheet, data

def log_message(message):
    logging.info(message)

# Data validation check
def check_g_column(sheet_data, row_number):
    target_row = row_number - 1  # Index starts at 0
    return sheet_data[target_row][6].strip().lower() == 'rich_media'  # Column G / adtype index is 6

# Check if column A is marked as complete
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
        # Try alternative method
        try:
            worksheet.update_cell(row_number, 1, value)
            log_message(f"Successfully updated cell {cell} using alternative method")
        except Exception as e2:
            log_message(f"Failed to update cell {cell} using alternative method: {str(e2)}")

# Import at file top
from gspread.exceptions import APIError


def run(playwright: Playwright, row_number: int, sheet_data) -> bool:
    target_row = row_number - 1  # Index starts at 0

    try:
        log_message(f"Processing row{row_number}")
        log_message("Launching arm64 native Chrome stable browser")
        browser = playwright.chromium.launch(
            executable_path="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",  # Specify arm64 native Chrome path
            headless=True,           # Run in headless mode
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
            ],
        )
        context = browser.new_context()
        page = context.new_page()

        page.goto("https://account.example.com/login?r=https%3A%2F%2Fadplatform.example.com%2Fme")

        # Playwright selector targeting external platform UI - keep as-is
        page.get_by_placeholder("Email").click()
        page.get_by_placeholder("Email").fill(config.EMAIL)
        page.get_by_placeholder("Email").press("Tab")
        # Playwright selector targeting external platform UI - keep as-is
        page.get_by_placeholder("Password").fill(config.PASSWORD)
        page.get_by_placeholder("Password").press("Enter")

        page.get_by_role("button", name="user_account").click()
        page.get_by_role("link", name="Example Organization").click()
        page.goto("https://adplatform.example.com/advertiser/show/adset?setId=EXAMPLE_ADSET_ID")

        # Playwright selector targeting external platform UI - keep as-is
        page.get_by_role("link", name="+  Create Ad Unit").click()

        page.wait_for_load_state("domcontentloaded")
        page.wait_for_load_state("networkidle")

        # Ad Unit - Display name
        # Playwright selector targeting external platform UI - keep as-is
        page.get_by_role("textbox", name="Display Name").click()
        page.get_by_role("textbox", name="Display Name").fill(sheet_data[target_row][29]) # Column AD / Display name

        # Ad Unit - Advertiser
        # Playwright selector targeting external platform UI - keep as-is
        page.get_by_role("textbox", name="Advertiser").click()
        page.get_by_role("textbox", name="Advertiser").fill(sheet_data[target_row][8]) # Column I / Advertiser

        # Ad Unit - Main title
        # Playwright selector targeting external platform UI - keep as-is
        page.get_by_role("textbox", name="Main Title").click()
        page.get_by_role("textbox", name="Main Title").fill(sheet_data[target_row][9]) # Column J / Main title

        # Ad Unit - Subtitle
        # Playwright selector targeting external platform UI - keep as-is
        page.get_by_role("textbox", name="Subtitle").click()
        page.get_by_role("textbox", name="Subtitle").fill(sheet_data[target_row][26]) # Column AA / Subtitle

        # Playwright selector targeting external platform UI - keep as-is
        page.get_by_role("textbox", name="Landing Page URL (HTTPS preferred)").fill(sheet_data[target_row][24]) # Landing Page
        page.get_by_role("textbox", name="Landing Page URL (HTTPS preferred)").click()
        # Playwright selector targeting external platform UI - keep as-is
        page.get_by_role("textbox", name="Free Input").fill("Learn more") # Call to action


    # Add insertable options
        page.get_by_role("button", name="").first.click()
        page.get_by_role("button", name="").first.click()
        page.get_by_role("button", name="").first.click()
        # page.get_by_role("button", name="").first.click()

   # Insert image - first time
        # Add wait before clicking
        # Playwright selector targeting external platform UI - keep as-is
        page.get_by_placeholder("Select").nth(0).click()
        # Use JavaScript to find and click specific option
        page.evaluate("""() => {
            // First click on the first dropdown menu
            const inputs = document.querySelectorAll('input[placeholder="Select"]');
            if (inputs.length > 1) {
                inputs[1].click();

                // Give time for dropdown to appear
                setTimeout(() => {
                    // Find all dropdowns
                    const dropdowns = document.querySelectorAll('.el-select-dropdown__list');
                    // Select first dropdown (index 1)
                    if (dropdowns.length > 1) {
                    // Select upload item to modify
                        const items = dropdowns[1].querySelectorAll('li.el-select-dropdown__item');
                        for (let item of items) {
                            if (item.textContent.includes('* Banner336 (336 × 280)')) {
                                item.click();
                                break;
                            }
                        }
                    }
                }, 500); // Wait 500ms
            }
        }""")
        page.wait_for_timeout(500)  # Wait 1 second

        absolute_image_path_2 = sheet_data[target_row][15] # Column P / 300x250 value
        log_message(f"Setting input file for second image: {absolute_image_path_2}")
        page.locator('input[type="file"]').nth(1).set_input_files(absolute_image_path_2)
        # Playwright selector targeting external platform UI - keep as-is
        page.get_by_role("button", name="Save").click()
        page.wait_for_timeout(500)  # Wait 1 second

    # Insert image - second time (input position names are repeated)
        absolute_image_path_1 = sheet_data[target_row][12]  # 1200x628 value
        log_message(f"Setting input file for first image: {absolute_image_path_1}")
        page.locator('input[type="file"]').nth(0).set_input_files(absolute_image_path_1)
        # Playwright selector targeting external platform UI - keep as-is
        page.get_by_role("button", name="Save").click()

        page.wait_for_timeout(500)  # Wait 1 second


    # Insert image - third time
        # Playwright selector targeting external platform UI - keep as-is
        page.get_by_placeholder("Select").nth(2).click()
        page.locator("span").filter(has_text="Banner640x100").nth(2).click()

        absolute_image_path_3 = sheet_data[target_row][14] # Column O / 640x100 value
        log_message(f"Setting input file for first image: {absolute_image_path_3}")
        page.locator('input[type="file"]').nth(2).set_input_files(absolute_image_path_3)
        # Playwright selector targeting external platform UI - keep as-is
        page.get_by_role("button", name="Save").click()


    # Insert image - fourth time (commented out)
    #     # Playwright selector targeting external platform UI - keep as-is
    #     page.get_by_placeholder("Select").nth(3).click()
    #     page.get_by_text("* Banner336 (336 × 280)").nth(3).click()

    #     absolute_image_path_4 = sheet_data[target_row][15] # 300x250 value
    #     log_message(f"Setting input file for first image: {absolute_image_path_4}")
    #     page.locator('input[type="file"]').nth(3).set_input_files(absolute_image_path_4)
    #     # Playwright selector targeting external platform UI - keep as-is
    #     page.get_by_role("button", name="Save").click()


        # Try different ways to click the add tracking URL button
        # try:
        #     Try using text content
        #     page.get_by_role("button", name=" ").click()
        # except:
        #     try:
        #         Try using a more specific selector
        #         page.locator("button.btn.btn-default.m-t-10").click()
        #     except:
        #         Try using JavaScript as a fallback
        #         page.evaluate("""() => {
        #             const buttons = document.querySelectorAll('button.btn.btn-default.m-t-10');
        #             for (const button of buttons) {
        #                 if (button.querySelector('i.fa.fa-plus')) {
        #                     button.click();
        #                     break;
        #                 }
        #             }
        #         }""")

        # Wait a bit after clicking
        # page.wait_for_timeout(1000)

        page.locator("button:has(i.fa-plus)").nth(1).click()  # Click first button

        # Fill the tracking URL
        page.wait_for_selector("input[placeholder='https://...']")  # Ensure element is loaded
        page.locator("input[placeholder='https://...']").nth(0).fill(sheet_data[target_row][28])


        # Playwright selector targeting external platform UI - keep as-is
        page.get_by_role("button", name="Add New Ad Unit").click()
        # Playwright selector targeting external platform UI - keep as-is
        page.get_by_role("button", name="Confirm").click()

        log_message(f"Successfully processed row {row_number}")
        return True
    except Exception as e:
        log_message(f"Error processing row {row_number}: {str(e)}")
        return False

                # Keep browser open
    # print("Automation completed. You can now interact with the browser. Press Ctrl+C to close the script.")
    # while True:
    #     pass

    finally:
        if 'context' in locals():
            context.close()
        if 'browser' in locals():
            browser.close()

# Main program
worksheet, sheet_data = get_sheet_data(sheet_url, range_name, worksheet_index)

with sync_playwright() as playwright:
    while row_number <= len(sheet_data):
        try:
            if check_a_column(worksheet, row_number):
                log_message(f"Row {row_number} already processed, skipping")
            elif check_g_column(sheet_data, row_number):
                log_message(f"Row {row_number} skipped as adtype is 'rich_media'")
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

log_message("All rows processing complete")
