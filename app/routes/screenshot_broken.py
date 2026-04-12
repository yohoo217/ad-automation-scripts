from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from playwright.sync_api import sync_playwright, TimeoutError as PwTimeout
import logging
import os
import base64
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
            elif (".example.com" in domain or "platform.example.com" == domain):
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
                            
                            for i, selector in enumerate(selectors_to_try, 1):
                                logger.info(f"🔎 trytestselector {i}/{len(selectors_to_try)}: {selector}")
                                try:
                                    elements = page.locator(selector)
                                    count = elements.count()
                                    logger.info(f"   📊 Found{count}apairmatchoriginelement")
                                    
                                    if count > 0:
                                        # rememberrecordFoundoforiginelementdetailedemotion
                                        element = elements.first
                                        try:
                                            element_id = element.get_attribute("id") or "noid"
                                            element_class = element.get_attribute("class") or "noclass"
                                            tag_name = element.evaluate("el => el.tagName")
                                            logger.info(f"   ✅ Foundeyelabeloriginelement: <{tag_name}> id='{element_id}' class='{element_class}'")
                                            
                                            # checkcheckoriginelementisnocansee
                                            is_visible = element.is_visible()
                                            logger.info(f"   👁️  originelementcanseesex: {is_visible}")
                                            
                                            if is_visible:
                                                ad_selector = selector
                                                ad_container_found = True
                                                logger.info(f"✅ stepsudden2Complete: willmakeuseselector '{selector}'")
                                                break
                                            else:
                                                logger.info(f"   ⚠️  originelementnocansee，trytestdownaaselector")
                                                
                                        except Exception as element_error:
                                            logger.warning(f"   ⚠️  nomethodtakegetoriginelementdetailedemotion: {element_error}")
                                    else:
                                        logger.info(f"   ❌ nopairmatchoriginelement")
                                        
                                except Exception as selector_error:
                                    logger.warning(f"   ⚠️  selectorerrorerror: {selector_error}")
                        
                        if not ad_container_found:
                            logger.error("❌ stepsudden2Failed: notFoundassignwhatcanseeofeyelabeloriginelement")
                            raise RuntimeError("notFoundeyelabeloriginelement")
                        
                        # ── 3. calculatecountandholdrowplaceinrollmove ──
                        logger.info("📐 stepsudden3: calculatecountandholdrowplaceinrollmove...")
                        logger.info(f"   makeuseselector: {ad_selector}")
                        
                        scroll_result = page.evaluate(
                            """
                            (sel) => {
                                console.log('🎯 openbeginplaceincalculatecount，selector:', sel);
                                const el = document.querySelector(sel);
                                if (!el) {
                                    console.error('❌ findnoarriveAdoriginelement');
                                    return { success: false, error: 'findnoarriveoriginelement' };
                                }
                                
                                const rect = el.getBoundingClientRect();
                                const viewportHeight = window.innerHeight;
                                const currentScrollY = window.pageYOffset;
                                const elementTop = rect.top + currentScrollY;
                                const elementHeight = rect.height;
                                const viewportMiddle = viewportHeight / 2;
                                const targetScrollY = elementTop - viewportMiddle + (elementHeight / 2);
                                
                                const result = {
                                    success: true,
                                    viewportHeight: viewportHeight,
                                    currentScrollY: currentScrollY,
                                    elementTop: elementTop,
                                    elementHeight: elementHeight,
                                    targetScrollY: targetScrollY,
                                    beforeTop: rect.top
                                };
                                
                                console.log('📊 placeincalculatecountresultfruit:', result);
                                
                                // holdrowrollmove
                                window.scrollTo({ top: Math.max(0, targetScrollY), behavior: 'instant' });
                                
                                // checkcheckrollmoveafterofpositionplace
                                const newRect = el.getBoundingClientRect();
                                result.afterTop = newRect.top;
                                result.actualScrollY = window.pageYOffset;
                                
                                console.log('✅ rollmoveholdrowComplete，mostendpositionplace:', {
                                    afterTop: result.afterTop,
                                    actualScrollY: result.actualScrollY
                                });
                                
                                return result;
                            }
                            """,
                            ad_selector
                        )
                        
                        if scroll_result['success']:
                            logger.info("✅ stepsudden3Complete: placeinrollmovehaveholdrow")
                            logger.info(f"   📊 rollmovefrontoriginelementdistancetopdepartment: {scroll_result['beforeTop']}px")
                            logger.info(f"   📊 rollmoveafteroriginelementdistancetopdepartment: {scroll_result['afterTop']}px")
                            logger.info(f"   📊 eyelabelrollmovepositionplace: {scroll_result['targetScrollY']}px")
                            logger.info(f"   📊 realborderrollmovepositionplace: {scroll_result['actualScrollY']}px")
                        else:
                            logger.error(f"❌ stepsudden3Failed: {scroll_result.get('error', 'notknowerrorerror')}")
                            raise RuntimeError("placeinrollmoveFailed")
                        
                        # ── 4. verifycertificateplaceinresultfruit ──
                        logger.info("⏱️  stepsudden4: verifycertificateoriginelementisnosuccessplacein...")
                        page.wait_for_timeout(500)  # Waiting forrollmoveComplete
                        
                        verification_result = page.evaluate(
                            """
                            (sel, tolerance) => {
                                const el = document.querySelector(sel);
                                if (!el) {
                                    return { success: false, error: 'verifycertificatetimefindnoarriveoriginelement' };
                                }
                                
                                const rect = el.getBoundingClientRect();
                                const viewportMiddle = window.innerHeight / 2;
                                const elementMiddle = rect.top + rect.height / 2;
                                const distance = Math.abs(elementMiddle - viewportMiddle);
                                const isCentered = distance <= tolerance;
                                
                                const result = {
                                    success: isCentered,
                                    elementTop: rect.top,
                                    elementBottom: rect.bottom,
                                    elementMiddle: elementMiddle,
                                    viewportMiddle: viewportMiddle,
                                    distance: distance,
                                    tolerance: tolerance
                                };
                                
                                console.log('📏 placeinverifycertificateresultfruit:', result);
                                return result;
                            }
                            """,
                            ad_selector,
                            30  # 30pxcontainerrorscopesurround
                        )
                        
                        if verification_result['success']:
                            logger.info("✅ stepsudden4Complete: originelementhavesuccessplacein")
                            logger.info(f"   📏 originelementinheartpoint: {verification_result['elementMiddle']:.1f}px")
                            logger.info(f"   📏 viewwindowinheartpoint: {verification_result['viewportMiddle']:.1f}px")
                            logger.info(f"   📏 biasdifferdistancedistance: {verification_result['distance']:.1f}px")
                        else:
                            logger.warning("⚠️  stepsudden4warningtell: originelementnotperfectwholeplacein，butcontinuecontinueadvancerow")
                            logger.info(f"   📏 biasdifferdistancedistance: {verification_result['distance']:.1f}px (containerror: 30px)")
                        
                        # ── 5. Waiting forAdperfectwholeloadenter ──
                        logger.info("🔄 stepsudden5: Waiting forAdperfectwholeloadenter...")
                        page.wait_for_timeout(1500)
                        logger.info("✅ stepsudden5Complete: AdloadenterWaiting forresultbundle")
                        logger.info("🎉 1200x628 AdoriginelementplaceinflowprogramwholedepartmentComplete!")
                        
                    except PwTimeout as te:
                        logger.warning(f"⏰ Timeouterrorerror: {te} → makeusefallbackrollmove")
                        page.mouse.wheel(0, scroll_distance)
                        page.wait_for_timeout(1500)
                    except Exception as e:
                        logger.warning(f"❌ 1200x628 placeinflowprogramFailed: {e} → makeusefallbackrollmove")
                        page.mouse.wheel(0, scroll_distance)
                        page.wait_for_timeout(1500)
                
                if template == 'social-forum':
                    # useslidemouserollround，SocialForum nowillholditrestoreoriginal，and lazy-load stillcantouchsend
                    logger.info("🏷️  SocialForummodeboard - makeuseslidemouserollroundrollmove")
                    page.mouse.wheel(0, scroll_distance)
                    logger.info("✅ SocialForumslidemouserollroundrollmoveComplete")

                else:
                    # hishenetworkstationprotectholdoriginalcomeofdomethod
                    logger.info("🏷️  labelstandardmodeboard - makeusewindow.scrollTorollmove")
                    page.evaluate(f"window.scrollTo(0, {scroll_distance})")
                    logger.info("✅ labelstandardrollmoveComplete")

                # Waiting forrollmoveComplete（1200x628 removeoutside，reasontohavethroughuse wait_for_function sureknow）
                if not (size == '1200x628' and template in ['news-article']):
                    logger.info("⏳ Waiting forrollmoveComplete...")
                    page.wait_for_timeout(1000)
                    logger.info("✅ rollmoveflowprogramComplete")
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
                        
                        for i, selector in enumerate(selectors_to_try, 1):
                            logger.info(f"   🔎 trytestselector {i}/{len(selectors_to_try)}: {selector}")
                            try:
                                elements = page.locator(selector)
                                count = elements.count()
                                logger.info(f"   📊 Found{count}apairmatchoriginelement")
                                
                                if count > 0:
                                    # rememberrecordFoundoforiginelementdetailedemotion
                                    element = elements.first
                                    try:
                                        element_id = element.get_attribute("id") or "noid"
                                        element_class = element.get_attribute("class") or "noclass"
                                        tag_name = element.evaluate("el => el.tagName")
                                        logger.info(f"   ✅ Foundeyelabeloriginelement: <{tag_name}> id='{element_id}' class='{element_class}'")
                                        
                                        # checkcheckoriginelementisnocansee
                                        is_visible = element.is_visible()
                                        logger.info(f"   👁️  originelementcanseesex: {is_visible}")
                                        
                                        if is_visible:
                                            ad_selector = selector
                                            ad_container_found = True
                                            logger.info(f"✅ stepsudden2Complete: willmakeuseselector '{selector}'")
                                            break
                                        else:
                                            logger.info(f"   ⚠️  originelementnocansee，trytestdownaaselector")
                                            
                                    except Exception as element_error:
                                        logger.warning(f"   ⚠️  nomethodtakegetoriginelementdetailedemotion: {element_error}")
                                else:
                                    logger.info(f"   ❌ nopairmatchoriginelement")
                                    
                            except Exception as selector_error:
                                logger.warning(f"   ⚠️  selectorerrorerror: {selector_error}")
                        
                        if not ad_container_found:
                            logger.error("❌ stepsudden2Failed: notFoundassignwhatcanseeofeyelabeloriginelement")
                            raise RuntimeError("notFoundeyelabeloriginelement")
                        
                        # ── 3. calculatecountandholdrowplaceinrollmove ──
                        logger.info("📐 stepsudden3: calculatecountandholdrowplaceinrollmove...")
                        logger.info(f"   makeuseselector: {ad_selector}")
                        
                        scroll_result = page.evaluate(
                            """
                            (sel) => {
                                console.log('🎯 openbeginplaceincalculatecount，selector:', sel);
                                const el = document.querySelector(sel);
                                if (!el) {
                                    console.error('❌ findnoarriveAdoriginelement');
                                    return { success: false, error: 'findnoarriveoriginelement' };
                                }
                                
                                const rect = el.getBoundingClientRect();
                                const viewportHeight = window.innerHeight;
                                const currentScrollY = window.pageYOffset;
                                const elementTop = rect.top + currentScrollY;
                                const elementHeight = rect.height;
                                const viewportMiddle = viewportHeight / 2;
                                const targetScrollY = elementTop - viewportMiddle + (elementHeight / 2);
                                
                                const result = {
                                    success: true,
                                    viewportHeight: viewportHeight,
                                    currentScrollY: currentScrollY,
                                    elementTop: elementTop,
                                    elementHeight: elementHeight,
                                    targetScrollY: targetScrollY,
                                    beforeTop: rect.top
                                };
                                
                                console.log('📊 placeincalculatecountresultfruit:', result);
                                
                                // holdrowrollmove
                                window.scrollTo({ top: Math.max(0, targetScrollY), behavior: 'instant' });
                                
                                // checkcheckrollmoveafterofpositionplace
                                const newRect = el.getBoundingClientRect();
                                result.afterTop = newRect.top;
                                result.actualScrollY = window.pageYOffset;
                                
                                console.log('✅ rollmoveholdrowComplete，mostendpositionplace:', {
                                    afterTop: result.afterTop,
                                    actualScrollY: result.actualScrollY
                                });
                                
                                return result;
                            }
                            """,
                            ad_selector
                        )
                        
                        if scroll_result['success']:
                            logger.info("✅ stepsudden3Complete: placeinrollmovehaveholdrow")
                            logger.info(f"   📊 rollmovefrontoriginelementdistancetopdepartment: {scroll_result['beforeTop']}px")
                            logger.info(f"   📊 rollmoveafteroriginelementdistancetopdepartment: {scroll_result['afterTop']}px")
                            logger.info(f"   📊 eyelabelrollmovepositionplace: {scroll_result['targetScrollY']}px")
                            logger.info(f"   📊 realborderrollmovepositionplace: {scroll_result['actualScrollY']}px")
                        else:
                            logger.error(f"❌ stepsudden3Failed: {scroll_result.get('error', 'notknowerrorerror')}")
                            raise RuntimeError("placeinrollmoveFailed")
                        
                        # ── 4. verifycertificateplaceinresultfruit ──
                        logger.info("⏱️  stepsudden4: verifycertificateoriginelementisnosuccessplacein...")
                        page.wait_for_timeout(500)  # Waiting forrollmoveComplete
                        
                        verification_result = page.evaluate(
                            """
                            (sel, tolerance) => {
                                const el = document.querySelector(sel);
                                if (!el) {
                                    return { success: false, error: 'verifycertificatetimefindnoarriveoriginelement' };
                                }
                                
                                const rect = el.getBoundingClientRect();
                                const viewportMiddle = window.innerHeight / 2;
                                const elementMiddle = rect.top + rect.height / 2;
                                const distance = Math.abs(elementMiddle - viewportMiddle);
                                const isCentered = distance <= tolerance;
                                
                                const result = {
                                    success: isCentered,
                                    elementTop: rect.top,
                                    elementBottom: rect.bottom,
                                    elementMiddle: elementMiddle,
                                    viewportMiddle: viewportMiddle,
                                    distance: distance,
                                    tolerance: tolerance
                                };
                                
                                console.log('📏 placeinverifycertificateresultfruit:', result);
                                return result;
                            }
                            """,
                            ad_selector,
                            30  # 30pxcontainerrorscopesurround
                        )
                        
                        if verification_result['success']:
                            logger.info("✅ stepsudden4Complete: originelementhavesuccessplacein")
                            logger.info(f"   📏 originelementinheartpoint: {verification_result['elementMiddle']:.1f}px")
                            logger.info(f"   📏 viewwindowinheartpoint: {verification_result['viewportMiddle']:.1f}px")
                            logger.info(f"   📏 biasdifferdistancedistance: {verification_result['distance']:.1f}px")
                        else:
                            logger.warning("⚠️  stepsudden4warningtell: originelementnotperfectwholeplacein，butcontinuecontinueadvancerow")
                            logger.info(f"   📏 biasdifferdistancedistance: {verification_result['distance']:.1f}px (containerror: 30px)")
                        
                        # ── 5. Waiting forAdperfectwholeloadenter ──
                        logger.info("🔄 stepsudden5: Waiting forAdperfectwholeloadenter...")
                        page.wait_for_timeout(1500)
                        logger.info("✅ stepsudden5Complete: AdloadenterWaiting forresultbundle")
                        logger.info("🎉 1200x628 AdoriginelementplaceinflowprogramwholedepartmentComplete!")
                        
                    except PwTimeout as te:
                        logger.warning(f"⏰ Timeouterrorerror: {te} → makeusefallbackrollmove")
                        page.mouse.wheel(0, scroll_distance)
                        page.wait_for_timeout(1500)
                    except Exception as e:
                        logger.warning(f"❌ 1200x628 placeinflowprogramFailed: {e} → makeusefallbackrollmove")
                        page.mouse.wheel(0, scroll_distance)
                        page.wait_for_timeout(1500)

                # specialspecialProcessing 300x250 Size：rollmovearrive「setimmediatelyapplyplease」buttonandplacein
                elif size == '300x250' and template == 'social-forum':
                    logger.info("🎯 300x250 → openbegin「setimmediatelyapplyplease」buttonplaceinflowprogram")
                    try:
                        # ── 1. Waiting forpagefaceharmonyAdloadenter ──
                        logger.info("📱 stepsudden1: Waiting forpagefaceharmonyAdloadenter...")
                        page.wait_for_timeout(2000)
                        logger.info("✅ stepsudden1Complete: Waiting fortimeroomresultbundle")
                        
                        # ── 2. searchfind「setimmediatelyapplyplease」buttonoriginelement ──
                        logger.info("🔍 stepsudden2: searchfind「setimmediatelyapplyplease」buttonoriginelement...")
                        button_found = False
                        button_selector = None
                        
                        # trytestnosameofbuttonselector
                        button_selectors_to_try = [
                            'button:has-text("setimmediatelyapplyplease")',               # mostessencestandard：packageinclude"setimmediatelyapplyplease"texttextofbutton
                            'button[class*="_platform_tk_text-sm"]',      # packageincludespecialset class ofbutton
                            'button[style*="width: 100px"]',            # packageincludespecialsetwidedegreeofbutton
                            'button[class*="_platform_tk_bg-black"]',     # packageincludeblackcolorbackviewclassofbutton
                            'div[class*="_platform_tk_justify-end"] button', # existjustify-endcontaindeviceinsideofbutton
                            'div[data-platform-id] button',                 # platformcontaindeviceinsideofbutton
                            'iframe[src*="/300x250"]',                  # equipmentuse：300x250Adiframe
                            'iframe[src*="tkcatrun"]',                  # equipmentuse：catrun iframe
                            '[data-platform-ad]'                            # equipmentuse：platformAdbelongsex
                        ]
                        
                        for i, selector in enumerate(button_selectors_to_try, 1):
                            logger.info(f"   🔎 trytestselector {i}/{len(button_selectors_to_try)}: {selector}")
                            try:
                                elements = page.locator(selector)
                                count = elements.count()
                                logger.info(f"   📊 Found{count}apairmatchoriginelement")
                                
                                if count > 0:
                                    # rememberrecordFoundoforiginelementdetailedemotion
                                    element = elements.first
                                    try:
                                        element_id = element.get_attribute("id") or "noid"
                                        element_class = element.get_attribute("class") or "noclass"
                                        tag_name = element.evaluate("el => el.tagName")
                                        element_text = element.text_content() or "notexttext"
                                        logger.info(f"   ✅ Foundeyelabeloriginelement: <{tag_name}> id='{element_id}' class='{element_class}' text='{element_text}'")
                                        
                                        # checkcheckoriginelementisnocansee
                                        is_visible = element.is_visible()
                                        logger.info(f"   👁️  originelementcanseesex: {is_visible}")
                                        
                                        if is_visible:
                                            button_selector = selector
                                            button_found = True
                                            logger.info(f"✅ stepsudden2Complete: willmakeuseselector '{selector}'")
                                            break
                                        else:
                                            logger.info(f"   ⚠️  originelementnocansee，trytestdownaaselector")
                                            
                                    except Exception as element_error:
                                        logger.warning(f"   ⚠️  nomethodtakegetoriginelementdetailedemotion: {element_error}")
                                else:
                                    logger.info(f"   ❌ nopairmatchoriginelement")
                                    
                            except Exception as selector_error:
                                logger.warning(f"   ⚠️  selectorerrorerror: {selector_error}")
                        
                        if not button_found:
                            logger.error("❌ stepsudden2Failed: notFoundassignwhatcanseeof「setimmediatelyapplyplease」button")
                            raise RuntimeError("notFoundsetimmediatelyapplypleasebutton")
                        
                        # ── 3. calculatecountandholdrowplaceinrollmove ──
                        logger.info("📐 stepsudden3: calculatecountandholdrowplaceinrollmove...")
                        logger.info(f"   makeuseselector: {button_selector}")
                        
                        scroll_result = page.evaluate(
                            """
                            (sel) => {
                                console.log('🎯 openbeginplaceincalculatecount，selector:', sel);
                                const el = document.querySelector(sel);
                                if (!el) {
                                    console.error('❌ findnoarrivebuttonoriginelement');
                                    return { success: false, error: 'findnoarriveoriginelement' };
                                }
                                
                                const rect = el.getBoundingClientRect();
                                const viewportHeight = window.innerHeight;
                                const currentScrollY = window.pageYOffset;
                                const elementTop = rect.top + currentScrollY;
                                const elementHeight = rect.height;
                                const viewportMiddle = viewportHeight / 2;
                                const targetScrollY = elementTop - viewportMiddle + (elementHeight / 2);
                                
                                const result = {
                                    success: true,
                                    viewportHeight: viewportHeight,
                                    currentScrollY: currentScrollY,
                                    elementTop: elementTop,
                                    elementHeight: elementHeight,
                                    targetScrollY: targetScrollY,
                                    beforeTop: rect.top
                                };
                                
                                console.log('📊 placeincalculatecountresultfruit:', result);
                                
                                // holdrowrollmove
                                window.scrollTo({ top: Math.max(0, targetScrollY), behavior: 'instant' });
                                
                                // checkcheckrollmoveafterofpositionplace
                                const newRect = el.getBoundingClientRect();
                                result.afterTop = newRect.top;
                                result.actualScrollY = window.pageYOffset;
                                
                                console.log('✅ rollmoveholdrowComplete，mostendpositionplace:', {
                                    afterTop: result.afterTop,
                                    actualScrollY: result.actualScrollY
                                });
                                
                                return result;
                            }
                            """,
                            button_selector
                        )
                        
                        if scroll_result['success']:
                            logger.info("✅ stepsudden3Complete: placeinrollmovehaveholdrow")
                            logger.info(f"   📊 rollmovefrontoriginelementdistancetopdepartment: {scroll_result['beforeTop']}px")
                            logger.info(f"   📊 rollmoveafteroriginelementdistancetopdepartment: {scroll_result['afterTop']}px")
                            logger.info(f"   📊 eyelabelrollmovepositionplace: {scroll_result['targetScrollY']}px")
                            logger.info(f"   📊 realborderrollmovepositionplace: {scroll_result['actualScrollY']}px")
                        else:
                            logger.error(f"❌ stepsudden3Failed: {scroll_result.get('error', 'notknowerrorerror')}")
                            raise RuntimeError("placeinrollmoveFailed")
                        
                        # ── 4. verifycertificateplaceinresultfruit ──
                        logger.info("⏱️  stepsudden4: verifycertificatebuttonisnosuccessplacein...")
                        page.wait_for_timeout(500)  # Waiting forrollmoveComplete
                        
                        verification_result = page.evaluate(
                            """
                            (sel, tolerance) => {
                                const el = document.querySelector(sel);
                                if (!el) {
                                    return { success: false, error: 'verifycertificatetimefindnoarriveoriginelement' };
                                }
                                
                                const rect = el.getBoundingClientRect();
                                const viewportMiddle = window.innerHeight / 2;
                                const elementMiddle = rect.top + rect.height / 2;
                                const distance = Math.abs(elementMiddle - viewportMiddle);
                                const isCentered = distance <= tolerance;
                                
                                const result = {
                                    success: isCentered,
                                    elementTop: rect.top,
                                    elementBottom: rect.bottom,
                                    elementMiddle: elementMiddle,
                                    viewportMiddle: viewportMiddle,
                                    distance: distance,
                                    tolerance: tolerance
                                };
                                
                                console.log('📏 placeinverifycertificateresultfruit:', result);
                                return result;
                            }
                            """,
                            button_selector,
                            30  # 30pxcontainerrorscopesurround
                        )
                        
                        if verification_result['success']:
                            logger.info("✅ stepsudden4Complete: buttonhavesuccessplacein")
                            logger.info(f"   📏 buttoninheartpoint: {verification_result['elementMiddle']:.1f}px")
                            logger.info(f"   📏 viewwindowinheartpoint: {verification_result['viewportMiddle']:.1f}px")
                            logger.info(f"   📏 biasdifferdistancedistance: {verification_result['distance']:.1f}px")
                        else:
                            logger.warning("⚠️  stepsudden4warningtell: buttonnotperfectwholeplacein，butcontinuecontinueadvancerow")
                            logger.info(f"   📏 biasdifferdistancedistance: {verification_result['distance']:.1f}px (containerror: 30px)")
                        
                        # ── 5. Waiting forAdperfectwholeloadenter ──
                        logger.info("🔄 stepsudden5: Waiting forAdperfectwholeloadenter...")
                        page.wait_for_timeout(1500)
                        logger.info("✅ stepsudden5Complete: AdloadenterWaiting forresultbundle")
                        logger.info("🎉 300×250「setimmediatelyapplyplease」buttonplaceinflowprogramwholedepartmentComplete!")
                        
                    except PwTimeout as te:
                        logger.warning(f"⏰ Timeouterrorerror: {te} → makeusefallbackrollmove")
                        page.mouse.wheel(0, scroll_distance)
                        page.wait_for_timeout(1500)
                    except Exception as e:
                        logger.warning(f"❌ 300×250 placeinflowprogramFailed: {e} → makeusefallbackrollmove")
                        page.mouse.wheel(0, scroll_distance)
                        page.wait_for_timeout(1500)

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

                # Waiting forrollmoveComplete（1200x628harmony300x250placeinflowprogramremoveoutside，reasontohavethroughhavefromselfofWaiting for）
                if not ((size == '1200x628' and template in ['news-article']) or (size == '300x250' and template == 'social-forum')):
                    logger.info("⏳ Waiting forrollmoveComplete...")
                    page.wait_for_timeout(1000)
                    logger.info("✅ rollmoveflowprogramComplete")
            else:
                logger.info("🚫 notsetsetrollmovedistancedistance，jumppassrollmove")

            # Createinterceptmapeyerecord
            today = datetime.now().strftime('%Y%m%d')
            screenshot_dir = os.path.join('uploads', 'screenshots', today)
            if not os.path.exists(screenshot_dir):
                os.makedirs(screenshot_dir)
            
            # lifebecomefilecasename
            timestamp = datetime.now().strftime('%H%M%S')
            device_suffix = device.replace('_', '-')
            
            # specialspecialProcessing 1200x628 harmony 300x250 offilecasename
            if size == '1200x628' and template in ['news-article']:
                scroll_suffix = 'element-scroll'
            elif size == '300x250' and template == 'social-forum':
                scroll_suffix = 'button-scroll'
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

                        # specialspecialProcessingplaceinflowprogramofweighttest
                        if size == '1200x628' and template in ['news-article']:
                            logger.info("🎯 weighttest-1200x628 → simplechangeplaceinflowprogram")
                            try:
                                selectors_to_try = [
                                    'button[class*="_platform_tk_text-sm"]',
                                    'button[style*="width: 100px"]',
                                    '#platform-ad-news-article-middle',
                                    'div[data-platform-id]'
                                ]
                                
                                for selector in selectors_to_try:
                                    elements = page.locator(selector)
                                    if elements.count() > 0 and elements.first.is_visible():
                                        page.evaluate(f"""
                                            const el = document.querySelector('{selector}');
                                            if (el) {{
                                                const rect = el.getBoundingClientRect();
                                                const targetY = rect.top + window.pageYOffset - window.innerHeight/2 + rect.height/2;
                                                window.scrollTo({{top: Math.max(0, targetY), behavior: 'instant'}});
                                            }}
                                        """)
                                        page.wait_for_timeout(1000)
                                        logger.info("✅ weighttest-1200x628simplechangeplaceinComplete")
                                        break
                                else:
                                    page.mouse.wheel(0, scroll_distance)
                            except:
                                page.mouse.wheel(0, scroll_distance)
                        
                        elif size == '300x250' and template == 'social-forum':
                            logger.info("🎯 weighttest-300x250 → simplechangeplaceinflowprogram")
                            try:
                                button_selectors = [
                                    'button:has-text("setimmediatelyapplyplease")',
                                    'button[class*="_platform_tk_text-sm"]',
                                    'button[style*="width: 100px"]'
                                ]
                                
                                for selector in button_selectors:
                                    elements = page.locator(selector)
                                    if elements.count() > 0 and elements.first.is_visible():
                                        page.evaluate(f"""
                                            const el = document.querySelector('{selector}');
                                            if (el) {{
                                                const rect = el.getBoundingClientRect();
                                                const targetY = rect.top + window.pageYOffset - window.innerHeight/2 + rect.height/2;
                                                window.scrollTo({{top: Math.max(0, targetY), behavior: 'instant'}});
                                            }}
                                        """)
                                        page.wait_for_timeout(1000)
                                        logger.info("✅ weighttest-300x250simplechangeplaceinComplete")
                                        break
                                else:
                                    page.mouse.wheel(0, scroll_distance)
                            except:
                                page.mouse.wheel(0, scroll_distance)
                        
                        else:
                            # hisheemotionsituationmakeuselabelstandardrollmove
                            page.mouse.wheel(0, scroll_distance)
                        
                        page.wait_for_timeout(1000)
                    
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
            
            logger.info(f"interceptmapComplete，filecasestoresaveto: {absolute_path}")
            flash(f'interceptmapsuccess！filecasestoresaveto: {absolute_path}', 'success')
            
            # willinterceptmaproadpathstoresavearrivesession，providemodeboardclearshow
            session['last_screenshot'] = absolute_path
            session['last_screenshot_device'] = device_config['name']
            session['last_screenshot_full_page'] = False
            session['last_screenshot_scroll_distance'] = scroll_distance
            session['last_screenshot_uuid'] = uuid
            session['last_screenshot_adunit_title'] = adunit_data.get('title', '')
            
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
            today = datetime.now().strftime('%Y%m%d')
            screenshot_dir = os.path.join('uploads', 'screenshots', today)
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
