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
    """自動截圖頁面"""
    return render_template('auto_screenshot.html')

@screenshot_bp.route('/native-ad-screenshot')
def native_ad_screenshot():
    """Native 廣告多尺寸截圖頁面"""
    return render_template('native_ad_screenshot.html')

@screenshot_bp.route('/create-native-screenshot', methods=['POST'])
def create_native_screenshot():
    """Native 廣告多尺寸截圖處理"""
    try:
        # 解析 JSON 請求
        data = request.get_json()
        uuid = data.get('uuid', '').strip()
        size = data.get('size', '')
        device = data.get('device', 'iphone_x')
        scroll_distance = int(data.get('scroll_distance', 4800))
        template = data.get('template', 'ptt-article')
        
        if not uuid or not size:
            return jsonify({'success': False, 'error': '缺少必要參數'}), 400
        
        # 從 MongoDB 查詢 AdUnit 資料
        logger.info(f"正在查詢 UUID: {uuid}")
        adunit_data = get_adunit_by_uuid(uuid)
        
        if not adunit_data:
            return jsonify({'success': False, 'error': f'找不到 UUID {uuid} 對應的 AdUnit 資料'}), 404
        
        # 建構截圖網址
        url = build_native_screenshot_url(adunit_data, size, template)
        if not url:
            return jsonify({'success': False, 'error': '無法建構截圖網址'}), 400
        
        logger.info(f"建構的截圖網址: {url}")
        
        # 裝置尺寸配置
        device_configs = {
            'iphone_x': {'width': 375, 'height': 812, 'name': 'iPhone X'},
            'iphone_se': {'width': 375, 'height': 667, 'name': 'iPhone SE'},
            'iphone_plus': {'width': 414, 'height': 736, 'name': 'iPhone Plus'},
            'android': {'width': 360, 'height': 640, 'name': 'Android 標準'},
            'tablet': {'width': 768, 'height': 1024, 'name': '平板電腦'},
            'desktop': {'width': 1920, 'height': 1080, 'name': '桌上型電腦'}
        }
        
        device_config = device_configs.get(device, device_configs['iphone_x'])
        
        default_cookie = os.getenv("PLATFORM_COOKIE", "")
        
        logger.info(f"開始截圖 {size}，目標網址: {url}, 裝置: {device_config['name']}, UUID: {uuid}")
        
        # 使用 Playwright 進行截圖
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
            
            # 根據裝置類型和網站設定不同的上下文
            extra_http_headers = {}
            
            # 為外部網站設置額外的 headers
            if template in ['moptt', 'pnn-article']:
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
            
            # 根據不同模板和尺寸設置不同的 cookies
            parsed_url = urlparse(url)
            domain = parsed_url.netloc
            
            # 為預覽頁設置專用 cookies
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
                    logger.info(f"已為預覽頁設置 {len(cookies)} 個專用 cookies")
                    
                except Exception as cookie_error:
                    logger.warning(f"設置預覽頁 cookies 時發生錯誤（將繼續不使用 cookie）: {str(cookie_error)}")
            
            # 對於平台相關網址設置預設 cookies
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
                    logger.info(f"已為平台網域設置 {len(cookies)} 個 cookies")
                    
                except Exception as cookie_error:
                    logger.warning(f"設置 cookie 時發生錯誤（將繼續不使用 cookie）: {str(cookie_error)}")
            else:
                logger.info(f"外部網址 {domain}，跳過 cookie 設置")
            
            try:
                # 根據不同網站使用不同的載入策略
                logger.info(f"🌐 開始載入頁面: {url}")
                logger.info(f"📋 使用模板: {template}, 尺寸: {size}")
                
                if template == 'moptt' and size == '300x250':
                    logger.info("🏷️  使用MoPTT 300x250特殊載入策略")
                    page.goto(url, wait_until='domcontentloaded', timeout=2000)
                    page.wait_for_timeout(1000)

                elif template == 'pnn-article' and size == '640x200':
                    logger.info("🏷️  使用PNN 640x200特殊載入策略")
                    # 簡化的 640x200 處理 - 移除降速和大量 log
                    page.goto(url, wait_until='commit', timeout=6000)
                    page.wait_for_timeout(3000)
                    
                    # 簡單等待廣告載入
                    logger.info("🔍 搜尋PNN廣告容器...")
                    try:
                        page.wait_for_selector('#platform-ad-pnn-article', timeout=2000)
                        logger.info("✅ 找到PNN廣告容器: #platform-ad-pnn-article")
                    except:
                        logger.warning("⚠️  未找到#platform-ad-pnn-article，嘗試通用容器...")
                        try:
                            page.wait_for_selector('div[data-platform-id]', timeout=1000)
                            logger.info("✅ 找到通用廣告容器: div[data-platform-id]")
                        except:
                            logger.warning("⚠️  未找到任何PNN廣告容器")
                    
                    page.wait_for_timeout(2000)
                    
                else: # 平台頁面或其他
                    logger.info("🏷️  使用標準載入策略 (networkidle)")
                    page.goto(url, wait_until='networkidle', timeout=12000)
                    logger.info("✅ 頁面networkidle完成")
                    page.wait_for_timeout(1000)
                    
                    # 詳細的廣告容器搜尋
                    logger.info("🔍 開始搜尋廣告容器...")
                    
                    # 首先檢查頁面基本結構
                    try:
                        logger.info("📊 檢查頁面基本結構...")
                        page_title = page.title()
                        logger.info(f"📄 頁面標題: {page_title}")
                        
                        # 檢查是否有主要的Vue應用容器
                        app_exists = page.locator("#app").count() > 0
                        logger.info(f"🎯 Vue應用容器#app存在: {app_exists}")
                        
                        # 檢查iframe數量
                        iframe_count = page.locator("iframe").count()
                        logger.info(f"🖼️  頁面iframe數量: {iframe_count}")
                        
                        if iframe_count > 0:
                            for i in range(iframe_count):
                                iframe = page.locator("iframe").nth(i)
                                iframe_src = iframe.get_attribute("src") or "無src"
                                iframe_id = iframe.get_attribute("id") or "無id"
                                iframe_name = iframe.get_attribute("name") or "無name"
                                logger.info(f"   🖼️  iframe[{i}]: id='{iframe_id}', name='{iframe_name}', src='{iframe_src[:100]}...'")
                        
                    except Exception as structure_error:
                        logger.warning(f"📊 頁面結構檢查失敗: {structure_error}")
                    
                    # 搜尋廣告容器
                    ad_container_found = False
                    
                    try:
                        if template == 'pnn-article':
                            logger.info("🎯 搜尋PNN廣告容器: #platform-ad-pnn-article")
                            page.wait_for_selector('#platform-ad-pnn-article', timeout=2000)
                            logger.info("✅ 找到PNN廣告容器")
                            ad_container_found = True
                        else:
                            # 嘗試不同的廣告容器selector
                            selectors_to_try = [
                                'button:has-text("觀看更多")',               # 最精準：包含"觀看更多"文字的按鈕
                                'button[class*="_platform_tk_text-sm"]',      # 包含特定 class 的按鈕
                                'button[style*="width: 100px"]',            # 包含特定寬度的按鈕
                                'button[class*="_platform_tk_bg-black"]',     # 包含黑色背景class的按鈕
                                '#platform-ad-ptt-article-middle',              # 備用：原廣告容器
                                'div[data-platform-id]',                        # 備用：通用platform容器
                                'iframe[src*="/1200x628"]',                 # 備用：1200x628廣告iframe
                                'iframe[src*="tkcatrun"]',                  # 備用：catrun iframe
                                'iframe[title="Advertisement"]',             # 備用：廣告iframe
                                '[data-platform-ad]'                            # 備用：platform廣告屬性
                            ]
                            
                            for i, selector in enumerate(selectors_to_try, 1):
                                logger.info(f"🔎 嘗試selector {i}/{len(selectors_to_try)}: {selector}")
                                try:
                                    elements = page.locator(selector)
                                    count = elements.count()
                                    logger.info(f"   📊 找到{count}個匹配元素")
                                    
                                    if count > 0:
                                        # 記錄找到的元素詳情
                                        element = elements.first
                                        try:
                                            element_id = element.get_attribute("id") or "無id"
                                            element_class = element.get_attribute("class") or "無class"
                                            tag_name = element.evaluate("el => el.tagName")
                                            logger.info(f"   ✅ 找到目標元素: <{tag_name}> id='{element_id}' class='{element_class}'")
                                            
                                            # 檢查元素是否可見
                                            is_visible = element.is_visible()
                                            logger.info(f"   👁️  元素可見性: {is_visible}")
                                            
                                            if is_visible:
                                                ad_selector = selector
                                                ad_container_found = True
                                                logger.info(f"✅ 步驟2完成: 將使用selector '{selector}'")
                                                break
                                            else:
                                                logger.info(f"   ⚠️  元素不可見，嘗試下一個selector")
                                                
                                        except Exception as element_error:
                                            logger.warning(f"   ⚠️  無法取得元素詳情: {element_error}")
                                    else:
                                        logger.info(f"   ❌ 無匹配元素")
                                        
                                except Exception as selector_error:
                                    logger.warning(f"   ⚠️  selector錯誤: {selector_error}")
                        
                        if not ad_container_found:
                            logger.error("❌ 步驟2失敗: 未找到任何可見的目標元素")
                            raise RuntimeError("未找到目標元素")
                        
                        # ── 3. 計算並執行置中滾動 ──
                        logger.info("📐 步驟3: 計算並執行置中滾動...")
                        logger.info(f"   使用selector: {ad_selector}")
                        
                        scroll_result = page.evaluate(
                            """
                            (sel) => {
                                console.log('🎯 開始置中計算，selector:', sel);
                                const el = document.querySelector(sel);
                                if (!el) {
                                    console.error('❌ 找不到廣告元素');
                                    return { success: false, error: '找不到元素' };
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
                                
                                console.log('📊 置中計算結果:', result);
                                
                                // 執行滾動
                                window.scrollTo({ top: Math.max(0, targetScrollY), behavior: 'instant' });
                                
                                // 檢查滾動後的位置
                                const newRect = el.getBoundingClientRect();
                                result.afterTop = newRect.top;
                                result.actualScrollY = window.pageYOffset;
                                
                                console.log('✅ 滾動執行完成，最終位置:', {
                                    afterTop: result.afterTop,
                                    actualScrollY: result.actualScrollY
                                });
                                
                                return result;
                            }
                            """,
                            ad_selector
                        )
                        
                        if scroll_result['success']:
                            logger.info("✅ 步驟3完成: 置中滾動已執行")
                            logger.info(f"   📊 滾動前元素距頂部: {scroll_result['beforeTop']}px")
                            logger.info(f"   📊 滾動後元素距頂部: {scroll_result['afterTop']}px")
                            logger.info(f"   📊 目標滾動位置: {scroll_result['targetScrollY']}px")
                            logger.info(f"   📊 實際滾動位置: {scroll_result['actualScrollY']}px")
                        else:
                            logger.error(f"❌ 步驟3失敗: {scroll_result.get('error', '未知錯誤')}")
                            raise RuntimeError("置中滾動失敗")
                        
                        # ── 4. 驗證置中結果 ──
                        logger.info("⏱️  步驟4: 驗證元素是否成功置中...")
                        page.wait_for_timeout(500)  # 等待滾動完成
                        
                        verification_result = page.evaluate(
                            """
                            (sel, tolerance) => {
                                const el = document.querySelector(sel);
                                if (!el) {
                                    return { success: false, error: '驗證時找不到元素' };
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
                                
                                console.log('📏 置中驗證結果:', result);
                                return result;
                            }
                            """,
                            ad_selector,
                            30  # 30px容錯範圍
                        )
                        
                        if verification_result['success']:
                            logger.info("✅ 步驟4完成: 元素已成功置中")
                            logger.info(f"   📏 元素中心點: {verification_result['elementMiddle']:.1f}px")
                            logger.info(f"   📏 視窗中心點: {verification_result['viewportMiddle']:.1f}px")
                            logger.info(f"   📏 偏差距離: {verification_result['distance']:.1f}px")
                        else:
                            logger.warning("⚠️  步驟4警告: 元素未完全置中，但繼續進行")
                            logger.info(f"   📏 偏差距離: {verification_result['distance']:.1f}px (容錯: 30px)")
                        
                        # ── 5. 等待廣告完全載入 ──
                        logger.info("🔄 步驟5: 等待廣告完全載入...")
                        page.wait_for_timeout(1500)
                        logger.info("✅ 步驟5完成: 廣告載入等待結束")
                        logger.info("🎉 1200×628 廣告元素置中流程全部完成!")
                        
                    except PwTimeout as te:
                        logger.warning(f"⏰ Timeout錯誤: {te} → 使用fallback滾動")
                        page.mouse.wheel(0, scroll_distance)
                        page.wait_for_timeout(1500)
                    except Exception as e:
                        logger.warning(f"❌ 1200×628 置中流程失敗: {e} → 使用fallback滾動")
                        page.mouse.wheel(0, scroll_distance)
                        page.wait_for_timeout(1500)
                
                if template == 'moptt':
                    # 用滑鼠滾輪，MoPTT 不會把它復原，且 lazy-load 仍能觸發
                    logger.info("🏷️  MoPTT模板 - 使用滑鼠滾輪滾動")
                    page.mouse.wheel(0, scroll_distance)
                    logger.info("✅ MoPTT滑鼠滾輪滾動完成")

                else:
                    # 其他網站保持原來的做法
                    logger.info("🏷️  標準模板 - 使用window.scrollTo滾動")
                    page.evaluate(f"window.scrollTo(0, {scroll_distance})")
                    logger.info("✅ 標準滾動完成")

                # 等待滾動完成（1200x628 除外，因為已經用 wait_for_function 確認）
                if not (size == '1200x628' and template in ['ptt-article']):
                    logger.info("⏳ 等待滾動完成...")
                    page.wait_for_timeout(1000)
                    logger.info("✅ 滾動流程完成")
            except Exception as page_error:
                logger.warning(f"頁面載入過程中發生警告: {str(page_error)}")
                
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
                        'error': f'頁面在載入過程中被關閉 ({template} {size})',
                        'detail': '頁面載入時關閉'
                    }), 500
                else:
                    try:
                        page.goto(url, wait_until='load', timeout=1000)
                    except Exception as retry_error:
                        logger.error(f"重新載入也失敗: {str(retry_error)}，繼續進行截圖")
            
            # 如果設定了滾動距離，則向下滾動到廣告區域
            if scroll_distance > 0:
                logger.info(f"🎲 開始滾動流程，距離: {scroll_distance}px")

                # 特殊處理 1200x628 尺寸：滾動到廣告元素並置中
                if size == '1200x628' and template in ['ptt-article']:
                    logger.info("🎯 1200x628 → 開始廣告元素置中流程")
                    try:
                        # ------ 新的 1200x628 廣告元素置中流程 ------
                        
                        # ── 1. 等待頁面和廣告載入 ──
                        logger.info("📱 步驟1: 等待頁面和廣告載入...")
                        page.wait_for_timeout(2000)  # 給廣告更多載入時間
                        logger.info("✅ 步驟1完成: 等待時間結束")
                        
                        # ── 2. 搜尋目標元素 ──
                        logger.info("🔍 步驟2: 搜尋「觀看更多」按鈕元素...")
                        ad_container_found = False
                        ad_selector = None
                        
                        # 嘗試不同的廣告容器selector
                        selectors_to_try = [
                            'button[class*="_platform_tk_text-sm"]',      # 包含特定 class 的按鈕
                            'button[style*="width: 100px"]',            # 包含特定寬度的按鈕
                            'button[class*="_platform_tk_bg-black"]',     # 包含黑色背景class的按鈕
                            '#platform-ad-ptt-article-middle',              # 備用：原廣告容器
                            'div[data-platform-id]',                        # 備用：通用platform容器
                            'iframe[src*="/1200x628"]',                 # 備用：1200x628廣告iframe
                            'iframe[src*="tkcatrun"]',                  # 備用：catrun iframe
                            'iframe[title="Advertisement"]',             # 備用：廣告iframe
                            '[data-platform-ad]'                            # 備用：platform廣告屬性
                        ]
                        
                        for i, selector in enumerate(selectors_to_try, 1):
                            logger.info(f"   🔎 嘗試selector {i}/{len(selectors_to_try)}: {selector}")
                            try:
                                elements = page.locator(selector)
                                count = elements.count()
                                logger.info(f"   📊 找到{count}個匹配元素")
                                
                                if count > 0:
                                    # 記錄找到的元素詳情
                                    element = elements.first
                                    try:
                                        element_id = element.get_attribute("id") or "無id"
                                        element_class = element.get_attribute("class") or "無class"
                                        tag_name = element.evaluate("el => el.tagName")
                                        logger.info(f"   ✅ 找到目標元素: <{tag_name}> id='{element_id}' class='{element_class}'")
                                        
                                        # 檢查元素是否可見
                                        is_visible = element.is_visible()
                                        logger.info(f"   👁️  元素可見性: {is_visible}")
                                        
                                        if is_visible:
                                            ad_selector = selector
                                            ad_container_found = True
                                            logger.info(f"✅ 步驟2完成: 將使用selector '{selector}'")
                                            break
                                        else:
                                            logger.info(f"   ⚠️  元素不可見，嘗試下一個selector")
                                            
                                    except Exception as element_error:
                                        logger.warning(f"   ⚠️  無法取得元素詳情: {element_error}")
                                else:
                                    logger.info(f"   ❌ 無匹配元素")
                                    
                            except Exception as selector_error:
                                logger.warning(f"   ⚠️  selector錯誤: {selector_error}")
                        
                        if not ad_container_found:
                            logger.error("❌ 步驟2失敗: 未找到任何可見的目標元素")
                            raise RuntimeError("未找到目標元素")
                        
                        # ── 3. 計算並執行置中滾動 ──
                        logger.info("📐 步驟3: 計算並執行置中滾動...")
                        logger.info(f"   使用selector: {ad_selector}")
                        
                        scroll_result = page.evaluate(
                            """
                            (sel) => {
                                console.log('🎯 開始置中計算，selector:', sel);
                                const el = document.querySelector(sel);
                                if (!el) {
                                    console.error('❌ 找不到廣告元素');
                                    return { success: false, error: '找不到元素' };
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
                                
                                console.log('📊 置中計算結果:', result);
                                
                                // 執行滾動
                                window.scrollTo({ top: Math.max(0, targetScrollY), behavior: 'instant' });
                                
                                // 檢查滾動後的位置
                                const newRect = el.getBoundingClientRect();
                                result.afterTop = newRect.top;
                                result.actualScrollY = window.pageYOffset;
                                
                                console.log('✅ 滾動執行完成，最終位置:', {
                                    afterTop: result.afterTop,
                                    actualScrollY: result.actualScrollY
                                });
                                
                                return result;
                            }
                            """,
                            ad_selector
                        )
                        
                        if scroll_result['success']:
                            logger.info("✅ 步驟3完成: 置中滾動已執行")
                            logger.info(f"   📊 滾動前元素距頂部: {scroll_result['beforeTop']}px")
                            logger.info(f"   📊 滾動後元素距頂部: {scroll_result['afterTop']}px")
                            logger.info(f"   📊 目標滾動位置: {scroll_result['targetScrollY']}px")
                            logger.info(f"   📊 實際滾動位置: {scroll_result['actualScrollY']}px")
                        else:
                            logger.error(f"❌ 步驟3失敗: {scroll_result.get('error', '未知錯誤')}")
                            raise RuntimeError("置中滾動失敗")
                        
                        # ── 4. 驗證置中結果 ──
                        logger.info("⏱️  步驟4: 驗證元素是否成功置中...")
                        page.wait_for_timeout(500)  # 等待滾動完成
                        
                        verification_result = page.evaluate(
                            """
                            (sel, tolerance) => {
                                const el = document.querySelector(sel);
                                if (!el) {
                                    return { success: false, error: '驗證時找不到元素' };
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
                                
                                console.log('📏 置中驗證結果:', result);
                                return result;
                            }
                            """,
                            ad_selector,
                            30  # 30px容錯範圍
                        )
                        
                        if verification_result['success']:
                            logger.info("✅ 步驟4完成: 元素已成功置中")
                            logger.info(f"   📏 元素中心點: {verification_result['elementMiddle']:.1f}px")
                            logger.info(f"   📏 視窗中心點: {verification_result['viewportMiddle']:.1f}px")
                            logger.info(f"   📏 偏差距離: {verification_result['distance']:.1f}px")
                        else:
                            logger.warning("⚠️  步驟4警告: 元素未完全置中，但繼續進行")
                            logger.info(f"   📏 偏差距離: {verification_result['distance']:.1f}px (容錯: 30px)")
                        
                        # ── 5. 等待廣告完全載入 ──
                        logger.info("🔄 步驟5: 等待廣告完全載入...")
                        page.wait_for_timeout(1500)
                        logger.info("✅ 步驟5完成: 廣告載入等待結束")
                        logger.info("🎉 1200×628 廣告元素置中流程全部完成!")
                        
                    except PwTimeout as te:
                        logger.warning(f"⏰ Timeout錯誤: {te} → 使用fallback滾動")
                        page.mouse.wheel(0, scroll_distance)
                        page.wait_for_timeout(1500)
                    except Exception as e:
                        logger.warning(f"❌ 1200×628 置中流程失敗: {e} → 使用fallback滾動")
                        page.mouse.wheel(0, scroll_distance)
                        page.wait_for_timeout(1500)

                # 特殊處理 300x250 尺寸：滾動到「立即申請」按鈕並置中
                elif size == '300x250' and template == 'moptt':
                    logger.info("🎯 300x250 → 開始「立即申請」按鈕置中流程")
                    try:
                        # ── 1. 等待頁面和廣告載入 ──
                        logger.info("📱 步驟1: 等待頁面和廣告載入...")
                        page.wait_for_timeout(2000)
                        logger.info("✅ 步驟1完成: 等待時間結束")
                        
                        # ── 2. 搜尋「立即申請」按鈕元素 ──
                        logger.info("🔍 步驟2: 搜尋「立即申請」按鈕元素...")
                        button_found = False
                        button_selector = None
                        
                        # 嘗試不同的按鈕selector
                        button_selectors_to_try = [
                            'button:has-text("立即申請")',               # 最精準：包含"立即申請"文字的按鈕
                            'button[class*="_platform_tk_text-sm"]',      # 包含特定 class 的按鈕
                            'button[style*="width: 100px"]',            # 包含特定寬度的按鈕
                            'button[class*="_platform_tk_bg-black"]',     # 包含黑色背景class的按鈕
                            'div[class*="_platform_tk_justify-end"] button', # 在justify-end容器內的按鈕
                            'div[data-platform-id] button',                 # platform容器內的按鈕
                            'iframe[src*="/300x250"]',                  # 備用：300x250廣告iframe
                            'iframe[src*="tkcatrun"]',                  # 備用：catrun iframe
                            '[data-platform-ad]'                            # 備用：platform廣告屬性
                        ]
                        
                        for i, selector in enumerate(button_selectors_to_try, 1):
                            logger.info(f"   🔎 嘗試selector {i}/{len(button_selectors_to_try)}: {selector}")
                            try:
                                elements = page.locator(selector)
                                count = elements.count()
                                logger.info(f"   📊 找到{count}個匹配元素")
                                
                                if count > 0:
                                    # 記錄找到的元素詳情
                                    element = elements.first
                                    try:
                                        element_id = element.get_attribute("id") or "無id"
                                        element_class = element.get_attribute("class") or "無class"
                                        tag_name = element.evaluate("el => el.tagName")
                                        element_text = element.text_content() or "無文字"
                                        logger.info(f"   ✅ 找到目標元素: <{tag_name}> id='{element_id}' class='{element_class}' text='{element_text}'")
                                        
                                        # 檢查元素是否可見
                                        is_visible = element.is_visible()
                                        logger.info(f"   👁️  元素可見性: {is_visible}")
                                        
                                        if is_visible:
                                            button_selector = selector
                                            button_found = True
                                            logger.info(f"✅ 步驟2完成: 將使用selector '{selector}'")
                                            break
                                        else:
                                            logger.info(f"   ⚠️  元素不可見，嘗試下一個selector")
                                            
                                    except Exception as element_error:
                                        logger.warning(f"   ⚠️  無法取得元素詳情: {element_error}")
                                else:
                                    logger.info(f"   ❌ 無匹配元素")
                                    
                            except Exception as selector_error:
                                logger.warning(f"   ⚠️  selector錯誤: {selector_error}")
                        
                        if not button_found:
                            logger.error("❌ 步驟2失敗: 未找到任何可見的「立即申請」按鈕")
                            raise RuntimeError("未找到立即申請按鈕")
                        
                        # ── 3. 計算並執行置中滾動 ──
                        logger.info("📐 步驟3: 計算並執行置中滾動...")
                        logger.info(f"   使用selector: {button_selector}")
                        
                        scroll_result = page.evaluate(
                            """
                            (sel) => {
                                console.log('🎯 開始置中計算，selector:', sel);
                                const el = document.querySelector(sel);
                                if (!el) {
                                    console.error('❌ 找不到按鈕元素');
                                    return { success: false, error: '找不到元素' };
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
                                
                                console.log('📊 置中計算結果:', result);
                                
                                // 執行滾動
                                window.scrollTo({ top: Math.max(0, targetScrollY), behavior: 'instant' });
                                
                                // 檢查滾動後的位置
                                const newRect = el.getBoundingClientRect();
                                result.afterTop = newRect.top;
                                result.actualScrollY = window.pageYOffset;
                                
                                console.log('✅ 滾動執行完成，最終位置:', {
                                    afterTop: result.afterTop,
                                    actualScrollY: result.actualScrollY
                                });
                                
                                return result;
                            }
                            """,
                            button_selector
                        )
                        
                        if scroll_result['success']:
                            logger.info("✅ 步驟3完成: 置中滾動已執行")
                            logger.info(f"   📊 滾動前元素距頂部: {scroll_result['beforeTop']}px")
                            logger.info(f"   📊 滾動後元素距頂部: {scroll_result['afterTop']}px")
                            logger.info(f"   📊 目標滾動位置: {scroll_result['targetScrollY']}px")
                            logger.info(f"   📊 實際滾動位置: {scroll_result['actualScrollY']}px")
                        else:
                            logger.error(f"❌ 步驟3失敗: {scroll_result.get('error', '未知錯誤')}")
                            raise RuntimeError("置中滾動失敗")
                        
                        # ── 4. 驗證置中結果 ──
                        logger.info("⏱️  步驟4: 驗證按鈕是否成功置中...")
                        page.wait_for_timeout(500)  # 等待滾動完成
                        
                        verification_result = page.evaluate(
                            """
                            (sel, tolerance) => {
                                const el = document.querySelector(sel);
                                if (!el) {
                                    return { success: false, error: '驗證時找不到元素' };
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
                                
                                console.log('📏 置中驗證結果:', result);
                                return result;
                            }
                            """,
                            button_selector,
                            30  # 30px容錯範圍
                        )
                        
                        if verification_result['success']:
                            logger.info("✅ 步驟4完成: 按鈕已成功置中")
                            logger.info(f"   📏 按鈕中心點: {verification_result['elementMiddle']:.1f}px")
                            logger.info(f"   📏 視窗中心點: {verification_result['viewportMiddle']:.1f}px")
                            logger.info(f"   📏 偏差距離: {verification_result['distance']:.1f}px")
                        else:
                            logger.warning("⚠️  步驟4警告: 按鈕未完全置中，但繼續進行")
                            logger.info(f"   📏 偏差距離: {verification_result['distance']:.1f}px (容錯: 30px)")
                        
                        # ── 5. 等待廣告完全載入 ──
                        logger.info("🔄 步驟5: 等待廣告完全載入...")
                        page.wait_for_timeout(1500)
                        logger.info("✅ 步驟5完成: 廣告載入等待結束")
                        logger.info("🎉 300×250「立即申請」按鈕置中流程全部完成!")
                        
                    except PwTimeout as te:
                        logger.warning(f"⏰ Timeout錯誤: {te} → 使用fallback滾動")
                        page.mouse.wheel(0, scroll_distance)
                        page.wait_for_timeout(1500)
                    except Exception as e:
                        logger.warning(f"❌ 300×250 置中流程失敗: {e} → 使用fallback滾動")
                        page.mouse.wheel(0, scroll_distance)
                        page.wait_for_timeout(1500)

                elif template in ['ptt-article', 'ptt-article-list']:
                    # PTT預覽頁面，嘗試在iframe內滾動
                    logger.info("🏷️  PTT模板 - 嘗試iframe內滾動")
                    try:
                        # 首先檢查iframe是否存在
                        logger.info("🔍 檢查ptt-viewer iframe是否存在...")
                        ptt_iframe_count = page.locator('iframe#ptt-viewer').count()
                        logger.info(f"📊 找到{ptt_iframe_count}個ptt-viewer iframe")
                        
                        if ptt_iframe_count > 0:
                            # 取得iframe的實際Frame物件
                            logger.info("📦 取得iframe Frame物件...")
                            iframe_element = page.locator('iframe#ptt-viewer').first
                            frame = iframe_element.content_frame()
                            
                            if frame:
                                logger.info("✅ 成功取得iframe Frame物件")
                                logger.info(f"🎲 在iframe內執行滾動: {scroll_distance}px")
                                frame.evaluate(f"window.scrollTo(0, {scroll_distance})")
                                logger.info("✅ iframe內滾動成功")
                            else:
                                logger.warning("⚠️  無法取得iframe Frame物件，使用fallback滾動")
                                page.mouse.wheel(0, scroll_distance)
                        else:
                            logger.warning("⚠️  未找到ptt-viewer iframe，使用fallback滾動")
                            page.mouse.wheel(0, scroll_distance)
                            
                    except Exception as e:
                        logger.warning(f"❌ PTT iframe滾動失敗: {e}")
                        logger.info("🔄 使用fallback滾動方案...")
                        page.mouse.wheel(0, scroll_distance)

                elif template == 'moptt':
                    # 用滑鼠滾輪，MoPTT 不會把它復原，且 lazy-load 仍能觸發
                    logger.info("🏷️  MoPTT模板 - 使用滑鼠滾輪滾動")
                    page.mouse.wheel(0, scroll_distance)
                    logger.info("✅ MoPTT滑鼠滾輪滾動完成")

                else:
                    # 其他網站保持原來的做法
                    logger.info("🏷️  標準模板 - 使用window.scrollTo滾動")
                    page.evaluate(f"window.scrollTo(0, {scroll_distance})")
                    logger.info("✅ 標準滾動完成")

                # 等待滾動完成（1200x628和300x250置中流程除外，因為已經有自己的等待）
                if not ((size == '1200x628' and template in ['ptt-article']) or (size == '300x250' and template == 'moptt')):
                    logger.info("⏳ 等待滾動完成...")
                    page.wait_for_timeout(1000)
                    logger.info("✅ 滾動流程完成")
            else:
                logger.info("🚫 未設定滾動距離，跳過滾動")

            # 創建截圖目錄
            today = datetime.now().strftime('%Y%m%d')
            screenshot_dir = os.path.join('uploads', 'screenshots', today)
            if not os.path.exists(screenshot_dir):
                os.makedirs(screenshot_dir)
            
            # 生成檔案名稱
            timestamp = datetime.now().strftime('%H%M%S')
            device_suffix = device.replace('_', '-')
            
            # 特殊處理 1200x628 和 300x250 的檔案名稱
            if size == '1200x628' and template in ['ptt-article']:
                scroll_suffix = 'element-scroll'
            elif size == '300x250' and template == 'moptt':
                scroll_suffix = 'button-scroll'
            else:
                scroll_suffix = f'scroll-{scroll_distance}px' if scroll_distance > 0 else 'no-scroll'
            
            template_suffix = f'_{template}' if template not in ['ptt-article'] else ''
            filename = f'native_{size.replace("x", "_")}_device-{device_suffix}_uuid-{uuid}_{scroll_suffix}{template_suffix}_{timestamp}.png'
            screenshot_path = os.path.join(screenshot_dir, filename)
            
            # 執行截圖
            try:
                page.wait_for_timeout(4000)
                page.screenshot(path=screenshot_path, full_page=False)
                logger.info("截圖操作完成")
                screenshot_success = True
                
            except Exception as screenshot_error:
                logger.error(f"截圖過程中發生錯誤: {str(screenshot_error)}")
                
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
                        'error': f'截圖時頁面已關閉 ({template} {size})',
                        'detail': '頁面已關閉，無法截圖'
                    }), 500
                
                # 重試一次
                try:
                    try:
                        page.close()
                    except:
                        pass
                    
                    page = context.new_page()
                    page.goto(url, wait_until='domcontentloaded', timeout=15000)
                    page.wait_for_timeout(3000)
                    
                    # 重試時也要滾動
                    if scroll_distance > 0:
                        logger.info(f"🔄 重試時開始滾動流程，距離: {scroll_distance}px")

                        # 特殊處理置中流程的重試
                        if size == '1200x628' and template in ['ptt-article']:
                            logger.info("🎯 重試-1200x628 → 簡化置中流程")
                            try:
                                selectors_to_try = [
                                    'button[class*="_platform_tk_text-sm"]',
                                    'button[style*="width: 100px"]',
                                    '#platform-ad-ptt-article-middle',
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
                                        logger.info("✅ 重試-1200x628簡化置中完成")
                                        break
                                else:
                                    page.mouse.wheel(0, scroll_distance)
                            except:
                                page.mouse.wheel(0, scroll_distance)
                        
                        elif size == '300x250' and template == 'moptt':
                            logger.info("🎯 重試-300x250 → 簡化置中流程")
                            try:
                                button_selectors = [
                                    'button:has-text("立即申請")',
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
                                        logger.info("✅ 重試-300x250簡化置中完成")
                                        break
                                else:
                                    page.mouse.wheel(0, scroll_distance)
                            except:
                                page.mouse.wheel(0, scroll_distance)
                        
                        else:
                            # 其他情況使用標準滾動
                            page.mouse.wheel(0, scroll_distance)
                        
                        page.wait_for_timeout(1000)
                    
                    page.screenshot(path=screenshot_path, full_page=False)
                    logger.info("重新截圖成功")
                    screenshot_success = True
                except Exception as retry_screenshot_error:
                    logger.error(f"重新截圖也失敗: {str(retry_screenshot_error)}")
                    raise screenshot_error
            
            # 確保瀏覽器資源被正確清理
            try:
                if hasattr(page, 'is_closed') and not page.is_closed():
                    page.close()
            except:
                pass
            
            try:
                browser.close()
            except:
                pass
            
            # 取得檔案資訊
            absolute_path = os.path.abspath(screenshot_path)
            
            logger.info(f"截圖完成，檔案儲存至: {absolute_path}")
            flash(f'截圖成功！檔案儲存至: {absolute_path}', 'success')
            
            # 將截圖路徑儲存到session，供模板顯示
            session['last_screenshot'] = absolute_path
            session['last_screenshot_device'] = device_config['name']
            session['last_screenshot_full_page'] = False
            session['last_screenshot_scroll_distance'] = scroll_distance
            session['last_screenshot_uuid'] = uuid
            session['last_screenshot_adunit_title'] = adunit_data.get('title', '')
            
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        logger.error(f"Native 廣告截圖時發生錯誤: {str(e)}")
        logger.error(f"錯誤詳情：\n{error_detail}")
        return jsonify({'success': False, 'error': str(e)}), 500

@screenshot_bp.route('/screenshot_base64/<path:filename>')
def screenshot_base64(filename):
    """提供截圖檔案的 base64 編碼"""
    try:
        # 安全檢查：確保檔案路徑在允許的目錄內
        if not filename.startswith('screenshots/'):
            return "Unauthorized", 403
            
        file_path = os.path.join('uploads', filename)
        
        if not os.path.exists(file_path):
            return "File not found", 404
            
        # 讀取檔案並轉換為 base64
        with open(file_path, 'rb') as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
            
        return f"data:image/png;base64,{encoded_string}"
        
    except Exception as e:
        logger.error(f"提供截圖檔案時發生錯誤: {str(e)}")
        return "Internal server error", 500

@screenshot_bp.route('/create-screenshot', methods=['POST'])
def create_screenshot():
    """處理截圖創建"""
    try:
        uuid = request.form.get('uuid', '').strip()
        device = request.form.get('device', 'iphone_x')
        full_page = request.form.get('full_page') == 'true'
        scroll_distance = int(request.form.get('scroll_distance', 4800))
        wait_time = int(request.form.get('wait_time', 3)) * 1000
        
        if not uuid:
            flash('請輸入有效的 UUID', 'error')
            return redirect(url_for('screenshot.auto_screenshot'))
        
        # 從 MongoDB 查詢 AdUnit 資料
        logger.info(f"正在查詢 UUID: {uuid}")
        adunit_data = get_adunit_by_uuid(uuid)
        
        if not adunit_data:
            flash(f'找不到 UUID {uuid} 對應的 AdUnit 資料', 'error')
            return redirect(url_for('screenshot.auto_screenshot'))
        
        # 建構截圖網址
        url = build_screenshot_url(adunit_data)
        if not url:
            flash('無法建構截圖網址', 'error')
            return redirect(url_for('screenshot.auto_screenshot'))
        
        logger.info(f"建構的截圖網址: {url}")
        
        # 裝置尺寸配置
        device_configs = {
            'iphone_x': {'width': 375, 'height': 812, 'name': 'iPhone X'},
            'iphone_se': {'width': 375, 'height': 667, 'name': 'iPhone SE'},
            'iphone_plus': {'width': 414, 'height': 736, 'name': 'iPhone Plus'},
            'android': {'width': 360, 'height': 640, 'name': 'Android 標準'},
            'tablet': {'width': 768, 'height': 1024, 'name': '平板電腦'}
        }
        
        device_config = device_configs.get(device, device_configs['iphone_x'])
        
        default_cookie = os.getenv("PLATFORM_COOKIE", "")
        
        logger.info(f"開始自動截圖，目標網址: {url}, 裝置: {device_config['name']}, 完整頁面: {full_page}, UUID: {uuid}")
        
        # 使用 Playwright 進行截圖
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
            
            # 根據域名設置不同的 cookie
            try:
                parsed_url = urlparse(url)
                domain = parsed_url.netloc
                
                # 為預覽頁設置專用 cookies
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
                    logger.info(f"已為預覽頁設置 {len(cookies)} 個專用 cookies")
                    
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
                    logger.info(f"已設置 {len(cookies)} 個 cookies")
                    
            except Exception as cookie_error:
                logger.warning(f"設置 cookie 時發生錯誤（將繼續不使用 cookie）: {str(cookie_error)}")
            
            page = context.new_page()
            
            # 訪問目標網址，增加超時時間並改善錯誤處理
            try:
                page.goto(url, wait_until='networkidle', timeout=12000)
            except Exception as goto_error:
                logger.warning(f"networkidle 等待超時，嘗試 domcontentloaded: {str(goto_error)}")
                try:
                    page.goto(url, wait_until='domcontentloaded', timeout=8000)
                except Exception as retry_error:
                    logger.warning(f"domcontentloaded 也超時，嘗試基本載入: {str(retry_error)}")
                    page.goto(url, wait_until='commit', timeout=6000)
            
            # 等待頁面載入完成
            page.wait_for_timeout(wait_time)
            
            # 如果設定了滾動距離，則向下滾動到廣告區域
            if scroll_distance > 0:
                logger.info(f"向下滾動 {scroll_distance}px")

                # 根據網址判斷是否為PTT相關頁面
                is_ptt_page = 'ptt' in url.lower() or 'github.io' in url.lower()
                
                if is_ptt_page:
                    # PTT預覽頁面，嘗試在iframe內滾動
                    try:
                        frame = page.frame_locator('iframe#ptt-viewer').first
                        frame.evaluate(f"window.scrollTo(0, {scroll_distance})")
                        logger.info("在PTT iframe內滾動成功")
                    except Exception as e:
                        logger.warning(f"PTT iframe scroll 失敗: {e}")
                        page.mouse.wheel(0, scroll_distance)          # 後援
                else:
                    # 其他網站保持原來的做法
                    page.evaluate(f"window.scrollTo(0, {scroll_distance})")

                # 等待滾動完成
                page.wait_for_timeout(1000)
            
            # 創建截圖目錄
            today = datetime.now().strftime('%Y%m%d')
            screenshot_dir = os.path.join('uploads', 'screenshots', today)
            if not os.path.exists(screenshot_dir):
                os.makedirs(screenshot_dir)
            
            # 生成檔案名稱
            timestamp = datetime.now().strftime('%H%M%S')
            device_suffix = device.replace('_', '-')
            page_type = 'full' if full_page else 'viewport'
            scroll_suffix = f'scroll-{scroll_distance}px' if scroll_distance > 0 else 'no-scroll'
            filename = f'screenshot_{device_suffix}_{page_type}_uuid-{uuid}_{scroll_suffix}_{timestamp}.png'
            screenshot_path = os.path.join(screenshot_dir, filename)
            
            # 截圖，增加重試機制
            screenshot_success = False
            max_retries = 3
            
            for attempt in range(max_retries):
                try:
                    logger.info(f"嘗試截圖 (第 {attempt + 1} 次)")
                    page.screenshot(path=screenshot_path, full_page=full_page)
                    screenshot_success = True
                    logger.info("截圖成功")
                    break
                except Exception as screenshot_error:
                    logger.warning(f"截圖失敗 (第 {attempt + 1} 次): {str(screenshot_error)}")
                    if attempt < max_retries - 1:
                        page.wait_for_timeout(2000)
                    else:
                        logger.error("所有截圖嘗試都失敗了")
                        raise screenshot_error
            
            browser.close()
            
            # 取得絕對路徑
            absolute_path = os.path.abspath(screenshot_path)
            
            logger.info(f"截圖完成，檔案儲存至: {absolute_path}")
            flash(f'截圖成功！檔案儲存至: {absolute_path}', 'success')
            
            # 將截圖路徑儲存到session，供模板顯示
            session['last_screenshot'] = absolute_path
            session['last_screenshot_device'] = device_config['name']
            session['last_screenshot_full_page'] = full_page
            session['last_screenshot_scroll_distance'] = scroll_distance
            session['last_screenshot_uuid'] = uuid
            session['last_screenshot_adunit_title'] = adunit_data.get('title', '')
            
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        logger.error(f"自動截圖時發生錯誤: {str(e)}")
        logger.error(f"錯誤詳情：\n{error_detail}")
        
        # 根據錯誤類型提供更友善的訊息
        if "Timeout" in str(e):
            user_friendly_msg = "網頁載入超時（已嘗試 60 秒），請稍後再試或檢查網址是否正確"
        elif "net::ERR" in str(e):
            user_friendly_msg = "網路連線錯誤，請檢查網址是否可正常訪問"
        elif "screenshot" in str(e).lower():
            user_friendly_msg = "截圖過程發生錯誤，請重新嘗試"
        elif "browser" in str(e).lower() or "chromium" in str(e).lower():
            user_friendly_msg = "瀏覽器啟動失敗，請稍後重試"
        else:
            user_friendly_msg = f"截圖失敗: {str(e)}"
            
        flash(user_friendly_msg, 'error')
    
    return redirect(url_for('screenshot.auto_screenshot')) 
