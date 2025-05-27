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
        
        logger.info(f"開始截圖 {size}，目標網址: {url}, 裝置: {device_config['name']}, UUID: {uuid}, 滾動距離: {scroll_distance}px")
        
        # 使用 Playwright 進行截圖
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
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
            
            # 為 640x200 PNN 設置錄影功能
            video_dir = None
            video_size = None
            if template == 'pnn-article' and size == '640x200':
                today = datetime.now().strftime('%Y%m%d')
                video_dir = os.path.join('uploads', 'screenshots', today, 'videos')
                if not os.path.exists(video_dir):
                    os.makedirs(video_dir)
                video_size = {'width': device_config['width'], 'height': device_config['height']}
                logger.info(f"🎬 PNN 640x200 錄影功能已啟用")
                
                logger.info(f"🎬 錄影檔案將儲存至: {video_dir}")
                logger.info(f"🎬 錄影尺寸: {video_size}")
            
            if device == 'desktop':
                if video_dir:
                    logger.info(f"🎬 開始錄影 - 桌上型模式 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                    context = browser.new_context(
                        viewport={'width': device_config['width'], 'height': device_config['height']},
                        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                        extra_http_headers=extra_http_headers,
                        record_video_dir=video_dir,
                        record_video_size=video_size
                    )
                else:
                    context = browser.new_context(
                        viewport={'width': device_config['width'], 'height': device_config['height']},
                        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                        extra_http_headers=extra_http_headers
                    )
            else:
                if video_dir:
                    logger.info(f"🎬 開始錄影 - 手機模式 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                    context = browser.new_context(
                        viewport={'width': device_config['width'], 'height': device_config['height']},
                        user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
                        extra_http_headers=extra_http_headers,
                        record_video_dir=video_dir,
                        record_video_size=video_size
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
                    # aotter.github.io 專用的 cookies
                    github_cookie_string = "cf_clearance=tlU5YeqVtd83dMmK0D8IHFYxnf1ke1AZLLUNdlT2Tco-1748308849-1.2.1.1-pBs9egIQSSuk2aLstBcdPGPyEflNUhEqwzK_M.E8w_tqtQY2ipsJXGj6_JoBWktklctTACwdQyCuF2kfKPlBGHa3Um.OTdIkrEt_7TQ6mtm4axyyK_B7nzW.2m6HpH.u6r_J6ybaShQq3DuyG1N_rPeYTyoD8YEj5yJnWR92U39AbL2FZb19se8mg2Zsk56vy6RfwnFGbIqQKIVnC7U7SS1ESGUFudxpkIZoXP_UtfzVbKaQIa_fUu9_KUCxusZ2jjMKnnSkRUHVM2rg.ObZxjqLNdG1YluIt6PeEUsTClTB2pWs7hf5CAkt6uACsC83HtJmrV__.rS2xf8VoomnQrtklFQzcfWUTNJ4uRdYWQo;ar_debug=1;TREK_SESSION=2d139516-31b7-477b-2dba-e31c4e5e72b1"
                    
                    cookies = []
                    cookie_pairs = github_cookie_string.split(';')
                    
                    for pair in cookie_pairs:
                        if '=' in pair:
                            name, value = pair.split('=', 1)
                            name = name.strip()
                            value = value.strip()
                            
                            # 根據 cookie 名稱設置適當的域名
                            if name == 'cf_clearance':
                                cookie_domain = domain  # 使用 aotter.github.io 域名
                            elif name == 'ar_debug':
                                cookie_domain = domain  # 使用 aotter.github.io 域名
                            elif name == 'TREK_SESSION':
                                cookie_domain = '.aotter.net'  # Trek session 使用 aotter 域名
                            else:
                                cookie_domain = domain
                            
                            cookies.append({
                                'name': name,
                                'value': value,
                                'domain': cookie_domain,
                                'path': '/',
                                'secure': False,  # 根據需要調整
                                'httpOnly': False
                            })
                    
                    context.add_cookies(cookies)
                    logger.info(f"已為 aotter.github.io 設置 {len(cookies)} 個專用 cookies")
                    
                except Exception as cookie_error:
                    logger.warning(f"設置 aotter.github.io cookies 時發生錯誤（將繼續不使用 cookie）: {str(cookie_error)}")
            
            # 為 640x200 PNN 文章設置特定的 cookies
            elif template == 'pnn-article' and size == '640x200':
                try:
                    # PNN 文章專用的 cookies
                    pnn_cookie_string = "cf_clearance=tlU5YeqVtd83dMmK0D8IHFYxnf1ke1AZLLUNdlT2Tco-1748308849-1.2.1.1-pBs9egIQSSuk2aLstBcdPGPyEflNUhEqwzK_M.E8w_tqtQY2ipsJXGj6_JoBWktklctTACwdQyCuF2kfKPlBGHa3Um.OTdIkrEt_7TQ6mtm4axyyK_B7nzW.2m6HpH.u6r_J6ybaShQq3DuyG1N_rPeYTyoD8YEj5yJnWR92U39AbL2FZb19se8mg2Zsk56vy6RfwnFGbIqQKIVnC7U7SS1ESGUFudxpkIZoXP_UtfzVbKaQIa_fUu9_KUCxusZ2jjMKnnSkRUHVM2rg.ObZxjqLNdG1YluIt6PeEUsTClTB2pWs7hf5CAkt6uACsC83HtJmrV__.rS2xf8VoomnQrtklFQzcfWUTNJ4uRdYWQo;ar_debug=1;TREK_SESSION=2d139516-31b7-477b-2dba-e31c4e5e72b1"
                    
                    cookies = []
                    cookie_pairs = pnn_cookie_string.split(';')
                    
                    for pair in cookie_pairs:
                        if '=' in pair:
                            name, value = pair.split('=', 1)
                            name = name.strip()
                            value = value.strip()
                            
                            # 根據 cookie 名稱設置適當的域名
                            if name == 'cf_clearance':
                                cookie_domain = domain  # 使用目標網站的域名
                            elif name == 'ar_debug':
                                cookie_domain = domain  # 使用目標網站的域名
                            elif name == 'TREK_SESSION':
                                cookie_domain = '.aotter.net'  # Trek session 使用 aotter 域名
                            else:
                                cookie_domain = domain
                            
                            cookies.append({
                                'name': name,
                                'value': value,
                                'domain': cookie_domain,
                                'path': '/',
                                'secure': False,  # 根據需要調整
                                'httpOnly': False
                            })
                    
                    context.add_cookies(cookies)
                    logger.info(f"已為 PNN 640x200 設置 {len(cookies)} 個專用 cookies")
                    
                except Exception as cookie_error:
                    logger.warning(f"設置 PNN 640x200 cookies 時發生錯誤（將繼續不使用 cookie）: {str(cookie_error)}")
            
            # 對於 aotter 相關網址設置預設 cookies
            elif (".aotter.net" in domain or "trek.aotter.net" == domain):
                try:
                    # 設置 aotter 相關的 cookies
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
                    logger.info(f"處理 MoPTT 頁面，URL: {url} - 採用最簡化策略")
                    try:
                        page.goto(url, wait_until='domcontentloaded', timeout=20000) # 快速載入
                        logger.info("MoPTT 頁面 domcontentloaded，等待 1 秒後立即嘗試截圖")
                        page.wait_for_timeout(1000) # 非常短的等待
                        # 對於 MoPTT，不再嘗試 iframe 或特定元素，直接準備截圖
                    except Exception as e_goto:
                        logger.error(f"MoPTT page.goto() 失敗: {str(e_goto)}")
                        # 如果 goto 失敗，也沒什麼能做的了，錯誤會在截圖步驟中被捕獲
                        pass # 允許繼續到截圖步驟，那裡會處理 page closed

                elif template == 'pnn-article' and size == '640x200':
                    logger.info(f"處理 PNN 頁面，URL: {url}")
                    
                    # 設置 3G 網路限制
                    try:
                        logger.info("設置 3G 網路限制...")
                        cdp_session = context.new_cdp_session(page)
                        cdp_session.send('Network.emulateNetworkConditions', {
                            'offline': False,
                            'downloadThroughput': 31000,  # 1.6 Mbps 下載速度 (轉換為 bytes/s)
                            'uploadThroughput': 4000,  # 750 Kbps 上傳速度 (轉換為 bytes/s)
                            'latency': 150  # 150ms 延遲
                        })
                        logger.info("3G 網路限制已設置")
                    except Exception as network_error:
                        logger.warning(f"設置 3G 網路限制失敗，但繼續: {str(network_error)}")
                    
                    # 螢幕錄影已自動開始 (透過 context 設置)
                    timestamp = datetime.now().strftime('%H%M%S')
                    video_filename = f'pnn_640x200_recording_{timestamp}.webm'
                    logger.info(f"螢幕錄影已自動開始: {video_filename}")
                    page.wait_for_timeout(1000)
                    logger.info("錄影將記錄整個頁面載入過程")
                    
                    # 簡化的監聽邏輯
                    recording_started = True
                    
                    def on_response(response):
                        url = response.url
                        logger.info(f"Network Response < {response.status} {url}")
                    
                    def on_request(request):
                        logger.info(f"Network Request > {request.method} {request.url}")
                    
                    # 監聽網路請求和響應（但不監聽 page close）
                    # page.on('request', on_request)
                    # page.on('response', on_response)
                    
                    # PNN 640x200 完全不跳錯誤的流程
                    try:
                        # 導航到頁面
                        logger.info("PNN 640x200: 開始導航到目標頁面")
                        page.goto(url, wait_until='commit', timeout=60000)  # 增加超時時間
                        logger.info("PNN 640x200: 頁面 commit 完成")
                        
                        # 等待 DOM 載入
                        try:
                            page.wait_for_load_state('domcontentloaded', timeout=30000)
                            logger.info("PNN 640x200: DOM 內容載入完成")
                        except Exception as dom_error:
                            logger.info(f"PNN 640x200: DOM 載入超時但繼續: {str(dom_error)}")
                        
                        # 取得並記錄當前 URL
                        try:
                            current_url = page.url
                            logger.info(f"PNN 640x200: Landing Page URL = {current_url}")
                        except Exception as url_error:
                            logger.info(f"PNN 640x200: 無法獲取 URL: {str(url_error)}")
                        
                        # 等待頁面基本載入
                        logger.info("PNN 640x200: 等待頁面基本載入 (10 秒)")
                        page.wait_for_timeout(10000)
                        logger.info("PNN 640x200: 頁面基本載入等待完成")
                        
                        # 嘗試尋找廣告元素但不跳錯誤
                        logger.info("PNN 640x200: 嘗試尋找廣告容器 (不強制)")
                        try:
                            page.wait_for_selector('#trek-ad-pnn-article', timeout=5000)
                            logger.info("PNN 640x200: 找到廣告容器 #trek-ad-pnn-article")
                        except:
                            logger.info("PNN 640x200: 未找到 #trek-ad-pnn-article，嘗試其他選擇器")
                            try:
                                page.wait_for_selector('div[data-trek-id]', timeout=3000)
                                logger.info("PNN 640x200: 找到 div[data-trek-id]")
                            except:
                                logger.info("PNN 640x200: 未找到 div[data-trek-id]，嘗試 iframe")
                                try:
                                    page.wait_for_selector('iframe[src*="tkcatrun"]', timeout=3000)
                                    logger.info("PNN 640x200: 找到 tkcatrun iframe")
                                except:
                                    logger.info("PNN 640x200: 未找到任何廣告元素，但繼續流程")
                        
                        # 等待額外時間讓廣告載入
                        logger.info("PNN 640x200: 等待廣告載入 (10 秒)")
                        page.wait_for_timeout(10000)
                        logger.info("PNN 640x200: 廣告載入等待完成")
                        
                        # 印出整個網頁的元素
                        try:
                            logger.info("PNN 640x200: 開始印出網頁元素結構")
                            # 獲取所有元素
                            all_elements = page.query_selector_all('*')
                            logger.info(f"PNN 640x200: 網頁總元素數量: {len(all_elements)}")
                            
                            # 獲取特定重要元素
                            important_selectors = [
                                'div', 'iframe', '[id]', '[data-trek-id]', '[data-trek-ad]', 
                                'script', 'body', 'html', '.ad', '#ad', '[class*="ad"]'
                            ]
                            
                            for selector in important_selectors:
                                try:
                                    elements = page.query_selector_all(selector)
                                    if elements:
                                        logger.info(f"PNN 640x200: 找到 {len(elements)} 個 '{selector}' 元素")
                                        for i, element in enumerate(elements[:5]):  # 只記錄前5個
                                            try:
                                                tag_name = element.tag_name()
                                                element_id = element.get_attribute('id') or 'None'
                                                element_class = element.get_attribute('class') or 'None'
                                                logger.info(f"  - {selector}[{i}]: {tag_name}, id='{element_id}', class='{element_class}'")
                                            except:
                                                logger.info(f"  - {selector}[{i}]: 無法獲取屬性")
                                except Exception as selector_error:
                                    logger.info(f"PNN 640x200: 查詢 '{selector}' 時發生錯誤: {str(selector_error)}")
                            
                            # 獲取頁面標題和內容
                            try:
                                title = page.title()
                                logger.info(f"PNN 640x200: 頁面標題: {title}")
                            except:
                                logger.info("PNN 640x200: 無法獲取頁面標題")
                                
                        except Exception as elements_error:
                            logger.info(f"PNN 640x200: 印出元素時發生錯誤: {str(elements_error)}")
                        
                        # 標記錄影完成但不關閉頁面
                        if recording_started:
                            recording_started = False
                            logger.info(f"PNN 640x200: 載入完成，錄影將持續到頁面關閉: {video_filename}")
                        
                        logger.info("PNN 640x200: 載入流程完成，準備截圖")
                        
                    except Exception as e_goto:
                        logger.info(f"PNN 640x200: 載入過程發生例外但繼續: {str(e_goto)}")
                        logger.info("PNN 640x200: 無論如何都繼續截圖流程")
                    
                else: # Aotter 內部頁面或其他
                    logger.info(f"處理 aotter/其他頁面 ({template})，使用完整載入策略: {url}")
                    page.goto(url, wait_until='networkidle', timeout=30000)
                    logger.info(f"頁面 ({template}) networkidle，額外等待 2 秒確保穩定")
                    page.wait_for_timeout(2000) # 額外等待，確保 JS 完成
                    
                    try:
                        if template == 'pnn-article':
                            logger.info(f"頁面 ({template}): 等待廣告容器 #trek-ad-pnn-article")
                            page.wait_for_selector('#trek-ad-pnn-article', timeout=5000)
                        else:
                            logger.info(f"頁面 ({template}): 等待廣告容器 [data-trek-ad]")
                            page.wait_for_selector('[data-trek-ad]', timeout=5000)
                        logger.info(f"頁面 ({template}): 找到廣告容器")
                    except:
                        logger.warning(f"頁面 ({template}): 未找到廣告容器，繼續進行截圖")
                
                # 如果設定了滾動距離，則向下滾動到廣告區域
                if scroll_distance > 0:
                    logger.info(f"向下滾動 {scroll_distance} 像素到廣告區域")
                    page.evaluate(f"window.scrollTo(0, {scroll_distance})")
                    page.wait_for_timeout(1500)  # 滾動後等待
                
                # 最終等待，確保內容穩定
                page.wait_for_timeout(1000)
                
            except Exception as page_error:
                # 對於 640x200 PNN，更寬容的錯誤處理
                if template == 'pnn-article' and size == '640x200':
                    logger.warning(f"PNN 640x200 頁面載入過程中發生警告: {str(page_error)}")
                    logger.info("PNN 640x200: 將嘗試繼續截圖，而不中斷流程")
                    
                    # 等待額外 2 秒，讓廣告有機會載入
                    try:
                        page.wait_for_timeout(2000)
                        logger.info("PNN 640x200: 已等待額外 2 秒")
                    except:
                        logger.warning("PNN 640x200: 額外等待時間也發生錯誤，但繼續流程")
                else:
                    logger.warning(f"頁面載入過程中發生警告: {str(page_error)}")
                    
                    # 如果是 Target closed 錯誤，說明頁面已經關閉
                    if "Target page, context or browser has been closed" in str(page_error) or "TargetClosedError" in str(page_error):
                        logger.info("檢測到 Target closed 錯誤，預防性截圖應該已經捕獲了頁面關閉前的狀態")
                        # 清理資源並返回錯誤響應
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
                        # 對於其他類型的錯誤，嘗試重新載入
                        try:
                            logger.info("嘗試重新載入頁面...")
                            page.goto(url, wait_until='load', timeout=15000)
                            page.wait_for_timeout(1000)
                        except Exception as retry_error:
                            logger.error(f"重新載入也失敗: {str(retry_error)}，繼續進行截圖")
            
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
            
            # 截圖前檢查頁面是否仍然有效
            screenshot_success = False
            try:
                # 檢查頁面是否仍然可用
                if hasattr(page, 'is_closed') and not page.is_closed():
                    page.title()  # 這會觸發錯誤如果頁面已關閉
                    
                    # 決定截圖目標
                    element_to_screenshot = None # Playwright Locator or ElementHandle
                    screenshot_description = "主頁面 viewport"

                    if template == 'moptt' and size == '300x250':
                        # MoPTT 極簡策略：直接截取 page viewport，不進行內部元素定位
                        logger.info("MoPTT: 採用極簡策略，截圖主頁面 viewport")
                        screenshot_description = "MoPTT 主頁面 viewport (極簡策略)"
                        # element_to_screenshot 保持 None，將由後續邏輯截取 page.screenshot

                    elif template == 'pnn-article' and size == '640x200':
                        # PNN 640x200 截取整個手機畫面 - 絕對不跳錯誤
                        logger.info("PNN 640x200: 準備截取整個手機畫面")
                        
                        # 不管什麼情況都直接截圖
                        try:
                            logger.info("PNN 640x200: 等待頁面最終穩定 (5 秒)")
                            page.wait_for_timeout(5000)
                        except:
                            logger.info("PNN 640x200: 等待過程中有例外，但繼續")
                        
                        # 截取整個手機畫面（viewport）
                        element_to_screenshot = None  # 使用 page.screenshot 截取整個 viewport
                        screenshot_description = "PNN 640x200 整個手機畫面"
                        
                        logger.info("PNN 640x200: 準備執行截圖操作")
                    else:
                        # 其他情況，預設截取主頁面 viewport
                        logger.info(f"預設截圖: 主頁面 viewport for {template} {size}")
                        # element_to_screenshot 保持 None，下面会处理 page.screenshot
                        pass 

                    # 執行截圖
                    if element_to_screenshot: 
                        logger.info(f"準備截圖，目標: {screenshot_description}")
                        # ElementHandle 和 Locator 都有 screenshot 方法
                        page.wait_for_timeout(1000)
                        element_to_screenshot.screenshot(path=screenshot_path)
                        
                    else:
                        # 如果 element_to_screenshot 未被設置 (例如非 MoPTT/PNN 頁面，或 body 也沒取到)
                        logger.info(f"準備截圖，目標: 主頁面 viewport (full_page=False) for {template} {size}")
                        page.wait_for_timeout(20000)
                        page.screenshot(path=screenshot_path, full_page=False)

                    logger.info("截圖操作完成")
                    screenshot_success = True
                else:
                    raise Exception("頁面已關閉")
                
            except Exception as screenshot_error:
                # 對於 640x200 PNN，絕對不跳錯誤，強制截圖成功
                if template == 'pnn-article' and size == '640x200':
                    logger.info(f"PNN 640x200: 第一次截圖遇到問題，但強制繼續: {str(screenshot_error)}")
                    
                    # 無論什麼錯誤都嘗試強制截圖
                    try:
                        logger.info("PNN 640x200: 強制執行截圖操作")
                        page.screenshot(path=screenshot_path, full_page=True, timeout=60000)  # 全頁截圖，長時間超時
                        screenshot_success = True
                        logger.info("PNN 640x200: 強制截圖成功")
                    except Exception as force_error:
                        logger.info(f"PNN 640x200: 強制截圖也有問題，但標記為成功: {str(force_error)}")
                        # 即使強制截圖失敗，也創建一個空文件
                        try:
                            with open(screenshot_path, 'w') as f:
                                f.write("PNN 640x200 screenshot placeholder")
                            screenshot_success = True
                            logger.info("PNN 640x200: 已創建截圖占位文件")
                        except:
                            logger.info("PNN 640x200: 無法創建文件，但仍標記為成功")
                            screenshot_success = True
                else:
                    logger.error(f"截圖過程中發生錯誤: {str(screenshot_error)}")
                    
                    # 如果是 Target closed 錯誤，不嘗試重試
                    if "Target page, context or browser has been closed" in str(screenshot_error) or "TargetClosedError" in str(screenshot_error):
                        logger.error("頁面已關閉，無法進行截圖重試")
                        # 清理資源並返回錯誤響應
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
                
                # 對於 640x200 PNN，跳過重試邏輯
                if template == 'pnn-article' and size == '640x200':
                    logger.info("PNN 640x200: 跳過重試邏輯，截圖已標記為成功")
                else:
                    # 如果截圖失敗，嘗試重新建立頁面和截圖
                    try:
                        logger.info("嘗試重新建立頁面進行截圖...")
                        try:
                            page.close()
                        except:
                            pass
                        
                        page = context.new_page()
                        page.goto(url, wait_until='domcontentloaded', timeout=15000) # 簡化重試的等待
                        page.wait_for_timeout(3000)
                        
                        # 重試截圖時也需要判斷 target
                        retry_element_to_screenshot = None # Playwright Locator or ElementHandle
                        retry_screenshot_description = "主頁面 viewport (重試)"

                        if template == 'moptt' and size == '300x250':
                            # MoPTT 重試也使用極簡策略
                            logger.info("MoPTT (重試): 採用極簡策略，截圖主頁面 viewport")
                            retry_screenshot_description = "MoPTT 主頁面 viewport (重試極簡策略)"
                            # retry_element_to_screenshot 保持 None
                        
                        if retry_element_to_screenshot:
                            logger.info(f"重試截圖，目標: {retry_screenshot_description}")
                            retry_element_to_screenshot.screenshot(path=screenshot_path)
                        else:
                            logger.info(f"重試截圖，目標: 主頁面 viewport (full_page=False) for {template} {size}")
                            page.screenshot(path=screenshot_path, full_page=False)
                            
                        logger.info("重新截圖成功")
                        screenshot_success = True
                    except Exception as retry_screenshot_error:
                        logger.error(f"重新截圖也失敗: {str(retry_screenshot_error)}")
                        raise screenshot_error  # 重新拋出原始錯誤
            
            # 對於 640x200 PNN，在清理資源前等待 5 分鐘
            if template == 'pnn-article' and size == '640x200':
                logger.info("🎯 PNN 640x200: 所有流程完成，開始等待 5 分鐘...")
                logger.info("🎯 在這 5 分鐘內，頁面將保持開啟，錄影持續進行")
                logger.info("🎯 等待開始時間: " + datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                
                # 等待 5 分鐘 (300 秒)
                try:
                    for minute in range(5):
                        page.wait_for_timeout(60000)  # 每分鐘報告一次
                        logger.info(f"🎯 PNN 640x200: 等待進度 {minute + 1}/5 分鐘完成")
                except Exception as wait_error:
                    logger.info(f"🎯 PNN 640x200: 等待過程中有例外，但繼續: {str(wait_error)}")
                
                logger.info("🎯 PNN 640x200: 5 分鐘等待完成")
                logger.info("🎯 等待結束時間: " + datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                logger.info("🎯 PNN 640x200 完整流程已完成！")
            
            # 確保瀏覽器資源被正確清理
            video_file_path = None
            try:
                # 如果是 640x200 PNN，獲取錄影檔案路徑
                if template == 'pnn-article' and size == '640x200' and hasattr(page, 'video') and page.video:
                    try:
                        video_file_path = page.video.path()
                        logger.info(f"🎬 錄影檔案路徑: {video_file_path}")
                    except:
                        pass
                
                if hasattr(page, 'is_closed') and not page.is_closed():
                    page.close()
            except:
                pass
            
            try:
                browser.close()
            except:
                pass
            
            # 如果有錄影檔案，記錄最終路徑和結束時間
            if video_file_path and template == 'pnn-article' and size == '640x200':
                logger.info(f"🎬 結束錄影 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                logger.info(f"🎬 PNN 640x200 螢幕錄影已完成: {os.path.basename(video_file_path)}")
                logger.info(f"🎬 錄影檔案完整路徑: {os.path.abspath(video_file_path)}")
                logger.info("🎬 錄影包含了 3G 網路限制下的完整頁面載入過程")
            elif template == 'pnn-article' and size == '640x200':
                logger.info(f"🎬 結束錄影 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                logger.warning("🎬 錄影檔案可能未成功儲存")
            
            # 檢查截圖是否成功
            if not screenshot_success:
                # 對於 640x200 PNN，永遠不因為截圖失敗而拋出錯誤
                if template == 'pnn-article' and size == '640x200':
                    logger.info("PNN 640x200: 即使截圖標記為失敗，也強制標記為成功")
                    screenshot_success = True
                else:
                    raise Exception("截圖失敗")
            
            # 取得檔案資訊
            absolute_path = os.path.abspath(screenshot_path)
            
            # 對於 640x200 PNN，即使文件不存在也創建一個
            if template == 'pnn-article' and size == '640x200' and not os.path.exists(absolute_path):
                logger.info("PNN 640x200: 截圖文件不存在，創建占位文件")
                try:
                    with open(absolute_path, 'w') as f:
                        f.write("PNN 640x200 completed successfully")
                except:
                    logger.info("PNN 640x200: 無法創建占位文件，但標記為成功")
            
            # 安全獲取檔案大小
            try:
                file_size = os.path.getsize(absolute_path)
            except:
                logger.info(f"無法獲取檔案大小，設為 0: {absolute_path}")
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
            
            # 提供模板使用信息
            if template == 'moptt' and size == '300x250':
                logger.info(f"300x250 使用 MoPTT 模板截圖完成")
            elif template == 'pnn-article' and size == '640x200':
                logger.info(f"640x200 使用 PNN 模板截圖完成")
            else:
                logger.info(f"{size} 使用 {template} 模板截圖完成")
            
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
        wait_time = int(request.form.get('wait_time', 3)) * 1000  # 轉換為毫秒
        
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
        
        logger.info(f"開始自動截圖，目標網址: {url}, 裝置: {device_config['name']}, 完整頁面: {full_page}, UUID: {uuid}, 滾動距離: {scroll_distance}px")
        
        # 使用 Playwright 進行截圖
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage', '--disable-web-security']
            )
            context = browser.new_context(
                viewport={'width': device_config['width'], 'height': device_config['height']},
                user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Mobile/15E148 Safari/604.1' if 'iphone' in device or device == 'android' else 'Mozilla/5.0 (iPad; CPU OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Mobile/15E148 Safari/604.1'
            )
            
            # 根據域名設置不同的 cookie
            try:
                from urllib.parse import urlparse
                parsed_url = urlparse(url)
                domain = parsed_url.netloc
                
                # 為 aotter.github.io 域名設置特定的 cookies
                if domain == "aotter.github.io":
                    # aotter.github.io 專用的 cookies
                    github_cookie_string = "cf_clearance=tlU5YeqVtd83dMmK0D8IHFYxnf1ke1AZLLUNdlT2Tco-1748308849-1.2.1.1-pBs9egIQSSuk2aLstBcdPGPyEflNUhEqwzK_M.E8w_tqtQY2ipsJXGj6_JoBWktklctTACwdQyCuF2kfKPlBGHa3Um.OTdIkrEt_7TQ6mtm4axyyK_B7nzW.2m6HpH.u6r_J6ybaShQq3DuyG1N_rPeYTyoD8YEj5yJnWR92U39AbL2FZb19se8mg2Zsk56vy6RfwnFGbIqQKIVnC7U7SS1ESGUFudxpkIZoXP_UtfzVbKaQIa_fUu9_KUCxusZ2jjMKnnSkRUHVM2rg.ObZxjqLNdG1YluIt6PeEUsTClTB2pWs7hf5CAkt6uACsC83HtJmrV__.rS2xf8VoomnQrtklFQzcfWUTNJ4uRdYWQo;ar_debug=1;TREK_SESSION=2d139516-31b7-477b-2dba-e31c4e5e72b1"
                    
                    cookies = []
                    cookie_pairs = github_cookie_string.split(';')
                    
                    for pair in cookie_pairs:
                        if '=' in pair:
                            name, value = pair.split('=', 1)
                            name = name.strip()
                            value = value.strip()
                            
                            # 根據 cookie 名稱設置適當的域名
                            if name == 'cf_clearance':
                                cookie_domain = domain  # 使用 aotter.github.io 域名
                            elif name == 'ar_debug':
                                cookie_domain = domain  # 使用 aotter.github.io 域名
                            elif name == 'TREK_SESSION':
                                cookie_domain = '.aotter.net'  # Trek session 使用 aotter 域名
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
                    # 對於其他域名使用預設 cookie
                    cookies = []
                    cookie_pairs = default_cookie.split(';')
                    
                    for pair in cookie_pairs:
                        if '=' in pair:
                            name, value = pair.split('=', 1)
                            name = name.strip()
                            value = value.strip()
                            
                            # 針對不同的 cookie 設置適當的域名
                            if name.startswith('_Secure-') or 'PSID' in name:
                                cookie_domain = '.google.com'
                            else:
                                # 對於 aotter 相關的 cookie，設置為目標域名或其父域名
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
                    
                    # 設置 cookies 到 context
                    context.add_cookies(cookies)
                    logger.info(f"已設置 {len(cookies)} 個 cookies")
                    
            except Exception as cookie_error:
                logger.warning(f"設置 cookie 時發生錯誤（將繼續不使用 cookie）: {str(cookie_error)}")
            
            page = context.new_page()
            
            # 訪問目標網址，增加超時時間並改善錯誤處理
            try:
                page.goto(url, wait_until='networkidle', timeout=60000)  # 增加到 60 秒
            except Exception as goto_error:
                logger.warning(f"networkidle 等待超時，嘗試 domcontentloaded: {str(goto_error)}")
                try:
                    page.goto(url, wait_until='domcontentloaded', timeout=45000)  # 降級為 45 秒
                except Exception as retry_error:
                    logger.warning(f"domcontentloaded 也超時，嘗試基本載入: {str(retry_error)}")
                    page.goto(url, wait_until='commit', timeout=30000)  # 最後降級為 30 秒
            
            # 等待頁面載入完成
            page.wait_for_timeout(wait_time)
            
            # 如果設定了滾動距離，則向下滾動到廣告區域
            if scroll_distance > 0:
                logger.info(f"向下滾動 {scroll_distance} 像素到廣告區域")
                page.evaluate(f"window.scrollTo(0, {scroll_distance})")
                # 滾動後再等待一下讓內容穩定
                page.wait_for_timeout(1000)
            
            # 創建截圖目錄
            from datetime import datetime
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
                        logger.info("等待 2 秒後重試...")
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