# Full version with validation - tested and verified 2024/11/27

import re
import platform,sys,subprocess,shlex,os
from playwright.sync_api import Playwright, sync_playwright
import logging
import config

        # Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def log_message(message):
    logging.info(message)



def run(playwright: Playwright, ad_data: dict) -> bool:
    # target_row = row_number - 1  # Index starts at 0 - Removed
    browser = None
    context = None
    try:
        log_message(f"Processing ad: {ad_data.get('display_name', 'N/A')}")
        log_message("Launching arm64 native Chrome stable browser")
        browser = playwright.chromium.launch(
            executable_path="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",  # Specify arm64 native Chrome path
            headless=False,           # Run in headless mode
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

        # Wait for page to fully load
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_load_state("networkidle")

        # Playwright selector targeting external platform UI - keep as-is
        page.get_by_placeholder("Email").click()
        # Dynamically retrieve credentials (prioritize function)
        email = config.get_email()
        password = config.get_password()

        if not email or not password:
            # If function returns nothing, try environment variables
            email = config.EMAIL
            password = config.PASSWORD

        if not email or not password:
            raise Exception("Unable to retrieve platform login credentials. Verify .env settings or demo system login.")

        # Playwright selector targeting external platform UI - keep as-is
        page.get_by_placeholder("Email").fill(email)
        page.get_by_placeholder("Email").press("Tab")
        # Playwright selector targeting external platform UI - keep as-is
        page.get_by_placeholder("Password").fill(password)
        page.get_by_placeholder("Password").press("Enter")

        # Wait for login to complete
        page.wait_for_load_state("networkidle")

        page.get_by_role("button", name="user_account").click()
        page.get_by_role("link", name="Example Organization").click()
        # page.goto("https://adplatform.example.com/advertiser/show/adset?setId=EXAMPLE_ADSET_ID")
        page.goto(f"https://adplatform.example.com/advertiser/show/adset?setId={ad_data['adset_id']}")

        # Playwright selector targeting external platform UI - keep as-is
        page.get_by_role("link", name="+  Create Ad Unit").click()

        page.wait_for_load_state("domcontentloaded")
        page.wait_for_load_state("networkidle")

        # Ad Unit - Display name
        # Playwright selector targeting external platform UI - keep as-is
        page.get_by_role("textbox", name="Display Name").click()
        page.get_by_role("textbox", name="Display Name").fill(ad_data['display_name']) # Column AD / Display name

        # Ad Unit - Advertiser
        # Playwright selector targeting external platform UI - keep as-is
        page.get_by_role("textbox", name="Advertiser").click()
        page.get_by_role("textbox", name="Advertiser").fill(ad_data['advertiser']) # Column I / Advertiser

        # Ad Unit - Main title
        # Playwright selector targeting external platform UI - keep as-is
        page.get_by_role("textbox", name="Main Title").click()
        page.get_by_role("textbox", name="Main Title").fill(ad_data['main_title']) # Column J / Main title

        # Ad Unit - Subtitle
        # Playwright selector targeting external platform UI - keep as-is
        page.get_by_role("textbox", name="Subtitle").click()
        page.get_by_role("textbox", name="Subtitle").fill(ad_data['subtitle']) # Column AA / Subtitle

        # Playwright selector targeting external platform UI - keep as-is
        page.get_by_role("textbox", name="Landing Page URL (HTTPS preferred)").fill(ad_data['landing_page']) # Landing Page
        page.get_by_role("textbox", name="Landing Page URL (HTTPS preferred)").click()
        # Playwright selector targeting external platform UI - keep as-is
        page.get_by_role("textbox", name="Free Input").fill(ad_data.get('call_to_action', 'Learn more')) # call to action, with default


        # Check which images need to be uploaded
        image_uploads = []

        if ad_data.get('image_path_m'):
            image_uploads.append({
                'path': ad_data['image_path_m'],
                'name': '1200x628',
                'selector_text': None,  # First image doesn't need selector
                'description': 'First image (1200x628)'
            })

        if ad_data.get('image_path_p'):
            image_uploads.append({
                'path': ad_data['image_path_p'],
                'name': '300x300',
                'selector_text': '* Square image (300 × 300)',
                'description': 'Square image (300x300)'
            })

        if ad_data.get('image_path_o'):
            image_uploads.append({
                'path': ad_data['image_path_o'],
                'name': '640x100',
                'selector_text': '* Banner640x100 (640 × 100)',
                'description': 'Banner image (640x100)'
            })

        if ad_data.get('image_path_s'):
            image_uploads.append({
                'path': ad_data['image_path_s'],
                'name': '336x280',
                'selector_text': '* Banner336 (336 × 280)',
                'description': 'Banner image (336x280)'
            })

        # Ensure at least one image
        if not image_uploads:
            raise Exception("At least one image must be provided")

        log_message(f"Preparing to upload {len(image_uploads)} images")

        # Add insertable options (based on number of images to upload)
        for _ in range(len(image_uploads)):
            page.get_by_role("button", name="").first.click()
            page.wait_for_timeout(300)  # Wait 300ms to avoid clicking too fast

        # Dynamically handle image uploads
        for i, upload_info in enumerate(image_uploads):
            log_message(f"Setting {upload_info['description']}: {upload_info['path']}")

            # First image doesn't need type selection (already preset)
            if i > 0 and upload_info['selector_text']:
                # Playwright selector targeting external platform UI - keep as-is
                page.get_by_placeholder("Select").nth(i).click()
                page.wait_for_timeout(500)
                page.get_by_text(upload_info['selector_text']).nth(3).click()

            # Upload image file
            page.locator('input[type="file"]').nth(i).set_input_files(upload_info['path'])
            # Playwright selector targeting external platform UI - keep as-is
            page.get_by_role("button", name="Save").click()

            if i < len(image_uploads) - 1:  # Wait if not last image
                page.wait_for_timeout(500)

        # Fill the tracking URL
        # Default select DCM
        if ad_data.get('tracking_url'):
            page.locator("button:has(i.fa-plus)").nth(1).click()  # Click first button
            page.wait_for_selector("input[placeholder='https://...']")  # Ensure element is loaded
            page.locator("input[placeholder='https://...']").nth(0).fill(ad_data['tracking_url'])

        # Playwright selector targeting external platform UI - keep as-is
        page.get_by_role("button", name="Add New Ad Unit").click()
        # Playwright selector targeting external platform UI - keep as-is
        page.get_by_role("button", name="Confirm").click()

        log_message(f"Successfully processed ad: {ad_data.get('display_name', 'N/A')}")
        return True
    except Exception as e:
        log_message(f"Error processing ad {ad_data.get('display_name', 'N/A')}: {str(e)}")
        return False
    finally:
        # Ensure browser and context always close, even on error
        try:
            if context:
                context.close()
            if browser:
                browser.close()
                log_message("Browser closed")
        except Exception as e:
            log_message(f"Error closing browser: {str(e)}")
