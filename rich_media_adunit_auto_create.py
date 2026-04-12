import os
import time
import random  # Added random module
import json  # Added json module
from playwright.sync_api import Page, Playwright
import logging
import config # Added config import
import re

# Configure logging
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
    """Log message to logger"""
    logger.info(message)

def slow_down(page: Page, min_delay: float = 0.3, max_delay: float = 0.8):
    """Random delay to simulate human operation
    Reduced delay time to lower timeout risk, but still maintain certain interval
    """
    delay = min_delay + (max_delay - min_delay) * random.random()
    time.sleep(delay)

def extract_last_36_chars_from_url(page: Page) -> str:
    """Extract last 36 characters from current page URL"""
    current_url = page.url
    return current_url[-36:]

def run(playwright: Playwright, ad_data: dict, ad_type: str = 'gif') -> bool:
    """
    Execute ad creation flow, support multiple interactive ad types

    Args:
        playwright: Playwright instance
        ad_data: Dictionary containing ad data
        ad_type: Ad type (gif, slide, countdown, etc.)

    Returns:
        bool: Whether operation is successful
    """
    # Force use passed ad_type parameter, ensure it won't be overwritten
    actual_ad_type = ad_type
    # Store ad_type in ad_data for subsequent use
    ad_data['ad_type'] = actual_ad_type

    log_message(f"Start creating {actual_ad_type} type ad - Received data: {str(ad_data)}")

    try:
        log_message("Launching arm64 native Chrome stable browser")
        # Use arm64 native Chrome stable version
        browser = playwright.chromium.launch(
            executable_path="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",  # Specify arm64 native Chrome path
            headless=False,  # Changed to non-headless mode for observation
            slow_mo=250,  # Added slow_mo parameter, each operation delayed by 250 milliseconds
            args=[
                '--disable-dev-shm-usage',  # Disable /dev/shm usage, more stable on some systems
                '--no-sandbox',  # Disable sandbox mode
                '--disable-setuid-sandbox',  # Disable setuid sandbox
                '--disable-gpu',  # Disable GPU acceleration
                '--disable-software-rasterizer',  # Disable software rasterization
                '--disable-background-timer-throttling',  # Prevent background timer throttling
                '--disable-backgrounding-occluded-windows',  # Prevent background window limiting
                '--disable-renderer-backgrounding',  # Prevent renderer backgrounding
                '--disable-features=TranslateUI',  # Disable translation UI
                '--disable-extensions',  # Disable extensions
                '--disable-plugins',    # Disable plugins
            ]
        )
        # Increase timeout and ignore HTTPS errors
        context = browser.new_context(
            ignore_https_errors=True,
            viewport={'width': 1280, 'height': 800}
        )
        log_message("Browser context created successfully")
        page = context.new_page()
        log_message("New page created successfully")

        # Login flow
        log_message("Navigating to login page")
        try:
            # Increase timeout setting to ensure page fully loads
            page.goto("https://account.example.com/login?r=https%3A%2F%2Fadplatform.example.com%2Fme",
                      timeout=60000,  # 60 second timeout
                      wait_until="networkidle")  # Wait for network idle
            log_message("Login page loaded")
        except Exception as nav_error:
            log_message(f"Page navigation error: {str(nav_error)}")
            return False

        # Ensure form elements exist
        try:
            log_message("Waiting for login form to appear")
            page.wait_for_selector('input[placeholder="Email"]', state="visible", timeout=20000)
            log_message("Login form appeared")
        except Exception as wait_error:
            log_message(f"Error waiting for form elements: {str(wait_error)}")
            return False

        # Try filling form
        try:
            log_message("Fill login form")
            # Dynamically get account and password (Prioritize function)
            email = config.get_email()
            password = config.get_password()

            if not email or not password:
                # If function returns nothing, try environment variables
                email = config.EMAIL
                password = config.PASSWORD

            if not email or not password:
                raise Exception("Unable to get platform login info, please verify .env settings or login to demo system")

            # Playwright selector targeting external platform UI - keep as-is
            page.get_by_placeholder("Email").fill(email)
            log_message(f"Email filled: {email}")
            # Playwright selector targeting external platform UI - keep as-is
            page.get_by_placeholder("Password").fill(password)
            log_message("Password filled")

            # Click login button instead of pressing Enter, more stable
            page.get_by_role("button", name="Login").click()
            log_message("Clicked login button")

            # Wait for login to complete
            page.wait_for_load_state("networkidle", timeout=30000)
            log_message("Login complete")
        except Exception as login_error:
            log_message(f"Login error: {str(login_error)}")
            return False

        # Navigate to special format creation page
        page.get_by_role("button", name="user_account").click()
        slow_down(page)
        page.get_by_role("link", name="Example Organization").click()
        slow_down(page)
        log_message(f"Navigate to ad set page, adset_id: {ad_data['adset_id']}")
        page.goto(f"https://adplatform.example.com/advertiser/show/adset?setId={ad_data['adset_id']}")
        log_message("Successfully reached ad set page")

        log_message("Click 'Create Interactive Ad Unit' button")
        # Playwright selector targeting external platform UI - keep as-is
        page.get_by_role("link", name="+  Create Interactive Ad Unit").click()
        log_message("Clicked create button")

        log_message("Waiting for page to load")
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_load_state("networkidle")
        log_message("Page fully loaded")

        # Ad Unit - Advertiser
        log_message("Start filling ad unit information")
        log_message(f"Fill advertiser name: {ad_data['advertiser']}")
        page.locator("input[name=\"advertiserName\"]").fill(ad_data['advertiser'])
        slow_down(page)
        page.locator("input[name=\"title\"]").click()

        # Ad Unit - Main title
        log_message(f"Fill ad main title: {ad_data['main_title']}")
        page.locator("input[name=\"title\"]").fill(ad_data['main_title'])
        slow_down(page)
        # Playwright selector targeting external platform UI - keep as-is
        page.get_by_placeholder("Mobile loading page for Ad").click()

        # Select 1200x628 image
        log_message("Preparing to upload 1200x628 image")
        absolute_image_path_1 = ad_data['image_path_m']
        log_message(f"1200x628 image path: {absolute_image_path_1}")

        if not os.path.exists(absolute_image_path_1):
            log_message(f"Error: 1200x628 image file does not exist: {absolute_image_path_1}")
            return False

        log_message("Image path verified to exist, starting upload")

        page.set_input_files('input[type="file"]', absolute_image_path_1)
        slow_down(page)
        page.wait_for_timeout(2000)

        # Wait for upload button to appear and click
        log_message("Waiting for image upload to complete...")
        try:
            page.get_by_text("Upload selected area").wait_for(state="visible", timeout=60000)
            page.wait_for_timeout(1500)
            page.get_by_text("Upload selected area").click()
            log_message("Successfully clicked upload button")
        except Exception as e:
            log_message(f"Warning: Upload button click failed: {str(e)}")
            try:
                # Playwright selector targeting external platform UI - keep as-is
                page.get_by_role("button", name="Upload Selected Area").click()
                log_message("Use alternative method to click upload button")
            except Exception as e2:
                log_message(f"Warning: Unable to click upload button: {str(e2)}")
                return False

        page.wait_for_timeout(3000)
        page.wait_for_load_state('networkidle', timeout=60000)
        slow_down(page)

        # Select 300x300 image
        log_message("Selecting 300x300 image button")
        absolute_image_path_2 = ad_data['image_path_s']
        log_message(f"Setting input file for second image: {absolute_image_path_2}")

        if not os.path.exists(absolute_image_path_2):
            log_message(f"Warning: 300x300 image file does not exist: {absolute_image_path_2}")
            return False

        page.locator('input[type="file"]').nth(1).set_input_files(absolute_image_path_2)
        slow_down(page)
        page.wait_for_timeout(2000)

        # Wait for upload button to appear and click
        log_message("Waiting for 300x300 image upload...")
        try:
            page.get_by_text("Upload selected area").wait_for(state="visible", timeout=60000)
            page.wait_for_timeout(1500)
            page.get_by_text("Upload selected area").click()
            log_message("Successfully clicked 300x300 upload button")
        except Exception as e:
            log_message(f"Warning: 300x300 upload button click failed: {str(e)}")
            try:
                # Playwright selector targeting external platform UI - keep as-is
                page.get_by_role("button", name="Upload Selected Area").click()
                log_message("Use alternative method to click 300x300 upload button")
            except Exception as e2:
                log_message(f"Warning: Unable to click 300x300 upload button: {str(e2)}")
                return False

        page.wait_for_timeout(3000)
        page.wait_for_load_state('networkidle', timeout=60000)
        slow_down(page)

        # URL
        # Playwright selector targeting external platform UI - keep as-is
        page.get_by_placeholder("Mobile loading page for Ad").fill(ad_data['landing_page'])
        slow_down(page)

        # Text description
        log_message("Filling text description...")
        page.locator("input[name=\"text\"]").fill(ad_data['subtitle'])
        log_message("Text description filled")
        slow_down(page)

        # Call to action
        log_message("Set call to action...")
        cta_input = page.locator('input[name="callToAction"]')
        cta_input.fill(ad_data['call_to_action'])
        log_message(f"Filled 「{ad_data['call_to_action']}」")
        slow_down(page)

        # Game kit default background
        # Playwright selector targeting external platform UI - keep as-is
        page.get_by_placeholder("bg_placeholder: background").fill(ad_data['background_url'])
        slow_down(page)
        page.once("dialog", lambda dialog: dialog.dismiss())

        # Popup URL
        LandingPageurl = "https://cdn.example.com/popup/"
        # Playwright selector targeting external platform UI - keep as-is
        page.get_by_placeholder("urlInteractivePopup: url to").fill(LandingPageurl)
        slow_down(page)

        # urlInteractivePopups
        log_message("Filling urlInteractivePopups...")
        page.locator("textarea[name=\"urlInteractivePopups\"]").fill('[]')
        slow_down(page)

        # Popup width and height, set based on ad type
        if ad_data.get('ad_type') == 'native_video':
            log_message("Detected native_video ad type, set popup width and height")
            page.locator("input[name=\"popupWidth\"]").fill("1200")
            slow_down(page)
            page.locator("input[name=\"popupHeight\"]").fill("2050")
            slow_down(page)
        else:
            log_message("Not native_video ad type, do not set popup dimensions")

        # payload_gameWidget
        page.locator("textarea[name=\"payload_gameWidgetJson\"]").fill(ad_data['payload_game_widget'])

        # payload_popupJson
        log_message("Filling payload_popupJson...")
        page.locator("textarea[name=\"payload_popupJson\"]").fill(ad_data.get('payload_popupJson') or '[]')


        slow_down(page)
        page.wait_for_timeout(2000)

        log_message("Click Add button")
        page.get_by_text("Add New").click()
        log_message("Clicked Add button")
        slow_down(page)

        log_message("Waiting for confirmation dialog")
        # Playwright selector targeting external platform UI - keep as-is
        page.get_by_role("button", name="OK").wait_for(state="visible")
        page.wait_for_timeout(2000)
        log_message("Click 「OK」button to confirm")
        page.get_by_role("button", name="OK").click()
        log_message("Clicked 「OK」button")
        slow_down(page)

        log_message("Waiting for interactive ad edit link")
        page.wait_for_timeout(2000)
        # Playwright selector targeting external platform UI - keep as-is
        page.get_by_role("link", name="  Interactive Ad Editor").wait_for(state="visible", timeout=60000)
        log_message("Click interactive ad edit link")
        page.get_by_role("link", name="  Interactive Ad Editor").click()
        log_message("Clicked interactive ad edit link")
        slow_down(page)

        log_message("Waiting for page to load")
        page.wait_for_load_state('networkidle')
        slow_down(page)

        log_message("Extract ID from URL")
        last_36_chars = extract_last_36_chars_from_url(page)
        log_message(f"Extracted ID: {last_36_chars}")

        # Get and update popup URL
        log_message("Update popup URL")
        target_placeholder = page.get_by_placeholder("urlInteractivePopup: url to")
        current_value = target_placeholder.input_value()
        new_value = current_value + last_36_chars
        log_message(f"Updated URL: {new_value}")
        target_placeholder.fill(new_value)
        log_message("Filled updated URL")
        slow_down(page)

        # Update urlInteractivePopups
        log_message("Update urlInteractivePopups")
        try:
            # These ad types do not need to fill urlInteractivePopups, because their interaction logic is in payload_game_widget
            skip_popup_ad_types = ['slide', 'vertical_slide', 'vertical_cube_slide', 'vote', 'countdown']
            if ad_data.get('ad_type') in skip_popup_ad_types:
                log_message(f"Detected {ad_data.get('ad_type')} ad type, do not need to update urlInteractivePopups")
            else:
                url_interactive_popups_textarea = page.locator("textarea[name=\"urlInteractivePopups\"]")

                # Determine urlInteractivePopups format based on ad type
                if ad_data.get('ad_type') == 'treasure_box':
                    log_message("Detected treasure_box ad type, use special urlInteractivePopups format")
                    # Treasure box ad uses a, b, c three keys, each with corresponding query parameter
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
                    # Other ad types use original format
                    log_message("Use standard urlInteractivePopups format")
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
                log_message(f"Updated urlInteractivePopups: {updated_popups_json}")

                url_interactive_popups_textarea.fill(updated_popups_json)
                log_message("Filled updated urlInteractivePopups")
                slow_down(page)

        except Exception as e:
            log_message(f"Error updating urlInteractivePopups: {str(e)}")
            # Check if should return False or continue

        log_message("Waiting for 「Modify」button to appear")
        # Playwright selector targeting external platform UI - keep as-is
        page.get_by_role("button", name="Edit").wait_for(state="visible", timeout=60000)
        log_message("Click 「Modify」button")
        page.get_by_role("button", name="Edit").click()
        log_message("Clicked 「Modify」button")
        slow_down(page)

        log_message("Waiting for page to load")
        page.wait_for_load_state('networkidle')

        # Use ad_type parameter from function to specify, this is accurate
        log_message(f"Successfully created {ad_type} ad, display name: {ad_data.get('display_name', 'untitled')}")
        return True

    except Exception as e:
        log_message(f"Error creating {ad_type} ad: {str(e)}")
        # Log stack trace for more info
        import traceback
        log_message(f"Error details: \n{traceback.format_exc()}")
        return False
    finally:
        log_message("Execution complete, preparing to close resources")
        try:
            # Close page first
            if 'page' in locals() and page:
                try:
                    log_message("Close page")
                    page.close(run_before_unload=False)
                    log_message("Page closed successfully")
                except Exception as page_close_error:
                    log_message(f"Error closing page (ignored): {str(page_close_error)}")

            # Then close context
            if 'context' in locals() and context:
                try:
                    log_message("Close browser context")
                    context.close()
                    log_message("Browser context closed successfully")
                except Exception as context_close_error:
                    log_message(f"Error closing context (ignored): {str(context_close_error)}")

            # Finally close browser
            if 'browser' in locals() and browser:
                try:
                    log_message("Close browser")
                    browser.close()
                    log_message("Browser closed successfully")
                except Exception as browser_close_error:
                    log_message(f"Error closing browser (ignored): {str(browser_close_error)}")

            log_message("All resources closed")
        except Exception as final_error:
            log_message(f"Error during final resource cleanup (ignored): {str(final_error)}")
