from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from playwright.sync_api import sync_playwright
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
        
        # 預設 cookie
        default_cookie = "AOTTERBD_SESSION=757418f543a95a889184e798ec5ab66d4fad04e5-lats=1724229220332&sso=PIg4zu/Vdnn/A15vMEimFlVAGliNhoWlVd5FTvtEMRAFpk/VvBGvAetanw8DLATSLexy9pee/t52uNojvoFS2Q==;aotter=eyJ1c2VyIjp7ImlkIjoiNjNkYjRkNDBjOTFiNTUyMmViMjk4YjBkIiwiZW1haWwiOiJpYW4uY2hlbkBhb3R0ZXIubmV0IiwiY3JlYXRlZEF0IjoxNjc1MzE2NTQ0LCJlbWFpbFZlcmlmaWVkIjp0cnVlLCJsZWdhY3lJZCI6bnVsbCwibGVnYWN5U2VxSWQiOjE2NzUzMTY1NDQ3ODI5NzQwMDB9LCJhY2Nlc3NUb2tlbiI6IjJkYjQyZTNkOTM5MDUzMjdmODgyZmYwMDRiZmI4YmEzZjBhNTlmMDQwYzhiN2Y4NGY5MmZmZTIzYTU0ZTQ2MDQiLCJ1ZWEiOm51bGx9; _Secure-1PSID=vlPPgXupFroiSjP1/A02minugZVZDgIG4K; _Secure-1PSIDCC=g.a000mwhavReSVd1vN09AVTswXkPAhyuW7Tgj8-JFhj-FZya9I_l1B6W2gqTIWAtQUTQMkTxoAwACgYKAW0SARISFQHGX2MiC--NJ2PzCzDpJ0m3odxHhxoVAUF8yKr8r49abq8oe4UxCA0t_QCW0076; _Secure-3PSID=AKEyXzUuXI1zywmFmkEBEBHfg6GRkRM9cJ9BiJZxmaR46x5im_krhaPtmL4Jhw8gQsz5uFFkfbc; _Secure-3PSIDCC=sidts-CjEBUFGohzUF6oK3ZMACCk2peoDBDp6djBwJhGc4Lxgu2zOlzbVFeVpXF4q1TYZ5ba6cEAA"
        
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
            
            # 為 aotter.github.io 域名設置特定的 cookies
            if domain == "aotter.github.io":
                try:
                    github_cookie_string = "cf_clearance=tlU5YeqVtd83dMmK0D8IHFYxnf1ke1AZLLUNdlT2Tco-1748308849-1.2.1.1-pBs9egIQSSuk2aLstBcdPGPyEflNUhEqwzK_M.E8w_tqtQY2ipsJXGj6_JoBWktklctTACwdQyCuF2kfKPlBGHa3Um.OTdIkrEt_7TQ6mtm4axyyK_B7nzW.2m6HpH.u6r_J6ybaShQq3DuyG1N_rPeYTyoD8YEj5yJnWR92U39AbL2FZb19se8mg2Zsk56vy6RfwnFGbIqQKIVnC7U7SS1ESGUFudxpkIZoXP_UtfzVbKaQIa_fUu9_KUCxusZ2jjMKnnSkRUHVM2rg.ObZxjqLNdG1YluIt6PeEUsTClTB2pWs7hf5CAkt6uACsC83HtJmrV__.rS2xf8VoomnQrtklFQzcfWUTNJ4uRdYWQo;ar_debug=1;TREK_SESSION=2d139516-31b7-477b-2dba-e31c4e5e72b1"
                    
                    cookies = []
                    cookie_pairs = github_cookie_string.split(';')
                    
                    for pair in cookie_pairs:
                        if '=' in pair:
                            name, value = pair.split('=', 1)
                            name = name.strip()
                            value = value.strip()
                            
                            if name == 'cf_clearance':
                                cookie_domain = domain
                            elif name == 'ar_debug':
                                cookie_domain = domain
                            elif name == 'TREK_SESSION':
                                cookie_domain = '.aotter.net'
                            else:
                                cookie_domain = domain
                            
                            cookies.append({
                                'name': name,
                                'value': value,
                                'domain': cookie_domain,
                                'path': '/',
                                'secure': False,
                                'httpOnly': False
                            })
                    
                    context.add_cookies(cookies)
                    logger.info(f"已為 aotter.github.io 設置 {len(cookies)} 個專用 cookies")
                    
                except Exception as cookie_error:
                    logger.warning(f"設置 aotter.github.io cookies 時發生錯誤（將繼續不使用 cookie）: {str(cookie_error)}")
            
            # 對於 aotter 相關網址設置預設 cookies
            elif (".aotter.net" in domain or "trek.aotter.net" == domain):
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
                                cookie_domain = '.aotter.net' if 'aotter.net' in domain else domain
                            
                            cookies.append({
                                'name': name,
                                'value': value,
                                'domain': cookie_domain,
                                'path': '/',
                                'secure': name.startswith('_Secure-') or 'PSID' in name,
                                'httpOnly': False
                            })
                    
                    context.add_cookies(cookies)
                    logger.info(f"已為 aotter 網域設置 {len(cookies)} 個 cookies")
                    
                except Exception as cookie_error:
                    logger.warning(f"設置 cookie 時發生錯誤（將繼續不使用 cookie）: {str(cookie_error)}")
            else:
                logger.info(f"外部網址 {domain}，跳過 cookie 設置")
            
            try:
                # 根據不同網站使用不同的載入策略
                if template == 'moptt' and size == '300x250':
                    page.goto(url, wait_until='domcontentloaded', timeout=2000)
                    page.wait_for_timeout(1000)

                elif template == 'pnn-article' and size == '640x200':
                    # 簡化的 640x200 處理 - 移除降速和大量 log
                    page.goto(url, wait_until='commit', timeout=6000)
                    page.wait_for_timeout(3000)
                    
                    # 簡單等待廣告載入
                    try:
                        page.wait_for_selector('#trek-ad-pnn-article', timeout=2000)
                    except:
                        try:
                            page.wait_for_selector('div[data-trek-id]', timeout=1000)
                        except:
                            pass
                    
                    page.wait_for_timeout(2000)
                    
                else: # Aotter 內部頁面或其他
                    page.goto(url, wait_until='networkidle', timeout=3000)
                    page.wait_for_timeout(1000)
                    
                    try:
                        if template == 'pnn-article':
                            page.wait_for_selector('#trek-ad-pnn-article', timeout=2000)
                        else:
                            page.wait_for_selector('[data-trek-ad]', timeout=2000)
                    except:
                        logger.warning(f"頁面 ({template}): 未找到廣告容器，繼續進行截圖")
                
                
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
                logger.info(f"向下滾動 {scroll_distance}px")

                if template in ['ptt-article', 'ptt-article-list']:
                    # 1️⃣ 先抓到 preview iframe
                    try:
                        frame = page.frame_locator('iframe#ptt-viewer').first
                        frame.evaluate(f"window.scrollTo(0, {scroll_distance})")
                    except Exception as e:
                        logger.warning(f"PTT iframe scroll 失敗: {e}")
                        page.mouse.wheel(0, scroll_distance)          # 後援

                elif template == 'moptt':
                    # 2️⃣ 用滑鼠滾輪，MoPTT 不會把它復原，且 lazy-load 仍能觸發
                    page.mouse.wheel(0, scroll_distance)

                else:
                    # 3️⃣ 其他網站保持原來的做法
                    page.evaluate(f"window.scrollTo(0, {scroll_distance})")

                page.wait_for_timeout(1000)
            
            # 創建截圖目錄
            today = datetime.now().strftime('%Y%m%d')
            screenshot_dir = os.path.join('uploads', 'screenshots', today)
            if not os.path.exists(screenshot_dir):
                os.makedirs(screenshot_dir)
            
            # 生成檔案名稱
            timestamp = datetime.now().strftime('%H%M%S')
            device_suffix = device.replace('_', '-')
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
                        logger.info(f"重試截圖時向下滾動 {scroll_distance}px")

                        if template in ['ptt-article', 'ptt-article-list']:
                            # 1️⃣ 先抓到 preview iframe
                            try:
                                frame = page.frame_locator('iframe#ptt-viewer').first
                                frame.evaluate(f"window.scrollTo(0, {scroll_distance})")
                            except Exception as e:
                                logger.warning(f"重試時 PTT iframe scroll 失敗: {e}")
                                page.mouse.wheel(0, scroll_distance)          # 後援

                        elif template == 'moptt':
                            # 2️⃣ 用滑鼠滾輪，MoPTT 不會把它復原，且 lazy-load 仍能觸發
                            page.mouse.wheel(0, scroll_distance)

                        else:
                            # 3️⃣ 其他網站保持原來的做法
                            page.evaluate(f"window.scrollTo(0, {scroll_distance})")

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
            
            # 安全獲取檔案大小
            try:
                file_size = os.path.getsize(absolute_path)
            except:
                file_size = 0
            
            # 格式化檔案大小
            if file_size > 1024 * 1024:
                file_size_str = f"{file_size / (1024 * 1024):.1f}MB"
            elif file_size > 1024:
                file_size_str = f"{file_size / 1024:.1f}KB"
            else:
                file_size_str = f"{file_size}B"
            
            logger.info(f"截圖完成，檔案儲存至: {absolute_path}")
            
            # 計算相對路徑供前端使用
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
        
        # 預設 cookie（用於 aotter 相關網站）
        default_cookie = "AOTTERBD_SESSION=757418f543a95a889184e798ec5ab66d4fad04e5-lats=1724229220332&sso=PIg4zu/Vdnn/A15vMEimFlVAGliNhoWlVd5FTvtEMRAFpk/VvBGvAetanw8DLATSLexy9pee/t52uNojvoFS2Q==;aotter=eyJ1c2VyIjp7ImlkIjoiNjNkYjRkNDBjOTFiNTUyMmViMjk4YjBkIiwiZW1haWwiOiJpYW4uY2hlbkBhb3R0ZXIubmV0IiwiY3JlYXRlZEF0IjoxNjc1MzE2NTQ0LCJlbWFpbFZlcmlmaWVkIjp0cnVlLCJsZWdhY3lJZCI6bnVsbCwibGVnYWN5U2VxSWQiOjE2NzUzMTY1NDQ3ODI5NzQwMDB9LCJhY2Nlc3NUb2tlbiI6IjJkYjQyZTNkOTM5MDUzMjdmODgyZmYwMDRiZmI4YmEzZjBhNTlmMDQwYzhiN2Y4NGY5MmZmZTIzYTU0ZTQ2MDQiLCJ1ZWEiOm51bGx9; _Secure-1PSID=vlPPgXupFroiSjP1/A02minugZVZDgIG4K; _Secure-1PSIDCC=g.a000mwhavReSVd1vN09AVTswXkPAhyuW7Tgj8-JFhj-FZya9I_l1B6W2gqTIWAtQUTQMkTxoAwACgYKAW0SARISFQHGX2MiC--NJ2PzCzDpJ0m3odxHhxoVAUF8yKr8r49abq8oe4UxCA0t_QCW0076; _Secure-3PSID=AKEyXzUuXI1zywmFmkEBEBHfg6GRkRM9cJ9BiJZxmaR46x5im_krhaPtmL4Jhw8gQsz5uFFkfbc; _Secure-3PSIDCC=sidts-CjEBUFGohzUF6oK3ZMACCk2peoDBDp6djBwJhGc4Lxgu2zOlzbVFeVpXF4q1TYZ5ba6cEAA"
        
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
                
                # 為 aotter.github.io 域名設置特定的 cookies
                if domain == "aotter.github.io":
                    github_cookie_string = "cf_clearance=tlU5YeqVtd83dMmK0D8IHFYxnf1ke1AZLLUNdlT2Tco-1748308849-1.2.1.1-pBs9egIQSSuk2aLstBcdPGPyEflNUhEqwzK_M.E8w_tqtQY2ipsJXGj6_JoBWktklctTACwdQyCuF2kfKPlBGHa3Um.OTdIkrEt_7TQ6mtm4axyyK_B7nzW.2m6HpH.u6r_J6ybaShQq3DuyG1N_rPeYTyoD8YEj5yJnWR92U39AbL2FZb19se8mg2Zsk56vy6RfwnFGbIqQKIVnC7U7SS1ESGUFudxpkIZoXP_UtfzVbKaQIa_fUu9_KUCxusZ2jjMKnnSkRUHVM2rg.ObZxjqLNdG1YluIt6PeEUsTClTB2pWs7hf5CAkt6uACsC83HtJmrV__.rS2xf8VoomnQrtklFQzcfWUTNJ4uRdYWQo;ar_debug=1;TREK_SESSION=2d139516-31b7-477b-2dba-e31c4e5e72b1"
                    
                    cookies = []
                    cookie_pairs = github_cookie_string.split(';')
                    
                    for pair in cookie_pairs:
                        if '=' in pair:
                            name, value = pair.split('=', 1)
                            name = name.strip()
                            value = value.strip()
                            
                            if name == 'cf_clearance':
                                cookie_domain = domain
                            elif name == 'ar_debug':
                                cookie_domain = domain
                            elif name == 'TREK_SESSION':
                                cookie_domain = '.aotter.net'
                            else:
                                cookie_domain = domain
                            
                            cookies.append({
                                'name': name,
                                'value': value,
                                'domain': cookie_domain,
                                'path': '/',
                                'secure': False,
                                'httpOnly': False
                            })
                    
                    context.add_cookies(cookies)
                    logger.info(f"已為 aotter.github.io 設置 {len(cookies)} 個專用 cookies")
                    
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
                                if 'aotter' in domain or 'trek' in domain:
                                    cookie_domain = '.aotter.net' if 'aotter.net' in domain else domain
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
                page.goto(url, wait_until='networkidle', timeout=6000)
            except Exception as goto_error:
                logger.warning(f"networkidle 等待超時，嘗試 domcontentloaded: {str(goto_error)}")
                try:
                    page.goto(url, wait_until='domcontentloaded', timeout=2000)
                except Exception as retry_error:
                    logger.warning(f"domcontentloaded 也超時，嘗試基本載入: {str(retry_error)}")
                    page.goto(url, wait_until='commit', timeout=3000)
            
            # 等待頁面載入完成
            page.wait_for_timeout(wait_time)
            
            # 如果設定了滾動距離，則向下滾動到廣告區域
            if scroll_distance > 0:
                logger.info(f"向下滾動 {scroll_distance}px")

                if template in ['ptt-article', 'ptt-article-list']:
                    # 1️⃣ 先抓到 preview iframe
                    try:
                        frame = page.frame_locator('iframe#ptt-viewer').first
                        frame.evaluate(f"window.scrollTo(0, {scroll_distance})")
                    except Exception as e:
                        logger.warning(f"PTT iframe scroll 失敗: {e}")
                        page.mouse.wheel(0, scroll_distance)          # 後援

                elif template == 'moptt':
                    # 2️⃣ 用滑鼠滾輪，MoPTT 不會把它復原，且 lazy-load 仍能觸發
                    page.mouse.wheel(0, scroll_distance)

                else:
                    # 3️⃣ 其他網站保持原來的做法
                    page.evaluate(f"window.scrollTo(0, {scroll_distance})")

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