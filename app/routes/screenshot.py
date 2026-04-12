from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from playwright.sync_api import sync_playwright, TimeoutError as PwTimeout
import logging
import os
import base64
import subprocess
from datetime import datetime
from urllib.parse import urlparse
import time

from app.models.adunit import get_adunit_by_uuid
from app.services.url_builder import build_screenshot_url, build_native_screenshot_url

logger = logging.getLogger(__name__)

screenshot_bp = Blueprint('screenshot', __name__)

@screenshot_bp.route('/auto-screenshot')
def auto_screenshot():
    """frommoveinterceptmappageface"""
    return render_template('auto_screenshot.html')

@screenshot_bp.route('/native-ad-screenshot')
def native_ad_screenshot():
    """Native AdmanySizeinterceptmappageface"""
    return render_template('native_ad_screenshot.html')

@screenshot_bp.route('/create-native-screenshot', methods=['POST'])
def create_native_screenshot():
    """Native AdmanySizeinterceptmapProcessing"""
    try:
        # Parse JSON request
        data = request.get_json()
        uuid = data.get('uuid', '').strip()
        size = data.get('size', '')
        device = data.get('device', 'iphone_x')
        scroll_distance = int(data.get('scroll_distance', 4800))
        template = data.get('template', 'news-article')
        
        if not uuid or not size:
            return jsonify({'success': False, 'error': 'Missing required parameter'}), 400
        
        # Query AdUnit data from MongoDB
        logger.info(f"Querying UUID: {uuid}")
        adunit_data = get_adunit_by_uuid(uuid)
        
        if not adunit_data:
            return jsonify({'success': False, 'error': f'Unable to find UUID {uuid} corresponding AdUnit data'}), 404
        
        # establishstructureinterceptmapURL
        url = build_native_screenshot_url(adunit_data, size, template)
        if not url:
            return jsonify({'success': False, 'error': 'Unable to build screenshot URL'}), 400
        
        logger.info(f"Built screenshot URL: {url}")
        
        # DeviceSizematchplace
        device_configs = {
            'iphone_x': {'width': 375, 'height': 812, 'name': 'iPhone X'},
            'iphone_se': {'width': 375, 'height': 667, 'name': 'iPhone SE'},
            'iphone_plus': {'width': 414, 'height': 736, 'name': 'iPhone Plus'},
            'android': {'width': 360, 'height': 640, 'name': 'Android Standard'},
            'tablet': {'width': 768, 'height': 1024, 'name': 'Tablet'},
            'desktop': {'width': 1920, 'height': 1080, 'name': 'Desktop'}
        }
        
        device_config = device_configs.get(device, device_configs['iphone_x'])
        
        default_cookie = os.getenv("PLATFORM_COOKIE", "")
        
        logger.info(f"Starting screenshot {size}, Target URL: {url}, Device: {device_config['name']}, UUID: {uuid}")
        
        # makeuse Playwright advancerowinterceptmap
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                executable_path="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                headless=True,
                args=[
                    "--disable-gpu",
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-background-timer-throttling",
                    "--disable-backgrounding-occluded-windows",
                    "--disable-renderer-backgrounding",
                    "--disable-features=TranslateUI",
                    "--disable-extensions",
                    "--disable-plugins",
                    "--disable-web-security",
                ]
            )
            
            # rootaccordingDevicekindtypeharmonynetworkstationsetsetnosameoftopdowntext
            extra_http_headers = {}
            
            # tooutsidedepartmentnetworkstationsetplaceamountoutsideof headers
            if template in ['social-forum', 'news-article']:
                extra_http_headers = {
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'DNT': '1',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                }
            
            if device == 'desktop':
                context = browser.new_context(
                    viewport={'width': device_config['width'], 'height': device_config['height']},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    extra_http_headers=extra_http_headers
                )
            else:
                context = browser.new_context(
                    viewport={'width': device_config['width'], 'height': device_config['height']},
                    user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
                    extra_http_headers=extra_http_headers
                )
            
            page = context.new_page()
            
            # rootaccordingnosamemodeboardharmonySizesetplacenosameof cookies
            parsed_url = urlparse(url)
            domain = parsed_url.netloc
            
            # topredictbrowsepagesetplacespecialuse cookies
            if domain == "preview.example.com":
                try:
                    github_cookie_string = os.getenv("PREVIEW_COOKIE", "")
                    
                    cookies = []
                    cookie_pairs = github_cookie_string.split(';')
                    
                    for pair in cookie_pairs:
                        if '=' in pair:
                            name, value = pair.split('=', 1)
                            name = name.strip()
                            value = value.strip()
                            
                            cookies.append({
                                'name': name,
                                'value': value,
                                'domain': domain,
                                'path': '/',
                                'secure': False,
                                'httpOnly': False
                            })
                    
                    context.add_cookies(cookies)
                    logger.info(f"havetopredictbrowsepagesetplace {len(cookies)} aspecialuse cookies")
                    
                except Exception as cookie_error:
                    logger.warning(f"setplacepredictbrowsepage cookies error occurred（willcontinuecontinuenomakeuse cookie）: {str(cookie_error)}")
            
            # targetinflatplatformeachcloseURLsetplacepredictset cookies
            elif (".example.com" in domain or "adplatform.example.com" == domain):
                try:
                    cookies = []
                    cookie_pairs = default_cookie.split(';')
                    
                    for pair in cookie_pairs:
                        if '=' in pair:
                            name, value = pair.split('=', 1)
                            name = name.strip()
                            value = value.strip()
                            
                            if name.startswith('_Secure-') or 'PSID' in name:
                                cookie_domain = '.google.com'
                            else:
                                cookie_domain = '.example.com' if 'example.com' in domain else domain
                            
                            cookies.append({
                                'name': name,
                                'value': value,
                                'domain': cookie_domain,
                                'path': '/',
                                'secure': name.startswith('_Secure-') or 'PSID' in name,
                                'httpOnly': False
                            })
                    
                    context.add_cookies(cookies)
                    logger.info(f"havetoflatplatformnetworkareasetplace {len(cookies)} a cookies")
                    
                except Exception as cookie_error:
                    logger.warning(f"setplace cookie error occurred（willcontinuecontinuenomakeuse cookie）: {str(cookie_error)}")
            else:
                logger.info(f"outsidedepartmentURL {domain}，jumppass cookie setplace")
            
            try:
                # rootaccordingnosamenetworkstationmakeusenosameofloadenterstrategyomit
                logger.info(f"🌐 openbeginloadenterpageface: {url}")
                logger.info(f"📋 makeusemodeboard: {template}, Size: {size}")
                
                if template == 'social-forum' and size == '300x250':
                    logger.info("🏷️  makeuseSocialForum 300x250specialspecialloadenterstrategyomit")
                    page.goto(url, wait_until='domcontentloaded', timeout=2000)
                    page.wait_for_timeout(1000)

                elif template == 'news-article' and size == '640x200':
                    logger.info("🏷️  makeusePNN 640x200specialspecialloadenterstrategyomit")
                    # simplechangeof 640x200 Processing - moveremovelowerspeedharmonybigamount log
                    page.goto(url, wait_until='commit', timeout=6000)
                    page.wait_for_timeout(3000)
                    
                    # simplesingleWaiting forAdloadenter
                    logger.info("🔍 searchfindPNNAdcontaindevice...")
                    try:
                        page.wait_for_selector('#platform-ad-news-article', timeout=2000)
                        logger.info("✅ FoundPNNAdcontaindevice: #platform-ad-news-article")
                    except:
                        logger.warning("⚠️  notFound#platform-ad-news-article，trytestpassusecontaindevice...")
                        try:
                            page.wait_for_selector('div[data-platform-id]', timeout=1000)
                            logger.info("✅ FoundpassuseAdcontaindevice: div[data-platform-id]")
                        except:
                            logger.warning("⚠️  notFoundassignwhatPNNAdcontaindevice")
                    
                    page.wait_for_timeout(2000)
                    
                else: # flatplatformpagefaceorhishe
                    logger.info("🏷️  makeuselabelstandardloadenterstrategyomit (networkidle)")
                    page.goto(url, wait_until='networkidle', timeout=12000)
                    logger.info("✅ pagefacenetworkidleComplete")
                    page.wait_for_timeout(1000)
                    
                    # detailedfineofAdcontaindevicesearchfind
                    logger.info("🔍 openbeginsearchfindAdcontaindevice...")
                    
                    # firstbeforecheckcheckpagefacefoundationthisresultstructure
                    try:
                        logger.info("📊 checkcheckpagefacefoundationthisresultstructure...")
                        page_title = page.title()
                        logger.info(f"📄 Page title: {page_title}")
                        
                        # checkcheckisnohavemainneedofVueanswerusecontaindevice
                        app_exists = page.locator("#app").count() > 0
                        logger.info(f"🎯 Vueanswerusecontaindevice#appsaveexist: {app_exists}")
                        
                        # checkcheckiframenumberamount
                        iframe_count = page.locator("iframe").count()
                        logger.info(f"🖼️  pagefaceiframenumberamount: {iframe_count}")
                        
                        if iframe_count > 0:
                            for i in range(iframe_count):
                                iframe = page.locator("iframe").nth(i)
                                iframe_src = iframe.get_attribute("src") or "nosrc"
                                iframe_id = iframe.get_attribute("id") or "noid"
                                iframe_name = iframe.get_attribute("name") or "noname"
                                logger.info(f"   🖼️  iframe[{i}]: id='{iframe_id}', name='{iframe_name}', src='{iframe_src[:100]}...'")
                        
                    except Exception as structure_error:
                        logger.warning(f"📊 pagefaceresultstructurecheckcheckFailed: {structure_error}")
                    
                    # searchfindAdcontaindevice
                    ad_container_found = False
                    
                    try:
                        if template == 'news-article':
                            logger.info("🎯 searchfindPNNAdcontaindevice: #platform-ad-news-article")
                            page.wait_for_selector('#platform-ad-news-article', timeout=2000)
                            logger.info("✅ FoundPNNAdcontaindevice")
                            ad_container_found = True
                        else:
                            # trytestnosameofAdcontaindeviceselector
                            selectors_to_try = [
                                'button[class*="_platform_tk_text-sm"]',      # packageincludespecialset class ofbutton
                                'button[style*="width: 100px"]',            # packageincludespecialsetwidedegreeofbutton
                                'button[class*="_platform_tk_bg-black"]',     # packageincludeblackcolorbackviewclassofbutton
                                '#platform-ad-news-article-middle',              # equipmentuse：originalAdcontaindevice
                                'div[data-platform-id]',                        # equipmentuse：passuseplatformcontaindevice
                                'iframe[src*="/1200x628"]',                 # equipmentuse：1200x628Adiframe
                                'iframe[src*="tkcatrun"]',                  # equipmentuse：catrun iframe
                                'iframe[title="Advertisement"]',             # equipmentuse：Adiframe
                                '[data-platform-ad]'                            # equipmentuse：platformAdbelongsex
                            ]
                            
                            for i, selector in enumerate(selectors_to_try, 1):
                                logger.info(f"🔎 trytestselector {i}/{len(selectors_to_try)}: {selector}")
                                try:
                                    elements = page.locator(selector)
                                    count = elements.count()
                                    logger.info(f"   📊 Found{count}apairmatchoriginelement")
                                    
                                    if count > 0:
                                        logger.info(f"✅ AdcontaindeviceFound! makeuseselector: {selector}")
                                        
                                        # rememberrecordFoundoforiginelementdetailedemotion
                                        for j in range(min(count, 3)):  # mostmanyrememberrecordfront3a
                                            element = elements.nth(j)
                                            try:
                                                element_id = element.get_attribute("id") or "noid"
                                                element_class = element.get_attribute("class") or "noclass"
                                                element_data_platform = element.get_attribute("data-platform-id") or element.get_attribute("data-platform-ad") or "noplatformbelongsex"
                                                logger.info(f"   🎯 originelement[{j}]: id='{element_id}', class='{element_class}', platform='{element_data_platform}'")
                                            except Exception as element_error:
                                                logger.warning(f"   ⚠️  nomethodtakegetoriginelement[{j}]detailedemotion: {element_error}")
                                        
                                        ad_container_found = True
                                        break
                                    else:
                                        logger.info(f"   ❌ nopairmatchoriginelement")
                                        
                                except Exception as selector_error:
                                    logger.warning(f"   ⚠️  selectorerrorerror: {selector_error}")
                    
                    except Exception as ad_search_error:
                        logger.warning(f"🔍 Adcontaindevicesearchfindpassprogramsendlifeerrorerror: {ad_search_error}")
                    
                    if not ad_container_found:
                        logger.warning(f"⚠️  pageface ({template}): notFoundassignwhatAdcontaindevice，continuecontinueadvancerowinterceptmap")
                        
                        # amountoutsidecheckcheck：arrangecomepagefacetopplacehavecancaneachcloseoforiginelement
                        try:
                            logger.info("🔍 advancerowwholepagefaceoriginelementsweepdescribe...")
                            
                            # checkcheckplacehavehaveidoforiginelement
                            elements_with_id = page.locator("[id]")
                            id_count = elements_with_id.count()
                            logger.info(f"📊 pagefacehave{id_count}abringidoforiginelement")
                            
                            # checkcheckpackageincludeplatformoforiginelement
                            platform_elements = page.locator("[id*='platform'], [class*='platform'], [data*='platform']")
                            platform_count = platform_elements.count()
                            logger.info(f"🎯 pagefacehave{platform_count}apackageinclude'platform'oforiginelement")
                            
                            if platform_count > 0:
                                for i in range(min(platform_count, 5)):  # mostmanyarrangecomefront5a
                                    element = platform_elements.nth(i)
                                    tag_name = element.evaluate("el => el.tagName")
                                    element_id = element.get_attribute("id") or ""
                                    element_class = element.get_attribute("class") or ""
                                    logger.info(f"   🎯 platformoriginelement[{i}]: <{tag_name}> id='{element_id}' class='{element_class}'")
                            
                        except Exception as scan_error:
                            logger.warning(f"🔍 wholepagefacesweepdescribeFailed: {scan_error}")
                    else:
                        logger.info("✅ AdcontaindevicesearchfindComplete")
                
                logger.info("🌐 pagefaceloadenterstrategyomitholdrowComplete")
                
            except Exception as page_error:
                logger.warning(f"pagefaceloadenterpassprograminsendlifewarningtell: {str(page_error)}")
                
                if "Target page, context or browser has been closed" in str(page_error) or "TargetClosedError" in str(page_error):
                    try:
                        if hasattr(page, 'is_closed') and not page.is_closed():
                            page.close()
                    except:
                        pass
                    
                    try:
                        browser.close()
                    except:
                        pass
                    
                    return jsonify({
                        'success': False, 
                        'error': f'pagefaceexistloadenterpassprograminbycloseclose ({template} {size})',
                        'detail': 'pagefaceloadentertimecloseclose'
                    }), 500
                else:
                    try:
                        page.goto(url, wait_until='load', timeout=1000)
                    except Exception as retry_error:
                        logger.error(f"weightnewloadenteralsoFailed: {str(retry_error)}，continuecontinueadvancerowinterceptmap")
            
            # iffruitsetsetfinishrollmovedistancedistance，ruledirectiondownrollmovearriveAdregionarea
            if scroll_distance > 0:
                logger.info(f"🎲 openbeginrollmoveflowprogram，distancedistance: {scroll_distance}px")

                # specialspecialProcessing 1200x628 Size：rollmovearriveAdoriginelementandplacein
                if size == '1200x628' and template in ['news-article']:
                    logger.info("🎯 1200x628 → openbeginAdoriginelementplaceinflowprogram")
                    try:
                        # ------ newof 1200x628 Adoriginelementplaceinflowprogram ------
                        
                        # ── 1. Waiting forpagefaceharmonyAdloadenter ──
                        logger.info("📱 stepsudden1: Waiting forpagefaceharmonyAdloadenter...")
                        page.wait_for_timeout(2000)  # giveAdchangemanyloadentertimeroom
                        logger.info("✅ stepsudden1Complete: Waiting fortimeroomresultbundle")
                        
                        # ── 2. searchfindeyelabeloriginelement ──
                        logger.info("🔍 stepsudden2: searchfind「watchseechangemany」buttonoriginelement...")
                        ad_container_found = False
                        ad_selector = None
                        
                        # trytestnosameofAdcontaindeviceselector
                        selectors_to_try = [
                            'button[class*="_platform_tk_text-sm"]',      # packageincludespecialset class ofbutton
                            'button[style*="width: 100px"]',            # packageincludespecialsetwidedegreeofbutton
                            'button[class*="_platform_tk_bg-black"]',     # packageincludeblackcolorbackviewclassofbutton
                            '#platform-ad-news-article-middle',              # equipmentuse：originalAdcontaindevice
                            'div[data-platform-id]',                        # equipmentuse：passuseplatformcontaindevice
                            'iframe[src*="/1200x628"]',                 # equipmentuse：1200x628Adiframe
                            'iframe[src*="tkcatrun"]',                  # equipmentuse：catrun iframe
                            'iframe[title="Advertisement"]',             # equipmentuse：Adiframe
                            '[data-platform-ad]'                            # equipmentuse：platformAdbelongsex
                        ]
                        
                        for selector in selectors_to_try:
                            elements = page.locator(selector)
                            if elements.count() > 0 and elements.first.is_visible():
                                ad_selector = selector
                                logger.info(f"✅ weighttest-stepsudden2Complete: Foundeyelabeloriginelement '{selector}'")
                                break
                        
                        if ad_selector:
                            # holdrowplaceinrollmove
                            logger.info("📐 stepsudden3: holdrowplaceinrollmove...")
                            scroll_result = page.evaluate(
                                """
                                (sel) => {
                                    const el = document.querySelector(sel);
                                    if (!el) return { success: false };
                                    
                                    const rect = el.getBoundingClientRect();
                                    const viewportHeight = window.innerHeight;
                                    const currentScrollY = window.pageYOffset;
                                    const elementTop = rect.top + currentScrollY;
                                    const elementHeight = rect.height;
                                    const viewportMiddle = viewportHeight / 2;
                                    const targetScrollY = elementTop - viewportMiddle + (elementHeight / 2);
                                    
                                    window.scrollTo({ top: Math.max(0, targetScrollY), behavior: 'instant' });
                                    return { success: true };
                                }
                                """,
                                ad_selector
                            )
                            
                            if scroll_result['success']:
                                logger.info("✅ stepsudden3Complete: placeinrollmovesuccess")
                                page.wait_for_timeout(1500)
                                logger.info("✅ 1200x628 AdoriginelementplaceinComplete!")
                            else:
                                logger.warning("⚠️  weighttest-placeinrollmoveFailed，makeusefallback")
                                page.mouse.wheel(0, scroll_distance)
                        else:
                            logger.warning("⚠️  weighttest-notFoundAdcontaindevice，makeusefallbackrollmove")
                            page.mouse.wheel(0, scroll_distance)
                            
                    except Exception as e:
                        logger.warning(f"❌ 1200x628 placeinflowprogramFailed: {e} → makeusefallbackrollmove")
                        page.mouse.wheel(0, scroll_distance)
                
                # specialspecialProcessing 300x250 Size：rollmovearriveAdoriginelementandplacein
                elif size == '300x250':
                    logger.info("🎯 300x250 → openbeginAdoriginelementplaceinflowprogram")
                    try:
                        # ------ newof 300x250 Adoriginelementplaceinflowprogram ------
                        
                        # ── 1. Waiting forpagefaceharmonyAdloadenter ──
                        logger.info("📱 stepsudden1: Waiting forpagefaceharmonyAdloadenter...")
                        page.wait_for_timeout(2000)  # giveAdchangemanyloadentertimeroom
                        logger.info("✅ stepsudden1Complete: Waiting fortimeroomresultbundle")
                        
                        # ── 2. searchfindeyelabeloriginelement ──
                        logger.info("🔍 stepsudden2: searchfind300x250Adcontaindeviceoriginelement...")
                        ad_container_found = False
                        ad_selector = None
                        
                        # trytestnosameof300x250Adcontaindeviceselector
                        selectors_to_try = [
                            'iframe[src*="tkcatrun"]:nth-of-type(2)',                # 🎯 mostsuperiorbefore：Rowtwoatkcatrun iframe
                            'button[class*="_platform_tk_text-sm"][class*="_platform_tk_text-white"][class*="_platform_tk_bg-black"]',  # perfectwholebuttonclassgroupmatch
                            'button[style*="width: 100px"][style*="height: 30px"]', # packageincludespecialsetSizeofbutton
                            'div._platform_tk_w-full div._platform_tk_w-full button',    # embedsetresultstructureinofbutton
                            'div[class*="_platform_tk_w-full"] button[class*="_platform_tk_bg-black"]',  # fathercontaindevice+buttongroupmatch
                            'div[style*="background-image"]',                        # packageincludebackviewmappieceofdiv
                            'div[class*="_platform_tk_bg-center"][class*="_platform_tk_bg-cover"]',  # backviewmappiececontaindeviceofspecialsetclass
                            'div[style*="padding-top: 83.3333%"]',                  # specialsetpaddingcompareexampleofcontaindevice
                            'button[class*="_platform_tk_rounded-md"]',                # roundcornerbutton
                            '#platform-ad-news-article-middle',                          # equipmentuse：originalAdcontaindevice
                            'div[data-platform-id]',                                     # equipmentuse：passuseplatformcontaindevice
                            'iframe[src*="/300x250"]',                               # equipmentuse：300x250Adiframe
                            'iframe[src*="tkcatrun"]',                               # equipmentuse：assignmeaningcatrun iframe
                            'iframe[title="Advertisement"]',                         # equipmentuse：Adiframe
                            '[data-platform-ad]'                                         # equipmentuse：platformAdbelongsex
                        ]
                        
                        for selector in selectors_to_try:
                            # specialspecialProcessingRowtwoaiframeofemotionsituation
                            if selector == 'iframe[src*="tkcatrun"]:nth-of-type(2)':
                                elements = page.locator('iframe[src*="tkcatrun"]')
                                element_count = elements.count()
                                logger.info(f"🔍 Found{element_count}atkcatrun iframe")
                                
                                if element_count >= 2:
                                    # checkcheckRowtwoaiframeisnocansee
                                    second_iframe = elements.nth(1)  # searchguide1 = Rowtwoa
                                    if second_iframe.is_visible():
                                        ad_selector = selector
                                        logger.info(f"✅ stepsudden2Complete: FoundRowtwoatkcatrun iframe")
                                        break
                                    else:
                                        logger.info(f"⚠️  Rowtwoatkcatrun iframenocansee，trytestdownaachoosechoosedevice")
                                else:
                                    logger.info(f"⚠️  tkcatrun iframenumberamountnoenough({element_count}a)，trytestdownaachoosechoosedevice")
                            else:
                                # ageneralofchoosechoosedeviceProcessing
                                elements = page.locator(selector)
                                if elements.count() > 0 and elements.first.is_visible():
                                    ad_selector = selector
                                    logger.info(f"✅ stepsudden2Complete: Foundeyelabeloriginelement '{selector}'")
                                    break
                        
                        if ad_selector:
                            # holdrowplaceinrollmove
                            logger.info("📐 stepsudden3: holdrowplaceinrollmove...")
                            
                            # specialspecialProcessingRowtwoaiframeofrollmove
                            if ad_selector == 'iframe[src*="tkcatrun"]:nth-of-type(2)':
                                scroll_result = page.evaluate(
                                    """
                                    () => {
                                        const iframes = document.querySelectorAll('iframe[src*="tkcatrun"]');
                                        if (iframes.length < 2) return { success: false };
                                        
                                        const el = iframes[1]; // Rowtwoaiframe
                                        const rect = el.getBoundingClientRect();
                                        const viewportHeight = window.innerHeight;
                                        const currentScrollY = window.pageYOffset;
                                        const elementTop = rect.top + currentScrollY;
                                        const elementHeight = rect.height;
                                        const viewportMiddle = viewportHeight / 2;
                                        const targetScrollY = elementTop - viewportMiddle + (elementHeight / 2);
                                        
                                        window.scrollTo({ top: Math.max(0, targetScrollY), behavior: 'instant' });
                                        return { success: true };
                                    }
                                    """
                                )
                            else:
                                # ageneraloriginelementofrollmove
                                scroll_result = page.evaluate(
                                    """
                                    (sel) => {
                                        const el = document.querySelector(sel);
                                        if (!el) return { success: false };
                                        
                                        const rect = el.getBoundingClientRect();
                                        const viewportHeight = window.innerHeight;
                                        const currentScrollY = window.pageYOffset;
                                        const elementTop = rect.top + currentScrollY;
                                        const elementHeight = rect.height;
                                        const viewportMiddle = viewportHeight / 2;
                                        const targetScrollY = elementTop - viewportMiddle + (elementHeight / 2);
                                        
                                        window.scrollTo({ top: Math.max(0, targetScrollY), behavior: 'instant' });
                                        return { success: true };
                                    }
                                    """,
                                    ad_selector if ad_selector != 'iframe[src*="tkcatrun"]:nth-of-type(2)' else 'iframe[src*="tkcatrun"]'
                                )
                            
                            if scroll_result['success']:
                                logger.info("✅ stepsudden3Complete: placeinrollmovesuccess")
                                page.wait_for_timeout(1500)
                                logger.info("✅ 300×250 AdoriginelementplaceinComplete!")
                            else:
                                logger.warning("⚠️  placeinrollmoveFailed，makeusefallback")
                                page.mouse.wheel(0, scroll_distance)
                        else:
                            logger.warning("⚠️  notFound300x250Adcontaindevice，makeusefallbackrollmove")
                            page.mouse.wheel(0, scroll_distance)
                            
                    except Exception as e:
                        logger.warning(f"❌ 300×250 placeinflowprogramFailed: {e} → makeusefallbackrollmove")
                        page.mouse.wheel(0, scroll_distance)

                elif template in ['news-article', 'news-article-list']:
                    # PTTpredictbrowsepageface，trytestexistiframeinsiderollmove
                    logger.info("🏷️  PTTmodeboard - trytestiframeinsiderollmove")
                    try:
                        # firstbeforecheckcheckiframeisnosaveexist
                        logger.info("🔍 checkcheckptt-viewer iframeisnosaveexist...")
                        ptt_iframe_count = page.locator('iframe#ptt-viewer').count()
                        logger.info(f"📊 Found{ptt_iframe_count}aptt-viewer iframe")
                        
                        if ptt_iframe_count > 0:
                            # takegetiframeofrealborderFrameobjectitem
                            logger.info("📦 takegetiframe Frameobjectitem...")
                            iframe_element = page.locator('iframe#ptt-viewer').first
                            frame = iframe_element.content_frame()
                            
                            if frame:
                                logger.info("✅ successtakegetiframe Frameobjectitem")
                                logger.info(f"🎲 existiframeinsideholdrowrollmove: {scroll_distance}px")
                                frame.evaluate(f"window.scrollTo(0, {scroll_distance})")
                                logger.info("✅ iframeinsiderollmovesuccess")
                            else:
                                logger.warning("⚠️  nomethodtakegetiframe Frameobjectitem，makeusefallbackrollmove")
                                page.mouse.wheel(0, scroll_distance)
                        else:
                            logger.warning("⚠️  notFoundptt-viewer iframe，makeusefallbackrollmove")
                            page.mouse.wheel(0, scroll_distance)
                            
                    except Exception as e:
                        logger.warning(f"❌ PTT iframerollmoveFailed: {e}")
                        logger.info("🔄 makeusefallbackrollmovesquarecase...")
                        page.mouse.wheel(0, scroll_distance)

                elif template == 'social-forum':
                    # useslidemouserollround，SocialForum nowillholditrestoreoriginal，and lazy-load stillcantouchsend
                    logger.info("🏷️  SocialForummodeboard - makeuseslidemouserollroundrollmove")
                    page.mouse.wheel(0, scroll_distance)
                    logger.info("✅ SocialForumslidemouserollroundrollmoveComplete")

                else:
                    # hishenetworkstationprotectholdoriginalcomeofdomethod
                    logger.info("🏷️  labelstandardmodeboard - makeusewindow.scrollTorollmove")
                    page.evaluate(f"window.scrollTo(0, {scroll_distance})")
                    logger.info("✅ labelstandardrollmoveComplete")

                # Waiting forrollmoveComplete（1200x628 harmony 300x250 removeoutside，reasontohavethroughhavefromselfofWaiting formachinecontrol）
                if not (size == '1200x628' and template in ['news-article']) and size != '300x250':
                    logger.info("⏳ Waiting forrollmoveComplete...")
                    page.wait_for_timeout(1000)
                    logger.info("✅ rollmoveflowprogramComplete")
            else:
                logger.info("🚫 notsetsetrollmovedistancedistance，jumppassrollmove")
            
            # Createinterceptmapeyerecord
            screenshot_dir = os.path.join('uploads', 'screenshots', uuid)
            if not os.path.exists(screenshot_dir):
                os.makedirs(screenshot_dir)
            
            # lifebecomefilecasename
            timestamp = datetime.now().strftime('%H%M%S')
            device_suffix = device.replace('_', '-')
            
            # specialspecialProcessing 1200x628 harmony 300x250 offilecasename
            if size == '1200x628' and template in ['news-article']:
                scroll_suffix = 'element-scroll'
            elif size == '300x250':
                scroll_suffix = 'element-scroll'
            else:
                scroll_suffix = f'scroll-{scroll_distance}px' if scroll_distance > 0 else 'no-scroll'
            
            template_suffix = f'_{template}' if template not in ['news-article'] else ''
            filename = f'native_{size.replace("x", "_")}_device-{device_suffix}_uuid-{uuid}_{scroll_suffix}{template_suffix}_{timestamp}.png'
            screenshot_path = os.path.join(screenshot_dir, filename)
            
            # holdrowinterceptmap
            try:
                page.wait_for_timeout(4000)
                page.screenshot(path=screenshot_path, full_page=False)
                logger.info("interceptmapoperateworkComplete")
                screenshot_success = True
                
            except Exception as screenshot_error:
                logger.error(f"interceptmappassprograminsendlifeerrorerror: {str(screenshot_error)}")
                
                if "Target page, context or browser has been closed" in str(screenshot_error) or "TargetClosedError" in str(screenshot_error):
                    try:
                        if hasattr(page, 'is_closed') and not page.is_closed():
                            page.close()
                    except:
                        pass
                    
                    try:
                        browser.close()
                    except:
                        pass
                    
                    return jsonify({
                        'success': False, 
                        'error': f'interceptmaptimepagefacehavecloseclose ({template} {size})',
                        'detail': 'pagefacehavecloseclose，nomethodinterceptmap'
                    }), 500
                
                # weighttestatime
                try:
                    try:
                        page.close()
                    except:
                        pass
                    
                    page = context.new_page()
                    page.goto(url, wait_until='domcontentloaded', timeout=15000)
                    page.wait_for_timeout(3000)
                    
                    # weighttesttimealsoneedrollmove
                    if scroll_distance > 0:
                        logger.info(f"🔄 weighttesttimeopenbeginrollmoveflowprogram，distancedistance: {scroll_distance}px")

                        # specialspecialProcessing 1200x628 Size：rollmovearriveAdoriginelementandplacein
                        if size == '1200x628' and template in ['news-article']:
                            logger.info("🎯 weighttest-1200x628 → openbeginAdoriginelementplaceinflowprogram")
                            try:
                                # Waiting forpagefaceharmonyAdloadenter
                                logger.info("📱 weighttest-stepsudden1: Waiting forpagefaceharmonyAdloadenter...")
                                page.wait_for_timeout(2000)
                                logger.info("✅ weighttest-stepsudden1Complete: Waiting fortimeroomresultbundle")
                                
                                # searchfindeyelabeloriginelement
                                logger.info("🔍 weighttest-stepsudden2: searchfind「watchseechangemany」buttonoriginelement...")
                                # trytestnosameofAdcontaindeviceselector
                                selectors_to_try = [
                                    'button:has-text("watchseechangemany")',               # mostessencestandard：packageinclude"watchseechangemany"texttextofbutton
                                    'button[class*="_platform_tk_text-sm"]',      # packageincludespecialset class ofbutton
                                    'button[style*="width: 100px"]',            # packageincludespecialsetwidedegreeofbutton
                                    'button[class*="_platform_tk_bg-black"]',     # packageincludeblackcolorbackviewclassofbutton
                                    '#platform-ad-news-article-middle',              # equipmentuse：originalAdcontaindevice
                                    'div[data-platform-id]',                        # equipmentuse：passuseplatformcontaindevice
                                    'iframe[src*="/1200x628"]',                 # equipmentuse：1200x628Adiframe
                                    'iframe[src*="tkcatrun"]',                  # equipmentuse：catrun iframe
                                    'iframe[title="Advertisement"]',             # equipmentuse：Adiframe
                                    '[data-platform-ad]'                            # equipmentuse：platformAdbelongsex
                                ]
                                
                                ad_selector = None
                                for selector in selectors_to_try:
                                    elements = page.locator(selector)
                                    if elements.count() > 0 and elements.first.is_visible():
                                        ad_selector = selector
                                        logger.info(f"✅ weighttest-stepsudden2Complete: Foundeyelabeloriginelement '{selector}'")
                                        break
                                
                                if ad_selector:
                                    # holdrowplaceinrollmove
                                    logger.info("📐 weighttest-stepsudden3: holdrowplaceinrollmove...")
                                    scroll_result = page.evaluate(
                                        """
                                        (sel) => {
                                            const el = document.querySelector(sel);
                                            if (!el) return { success: false };
                                            
                                            const rect = el.getBoundingClientRect();
                                            const viewportHeight = window.innerHeight;
                                            const currentScrollY = window.pageYOffset;
                                            const elementTop = rect.top + currentScrollY;
                                            const elementHeight = rect.height;
                                            const viewportMiddle = viewportHeight / 2;
                                            const targetScrollY = elementTop - viewportMiddle + (elementHeight / 2);
                                            
                                            window.scrollTo({ top: Math.max(0, targetScrollY), behavior: 'instant' });
                                            return { success: true };
                                        }
                                        """,
                                        ad_selector
                                    )
                                    
                                    if scroll_result['success']:
                                        logger.info("✅ weighttest-stepsudden3Complete: placeinrollmovesuccess")
                                        page.wait_for_timeout(1500)
                                        logger.info("✅ weighttest-1200x628 AdoriginelementplaceinComplete!")
                                    else:
                                        logger.warning("⚠️  weighttest-placeinrollmoveFailed，makeusefallback")
                                        page.mouse.wheel(0, scroll_distance)
                                else:
                                    logger.warning("⚠️  weighttest-notFoundAdcontaindevice，makeusefallbackrollmove")
                                    page.mouse.wheel(0, scroll_distance)
                                    
                            except Exception as e:
                                logger.warning(f"❌ weighttest-1200x628placeinflowprogramFailed: {e} → makeusefallbackrollmove")
                                page.mouse.wheel(0, scroll_distance)

                        # specialspecialProcessing 300x250 Size：rollmovearriveAdoriginelementandplacein
                        elif size == '300x250':
                            logger.info("🎯 weighttest-300x250 → openbeginAdoriginelementplaceinflowprogram")
                            try:
                                # Waiting forpagefaceharmonyAdloadenter
                                logger.info("📱 weighttest-stepsudden1: Waiting forpagefaceharmonyAdloadenter...")
                                page.wait_for_timeout(2000)
                                logger.info("✅ weighttest-stepsudden1Complete: Waiting fortimeroomresultbundle")
                                
                                # searchfindeyelabeloriginelement
                                logger.info("🔍 weighttest-stepsudden2: searchfind300x250Adcontaindeviceoriginelement...")
                                # trytestnosameof300x250Adcontaindeviceselector
                                selectors_to_try = [
                                    'button[class*="_platform_tk_text-sm"][class*="_platform_tk_text-white"][class*="_platform_tk_bg-black"]',  # perfectwholebuttonclassgroupmatch
                                    'button[style*="width: 100px"][style*="height: 30px"]', # packageincludespecialsetSizeofbutton
                                    'div._platform_tk_w-full div._platform_tk_w-full button',    # embedsetresultstructureinofbutton
                                    'div[class*="_platform_tk_w-full"] button[class*="_platform_tk_bg-black"]',  # fathercontaindevice+buttongroupmatch
                                    'div[style*="background-image"]',                        # packageincludebackviewmappieceofdiv
                                    'div[class*="_platform_tk_bg-center"][class*="_platform_tk_bg-cover"]',  # backviewmappiececontaindeviceofspecialsetclass
                                    'div[style*="padding-top: 83.3333%"]',                  # specialsetpaddingcompareexampleofcontaindevice
                                    'button[class*="_platform_tk_rounded-md"]',                # roundcornerbutton
                                    '#platform-ad-news-article-middle',                          # equipmentuse：originalAdcontaindevice
                                    'div[data-platform-id]',                                     # equipmentuse：passuseplatformcontaindevice
                                    'iframe[src*="/300x250"]',                               # equipmentuse：300x250Adiframe
                                    'iframe[src*="tkcatrun"]:nth-of-type(2)',                # 🎯 mostsuperiorbefore：Rowtwoatkcatrun iframe
                                    'iframe[title="Advertisement"]',                         # equipmentuse：Adiframe
                                    '[data-platform-ad]'                                         # equipmentuse：platformAdbelongsex
                                ]
                                
                                ad_selector = None
                                for selector in selectors_to_try:
                                    # specialspecialProcessingRowtwoaiframeofemotionsituation
                                    if selector == 'iframe[src*="tkcatrun"]:nth-of-type(2)':
                                        elements = page.locator('iframe[src*="tkcatrun"]')
                                        element_count = elements.count()
                                        logger.info(f"🔍 Found{element_count}atkcatrun iframe")
                                        
                                        if element_count >= 2:
                                            # checkcheckRowtwoaiframeisnocansee
                                            second_iframe = elements.nth(1)  # searchguide1 = Rowtwoa
                                            if second_iframe.is_visible():
                                                ad_selector = selector
                                                logger.info(f"✅ stepsudden2Complete: FoundRowtwoatkcatrun iframe")
                                                break
                                            else:
                                                logger.info(f"⚠️  Rowtwoatkcatrun iframenocansee，trytestdownaachoosechoosedevice")
                                        else:
                                            logger.info(f"⚠️  tkcatrun iframenumberamountnoenough({element_count}a)，trytestdownaachoosechoosedevice")
                                    else:
                                        # ageneralofchoosechoosedeviceProcessing
                                        elements = page.locator(selector)
                                        if elements.count() > 0 and elements.first.is_visible():
                                            ad_selector = selector
                                            logger.info(f"✅ stepsudden2Complete: Foundeyelabeloriginelement '{selector}'")
                                            break
                                
                                if ad_selector:
                                    # holdrowplaceinrollmove
                                    logger.info("📐 weighttest-stepsudden3: holdrowplaceinrollmove...")
                                    
                                    # specialspecialProcessingRowtwoaiframeofrollmove
                                    if ad_selector == 'iframe[src*="tkcatrun"]:nth-of-type(2)':
                                        scroll_result = page.evaluate(
                                            """
                                            () => {
                                                const iframes = document.querySelectorAll('iframe[src*="tkcatrun"]');
                                                if (iframes.length < 2) return { success: false };
                                                
                                                const el = iframes[1]; // Rowtwoaiframe
                                                const rect = el.getBoundingClientRect();
                                                const viewportHeight = window.innerHeight;
                                                const currentScrollY = window.pageYOffset;
                                                const elementTop = rect.top + currentScrollY;
                                                const elementHeight = rect.height;
                                                const viewportMiddle = viewportHeight / 2;
                                                const targetScrollY = elementTop - viewportMiddle + (elementHeight / 2);
                                                
                                                window.scrollTo({ top: Math.max(0, targetScrollY), behavior: 'instant' });
                                                return { success: true };
                                            }
                                            """
                                        )
                                    else:
                                        # ageneraloriginelementofrollmove
                                        scroll_result = page.evaluate(
                                            """
                                            (sel) => {
                                                const el = document.querySelector(sel);
                                                if (!el) return { success: false };
                                                
                                                const rect = el.getBoundingClientRect();
                                                const viewportHeight = window.innerHeight;
                                                const currentScrollY = window.pageYOffset;
                                                const elementTop = rect.top + currentScrollY;
                                                const elementHeight = rect.height;
                                                const viewportMiddle = viewportHeight / 2;
                                                const targetScrollY = elementTop - viewportMiddle + (elementHeight / 2);
                                                
                                                window.scrollTo({ top: Math.max(0, targetScrollY), behavior: 'instant' });
                                                return { success: true };
                                            }
                                            """,
                                            ad_selector if ad_selector != 'iframe[src*="tkcatrun"]:nth-of-type(2)' else 'iframe[src*="tkcatrun"]'
                                        )
                                    
                                    if scroll_result['success']:
                                        logger.info("✅ weighttest-stepsudden3Complete: placeinrollmovesuccess")
                                        page.wait_for_timeout(1500)
                                        logger.info("✅ weighttest-300×250 AdoriginelementplaceinComplete!")
                                    else:
                                        logger.warning("⚠️  weighttest-placeinrollmoveFailed，makeusefallback")
                                        page.mouse.wheel(0, scroll_distance)
                                else:
                                    logger.warning("⚠️  weighttest-notFound300x250Adcontaindevice，makeusefallbackrollmove")
                                    page.mouse.wheel(0, scroll_distance)
                                    
                            except Exception as e:
                                logger.warning(f"❌ weighttest-300×250placeinflowprogramFailed: {e} → makeusefallbackrollmove")
                                page.mouse.wheel(0, scroll_distance)

                        elif template in ['news-article', 'news-article-list']:
                            # PTTpredictbrowsepageface，trytestexistiframeinsiderollmove
                            logger.info("🏷️  weighttest-PTTmodeboard - trytestiframeinsiderollmove")
                            try:
                                # firstbeforecheckcheckiframeisnosaveexist
                                logger.info("🔍 weighttest-checkcheckptt-viewer iframeisnosaveexist...")
                                ptt_iframe_count = page.locator('iframe#ptt-viewer').count()
                                logger.info(f"📊 weighttest-Found{ptt_iframe_count}aptt-viewer iframe")
                                
                                if ptt_iframe_count > 0:
                                    # takegetiframeofrealborderFrameobjectitem
                                    logger.info("📦 weighttest-takegetiframe Frameobjectitem...")
                                    iframe_element = page.locator('iframe#ptt-viewer').first
                                    frame = iframe_element.content_frame()
                                    
                                    if frame:
                                        logger.info("✅ weighttest-successtakegetiframe Frameobjectitem")
                                        logger.info(f"🎲 weighttest-existiframeinsideholdrowrollmove: {scroll_distance}px")
                                        frame.evaluate(f"window.scrollTo(0, {scroll_distance})")
                                        logger.info("✅ weighttest-iframeinsiderollmovesuccess")
                                    else:
                                        logger.warning("⚠️  weighttest-nomethodtakegetiframe Frameobjectitem，makeusefallbackrollmove")
                                        page.mouse.wheel(0, scroll_distance)
                                else:
                                    logger.warning("⚠️  weighttest-notFoundptt-viewer iframe，makeusefallbackrollmove")
                                    page.mouse.wheel(0, scroll_distance)
                                    
                            except Exception as e:
                                logger.warning(f"❌ weighttest-PTT iframerollmoveFailed: {e}")
                                logger.info("🔄 weighttest-makeusefallbackrollmovesquarecase...")
                                page.mouse.wheel(0, scroll_distance)

                        elif template == 'social-forum':
                            # useslidemouserollround，SocialForum nowillholditrestoreoriginal，and lazy-load stillcantouchsend
                            logger.info("🏷️  weighttest-SocialForummodeboard - makeuseslidemouserollroundrollmove")
                            page.mouse.wheel(0, scroll_distance)
                            logger.info("✅ weighttest-SocialForumslidemouserollroundrollmoveComplete")

                        else:
                            # hishenetworkstationprotectholdoriginalcomeofdomethod
                            logger.info("🏷️  weighttest-labelstandardmodeboard - makeusewindow.scrollTorollmove")
                            page.evaluate(f"window.scrollTo(0, {scroll_distance})")
                            logger.info("✅ weighttest-labelstandardrollmoveComplete")

                        # Waiting forrollmoveComplete（1200x628harmony300x250placeinflowprogramremoveoutside，reasontohavethroughhavefromselfofWaiting for）
                        if not (size == '1200x628' and template in ['news-article']) and size != '300x250':
                            logger.info("⏳ weighttest-Waiting forrollmoveComplete...")
                            page.wait_for_timeout(1000)
                            logger.info("✅ weighttest-rollmoveflowprogramComplete")
                    
                    page.screenshot(path=screenshot_path, full_page=False)
                    logger.info("weightnewinterceptmapsuccess")
                    screenshot_success = True
                except Exception as retry_screenshot_error:
                    logger.error(f"weightnewinterceptmapalsoFailed: {str(retry_screenshot_error)}")
                    raise screenshot_error
            
            # sureprotectbrowsebrowsedeviceresourcesourcebyrightsureclearreason
            try:
                if hasattr(page, 'is_closed') and not page.is_closed():
                    page.close()
            except:
                pass
            
            try:
                browser.close()
            except:
                pass
            
            # takegetfilecaseresourcenews
            absolute_path = os.path.abspath(screenshot_path)
            
            # installwholegaintakefilecasebigsmall
            try:
                file_size = os.path.getsize(absolute_path)
            except:
                file_size = 0
            
            # formatchangefilecasebigsmall
            if file_size > 1024 * 1024:
                file_size_str = f"{file_size / (1024 * 1024):.1f}MB"
            elif file_size > 1024:
                file_size_str = f"{file_size / 1024:.1f}KB"
            else:
                file_size_str = f"{file_size}B"
            
            logger.info(f"interceptmapComplete，filecasestoresaveto: {absolute_path}")
            
            # calculatecounteachtargetroadpathprovidefrontendmakeuse
            relative_path = os.path.relpath(screenshot_path, 'uploads')
            
            return jsonify({
                'success': True,
                'file_path': absolute_path,
                'filename': filename,
                'file_size': file_size_str,
                'device_name': device_config['name'],
                'preview_url': url_for('screenshot.screenshot_base64', filename=relative_path),
                'download_url': url_for('screenshot.screenshot_base64', filename=relative_path)
            })
            
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        logger.error(f"Native Adinterceptmaperror occurred: {str(e)}")
        logger.error(f"Error details：\n{error_detail}")
        return jsonify({'success': False, 'error': str(e)}), 500

@screenshot_bp.route('/screenshot_base64/<path:filename>')
def screenshot_base64(filename):
    """provideprovideinterceptmapfilecaseof base64 editcode"""
    try:
        # installwholecheckcheck：sureprotectfilecaseroadpathexistallowallowofeyerecordinside
        if not filename.startswith('screenshots/'):
            return "Unauthorized", 403
            
        file_path = os.path.join('uploads', filename)
        
        if not os.path.exists(file_path):
            return "File not found", 404
            
        # readtakefilecaseandconvertchangeto base64
        with open(file_path, 'rb') as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
            
        return f"data:image/png;base64,{encoded_string}"
        
    except Exception as e:
        logger.error(f"provideprovideinterceptmapfilecaseerror occurred: {str(e)}")
        return "Internal server error", 500

@screenshot_bp.route('/create-screenshot', methods=['POST'])
def create_screenshot():
    """ProcessinginterceptmapCreate"""
    try:
        uuid = request.form.get('uuid', '').strip()
        device = request.form.get('device', 'iphone_x')
        full_page = request.form.get('full_page') == 'true'
        scroll_distance = int(request.form.get('scroll_distance', 4800))
        wait_time = int(request.form.get('wait_time', 3)) * 1000
        
        if not uuid:
            flash('pleaseinputenterhaveeffectof UUID', 'error')
            return redirect(url_for('screenshot.auto_screenshot'))
        
        # Query AdUnit data from MongoDB
        logger.info(f"Querying UUID: {uuid}")
        adunit_data = get_adunit_by_uuid(uuid)
        
        if not adunit_data:
            flash(f'Unable to find UUID {uuid} corresponding AdUnit data', 'error')
            return redirect(url_for('screenshot.auto_screenshot'))
        
        # establishstructureinterceptmapURL
        url = build_screenshot_url(adunit_data)
        if not url:
            flash('Unable to build screenshot URL', 'error')
            return redirect(url_for('screenshot.auto_screenshot'))
        
        logger.info(f"Built screenshot URL: {url}")
        
        # DeviceSizematchplace
        device_configs = {
            'iphone_x': {'width': 375, 'height': 812, 'name': 'iPhone X'},
            'iphone_se': {'width': 375, 'height': 667, 'name': 'iPhone SE'},
            'iphone_plus': {'width': 414, 'height': 736, 'name': 'iPhone Plus'},
            'android': {'width': 360, 'height': 640, 'name': 'Android Standard'},
            'tablet': {'width': 768, 'height': 1024, 'name': 'Tablet'}
        }
        
        device_config = device_configs.get(device, device_configs['iphone_x'])
        
        default_cookie = os.getenv("PLATFORM_COOKIE", "")
        
        logger.info(f"openbeginfrommoveinterceptmap, Target URL: {url}, Device: {device_config['name']}, perfectwholepageface: {full_page}, UUID: {uuid}")
        
        # makeuse Playwright advancerowinterceptmap
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                executable_path="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                headless=True,
                args=[
                    "--disable-gpu",
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-background-timer-throttling",
                    "--disable-backgrounding-occluded-windows",
                    "--disable-renderer-backgrounding",
                    "--disable-features=TranslateUI",
                    "--disable-extensions",
                    "--disable-plugins",
                    "--disable-web-security",
                ]
            )
            context = browser.new_context(
                viewport={'width': device_config['width'], 'height': device_config['height']},
                user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Mobile/15E148 Safari/604.1' if 'iphone' in device or device == 'android' else 'Mozilla/5.0 (iPad; CPU OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Mobile/15E148 Safari/604.1'
            )
            
            # rootaccordingareanamesetplacenosameof cookie
            try:
                parsed_url = urlparse(url)
                domain = parsed_url.netloc
                
                # topredictbrowsepagesetplacespecialuse cookies
                if domain == "preview.example.com":
                    github_cookie_string = os.getenv("PREVIEW_COOKIE", "")
                    
                    cookies = []
                    cookie_pairs = github_cookie_string.split(';')
                    
                    for pair in cookie_pairs:
                        if '=' in pair:
                            name, value = pair.split('=', 1)
                            name = name.strip()
                            value = value.strip()
                            
                            cookies.append({
                                'name': name,
                                'value': value,
                                'domain': domain,
                                'path': '/',
                                'secure': False,
                                'httpOnly': False
                            })
                    
                    context.add_cookies(cookies)
                    logger.info(f"havetopredictbrowsepagesetplace {len(cookies)} aspecialuse cookies")
                    
                else:
                    cookies = []
                    cookie_pairs = default_cookie.split(';')
                    
                    for pair in cookie_pairs:
                        if '=' in pair:
                            name, value = pair.split('=', 1)
                            name = name.strip()
                            value = value.strip()
                            
                            if name.startswith('_Secure-') or 'PSID' in name:
                                cookie_domain = '.google.com'
                            else:
                                if 'example.com' in domain or 'adplatform' in domain:
                                    cookie_domain = '.example.com' if 'example.com' in domain else domain
                                else:
                                    cookie_domain = domain
                            
                            cookies.append({
                                'name': name,
                                'value': value,
                                'domain': cookie_domain,
                                'path': '/',
                                'secure': name.startswith('_Secure-') or 'PSID' in name,
                                'httpOnly': False
                            })
                    
                    context.add_cookies(cookies)
                    logger.info(f"havesetplace {len(cookies)} a cookies")
                    
            except Exception as cookie_error:
                logger.warning(f"setplace cookie error occurred（willcontinuecontinuenomakeuse cookie）: {str(cookie_error)}")
            
            page = context.new_page()
            
            # visitquestioneyelabelURL，increaseaddexceedtimetimeroomandchangegooderrorerrorProcessing
            try:
                page.goto(url, wait_until='networkidle', timeout=12000)
            except Exception as goto_error:
                logger.warning(f"networkidle Waiting forexceedtime，trytest domcontentloaded: {str(goto_error)}")
                try:
                    page.goto(url, wait_until='domcontentloaded', timeout=8000)
                except Exception as retry_error:
                    logger.warning(f"domcontentloaded alsoexceedtime，trytestfoundationthisloadenter: {str(retry_error)}")
                    page.goto(url, wait_until='commit', timeout=6000)
            
            # Waiting for page to load
            page.wait_for_timeout(wait_time)
            
            # iffruitsetsetfinishrollmovedistancedistance，ruledirectiondownrollmovearriveAdregionarea
            if scroll_distance > 0:
                logger.info(f"directiondownrollmove {scroll_distance}px")

                # rootaccordingURLjudgecutisnotoPTTeachclosepageface
                is_ptt_page = 'ptt' in url.lower() or 'github.io' in url.lower()
                
                if is_ptt_page:
                    # PTTpredictbrowsepageface，trytestexistiframeinsiderollmove
                    try:
                        frame = page.frame_locator('iframe#ptt-viewer').first
                        frame.evaluate(f"window.scrollTo(0, {scroll_distance})")
                        logger.info("existPTT iframeinsiderollmovesuccess")
                    except Exception as e:
                        logger.warning(f"PTT iframe scroll Failed: {e}")
                        page.mouse.wheel(0, scroll_distance)          # afterhelp
                else:
                    # hishenetworkstationprotectholdoriginalcomeofdomethod
                    page.evaluate(f"window.scrollTo(0, {scroll_distance})")

                # Waiting forrollmoveComplete
                page.wait_for_timeout(1000)
            
            # Createinterceptmapeyerecord
            screenshot_dir = os.path.join('uploads', 'screenshots', uuid)
            if not os.path.exists(screenshot_dir):
                os.makedirs(screenshot_dir)
            
            # lifebecomefilecasename
            timestamp = datetime.now().strftime('%H%M%S')
            device_suffix = device.replace('_', '-')
            page_type = 'full' if full_page else 'viewport'
            scroll_suffix = f'scroll-{scroll_distance}px' if scroll_distance > 0 else 'no-scroll'
            filename = f'screenshot_{device_suffix}_{page_type}_uuid-{uuid}_{scroll_suffix}_{timestamp}.png'
            screenshot_path = os.path.join(screenshot_dir, filename)
            
            # interceptmap，increaseaddweighttestmachinecontrol
            screenshot_success = False
            max_retries = 3
            
            for attempt in range(max_retries):
                try:
                    logger.info(f"trytestinterceptmap (Row {attempt + 1} time)")
                    page.screenshot(path=screenshot_path, full_page=full_page)
                    screenshot_success = True
                    logger.info("interceptmapsuccess")
                    break
                except Exception as screenshot_error:
                    logger.warning(f"interceptmapFailed (Row {attempt + 1} time): {str(screenshot_error)}")
                    if attempt < max_retries - 1:
                        page.wait_for_timeout(2000)
                    else:
                        logger.error("placehaveinterceptmaptrytestallFailedfinish")
                        raise screenshot_error
            
            browser.close()
            
            # takegetnevertargetroadpath
            absolute_path = os.path.abspath(screenshot_path)
            
            logger.info(f"interceptmapComplete，filecasestoresaveto: {absolute_path}")
            flash(f'interceptmapsuccess！filecasestoresaveto: {absolute_path}', 'success')
            
            # willinterceptmaproadpathstoresavearrivesession，providemodeboardclearshow
            session['last_screenshot'] = absolute_path
            session['last_screenshot_device'] = device_config['name']
            session['last_screenshot_full_page'] = full_page
            session['last_screenshot_scroll_distance'] = scroll_distance
            session['last_screenshot_uuid'] = uuid
            session['last_screenshot_adunit_title'] = adunit_data.get('title', '')
            
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        logger.error(f"frommoveinterceptmaperror occurred: {str(e)}")
        logger.error(f"Error details：\n{error_detail}")
        
        # rootaccordingerrorerrorkindtypeprovideprovidechangefriendgoodofnewsrest
        if "Timeout" in str(e):
            user_friendly_msg = "networkpageloadenterexceedtime（havetrytest 60 second），pleaseslightlyafteragaintestorcheckcheckURLisnorightsure"
        elif "net::ERR" in str(e):
            user_friendly_msg = "networkroadconnectlineerrorerror，pleasecheckcheckURLisnocanrightoftenvisitquestion"
        elif "screenshot" in str(e).lower():
            user_friendly_msg = "interceptmappassprogramsendlifeerrorerror，pleaseweightnewtrytest"
        elif "browser" in str(e).lower() or "chromium" in str(e).lower():
            user_friendly_msg = "browsebrowsedevicestartmoveFailed，pleaseslightlyafterweighttest"
        else:
            user_friendly_msg = f"interceptmapFailed: {str(e)}"
            
        flash(user_friendly_msg, 'error')
    
    return redirect(url_for('screenshot.auto_screenshot')) 

@screenshot_bp.route('/open-folder', methods=['POST'])
def open_folder():
    """openstartfilecaseclippositionplace"""
    try:
        # Parse JSON request
        data = request.get_json()
        folder_path = data.get('folder_path', '').strip()
        
        if not folder_path:
            return jsonify({'success': False, 'error': 'notprovideprovidetextitemcliproadpath'}), 400
        
        # checkcheckroadpathisnosaveexist
        if not os.path.exists(folder_path):
            return jsonify({'success': False, 'error': f'textitemclipdoes not exist: {folder_path}'}), 404
        
        # checkcheckisnotoeyerecord
        if not os.path.isdir(folder_path):
            return jsonify({'success': False, 'error': f'roadpathnoisaahaveeffectoftextitemclip: {folder_path}'}), 400
        
        # installwholecheckcheck：sureprotectroadpathexistspecialcaseeyerecordinsideortonevertargetroadpath
        abs_folder_path = os.path.abspath(folder_path)
        
        # rootaccordingworkindustrysystemsystemopenstarttextitemclip
        try:
            # macOS
            if os.name == 'posix' and os.uname().sysname == 'Darwin':
                subprocess.run(['open', abs_folder_path], check=True)
                logger.info(f"successopenstarttextitemclip (macOS): {abs_folder_path}")
            # Windows
            elif os.name == 'nt':
                subprocess.run(['explorer', abs_folder_path], check=True)
                logger.info(f"successopenstarttextitemclip (Windows): {abs_folder_path}")
            # Linux
            else:
                subprocess.run(['xdg-open', abs_folder_path], check=True)
                logger.info(f"successopenstarttextitemclip (Linux): {abs_folder_path}")
            
            return jsonify({
                'success': True, 
                'message': f'haveopenstarttextitemclip: {abs_folder_path}'
            })
            
        except subprocess.CalledProcessError as cmd_error:
            logger.error(f"openstarttextitemclipfateorderholdrowFailed: {str(cmd_error)}")
            return jsonify({
                'success': False, 
                'error': f'nomethodopenstarttextitemclip，systemsystemfateorderholdrowFailed: {str(cmd_error)}'
            }), 500
            
        except FileNotFoundError:
            logger.error("systemsystemnotFoundtargetansweroffilecasemanagereasonprogramstyle")
            return jsonify({
                'success': False, 
                'error': 'systemsystemnotFoundtargetansweroffilecasemanagereasonprogramstyle'
            }), 500
            
    except Exception as e:
        logger.error(f"openstarttextitemcliptimesendlifenotpredicttimeoferrorerror: {str(e)}")
        return jsonify({
            'success': False, 
            'error': f'openstarttextitemcliperror occurred: {str(e)}'
        }), 500
