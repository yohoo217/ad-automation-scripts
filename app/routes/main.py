from flask import Blueprint, render_template, redirect, url_for, session, request, flash, jsonify, Response
import logging
import os
from playwright.sync_api import sync_playwright
import requests
from urllib.parse import quote_plus
import concurrent.futures
import time

# 導入 MongoDB 連接
from app.models.database import get_mongo_client, get_activity_name_by_adset_id

# 導入 suprad 自動化腳本
try:
    from suprad_adunit_auto_create import run as run_suprad
except ImportError:
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    from suprad_adunit_auto_create import run as run_suprad

logger = logging.getLogger(__name__)

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """主頁重定向到原生廣告頁面"""
    return redirect(url_for('native_ad.native_ad'))

@main_bp.route('/batch')
def batch():
    """批量廣告頁面"""
    return render_template('batch.html')

@main_bp.route('/report')
def report():
    """報表頁面"""
    return render_template('report.html')

@main_bp.route('/test-adset-info')
def test_adset_info():
    """廣告集資訊查詢測試頁面"""
    with open('test_integration.html', 'r', encoding='utf-8') as f:
        return f.read()

@main_bp.route('/api/adset-info')
def get_adset_info():
    """根據廣告活動 ID 查詢 MongoDB 中所有 AdSet 的計價方式和價格資訊"""
    try:
        # 獲取查詢參數
        campaign_id = request.args.get('campaignId')
        
        if not campaign_id:
            return jsonify({'error': '缺少必要參數：campaignId'}), 400
        
        logger.info(f"查詢廣告活動資訊: {campaign_id}")
        
        # 連接 MongoDB
        client = get_mongo_client()
        if not client:
            return jsonify({'error': 'MongoDB 連接失敗'}), 500
        
        # 選擇資料庫和集合
        db = client['trek']
        adset_collection = db['AdSet']
        
        # 查詢該 Campaign 下的所有 AdSet
        adsets = list(adset_collection.find({'campId': campaign_id}))
        
        if not adsets:
            return jsonify({'error': f'找不到廣告活動 ID: {campaign_id} 的任何廣告集'}), 404
        
        logger.info(f"找到 {len(adsets)} 個廣告集")
        
        # 特別為測試廣告活動顯示所有 AdSet 名稱
        if campaign_id == 'eed11b7d-ce2f-46cd-842f-005c5a3c6397':
            logger.info(f"📋 廣告活動 {campaign_id} 所有 AdSet 清單:")
            for i, adset in enumerate(adsets, 1):
                adset_name = adset.get('name', '')
                adset_uuid = adset.get('uuid', '')
                is_demo = 'demo' in adset_name.lower()
                logger.info(f"  {i}. {adset_name} (UUID: {adset_uuid[:8]}...) [{'DEMO' if is_demo else 'NORMAL'}]")
        
        # 從 Campaign 集合取得活動名稱和總預算
        campaign_collection = db['Campaign']
        campaign_data = campaign_collection.find_one({'uuid': campaign_id})
        
        campaign_name = None
        campaign_budget = None
        if campaign_data:
            campaign_name = campaign_data.get('name')
            campaign_budget = campaign_data.get('totalBudget')
            logger.info(f"從 Campaign 集合取得: 名稱={campaign_name}, 總預算={campaign_budget}")
        
        # 處理多個 AdSet 的資訊整合
        adset_infos = []
        earliest_from_time = None
        latest_to_time = None
        total_budget = 0
        primary_pricing = None
        
        for adset_data in adsets:
            adset_id = adset_data.get('uuid')
            adset_name = adset_data.get('name', '')
            
            # 提取計價方式和價格
            b_mode = adset_data.get('bMode', '')
            pricing_info = {
                'bMode': b_mode,
                'price': 0,
                'currency': adset_data.get('curr', 'TWD')
            }
            
            # 根據計價方式取得對應的價格
            if b_mode == 'CPC':
                pricing_info['price'] = adset_data.get('cpc', 0)
            elif b_mode == 'CPM':
                pricing_info['price'] = adset_data.get('cpm', 0)
            elif b_mode == 'CPV':
                pricing_info['price'] = adset_data.get('cpv', 0)
            
            # 過濾包含 "demo" 的 AdSet，優先設定非 demo 的計價方式
            is_demo = 'demo' in adset_name.lower()
            
            # 加強日誌，特別是對於特定的廣告活動
            if campaign_id == 'eed11b7d-ce2f-46cd-842f-005c5a3c6397':
                logger.info(f"🔍 廣告活動 {campaign_id} - AdSet 詳情:")
                logger.info(f"  AdSet UUID: {adset_id}")
                logger.info(f"  AdSet 名稱: '{adset_name}'")
                logger.info(f"  計價方式: {b_mode} ${pricing_info['price']}")
                logger.info(f"  是否為 demo: {is_demo}")
                logger.info(f"  目前 primary_pricing: {primary_pricing}")
            
            if primary_pricing is None and not is_demo:
                primary_pricing = pricing_info
                logger.info(f"✅ 設定主要計價方式從非 demo AdSet: {adset_name} - {b_mode} ${pricing_info['price']}")
            elif primary_pricing is None and is_demo:
                # 如果目前只有 demo AdSet，暫時設定但標記為 demo
                logger.warning(f"⚠️ 暫時使用 demo AdSet 的計價方式: {adset_name} - {b_mode} ${pricing_info['price']}")
                primary_pricing = pricing_info
            elif not is_demo and primary_pricing:
                # 如果已經有 primary_pricing，但現在找到非 demo 的，替換掉
                logger.info(f"🔄 發現非 demo AdSet，替換計價方式: {adset_name} - {b_mode} ${pricing_info['price']} (原: {primary_pricing})")
                primary_pricing = pricing_info
            
            # 從活動名稱解析預算（使用 AdSet 的 name）
            parsed_budget = parse_budget_from_name(adset_name)
            actual_budget = parsed_budget if parsed_budget > 0 else adset_data.get('budget', 0)
            
            # 如果是 demo AdSet，不計入總預算
            if not is_demo:
                total_budget += actual_budget
            else:
                logger.info(f"跳過 demo AdSet 的預算計算: {adset_name} (${actual_budget})")
            
            # 處理時間戳
            from_time = adset_data.get('fromTime')
            to_time = adset_data.get('toTime')
            
            from_timestamp = None
            to_timestamp = None
            
            if from_time:
                from datetime import datetime
                if isinstance(from_time, dict) and '$date' in from_time:
                    date_str = from_time['$date']
                    dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                elif isinstance(from_time, datetime):
                    dt = from_time
                else:
                    dt = datetime.fromisoformat(str(from_time).replace('Z', '+00:00'))
                
                from_timestamp = int(dt.timestamp() * 1000)
                if earliest_from_time is None or from_timestamp < earliest_from_time:
                    earliest_from_time = from_timestamp
            
            if to_time:
                from datetime import datetime
                if isinstance(to_time, dict) and '$date' in to_time:
                    date_str = to_time['$date']
                    dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                elif isinstance(to_time, datetime):
                    dt = to_time
                else:
                    dt = datetime.fromisoformat(str(to_time).replace('Z', '+00:00'))
                
                to_timestamp = int(dt.timestamp() * 1000)
                if latest_to_time is None or to_timestamp > latest_to_time:
                    latest_to_time = to_timestamp
            
            # 儲存個別 AdSet 資訊
            adset_infos.append({
                'uuid': adset_id,
                'name': adset_name,
                'adType': adset_data.get('adType', ''),
                'state': adset_data.get('state', ''),
                'budget': actual_budget,
                'parsedBudget': parsed_budget,
                'originalBudget': adset_data.get('budget', 0),
                'pricing': pricing_info,
                'fromTimestamp': from_timestamp,
                'toTimestamp': to_timestamp,
                'isDemo': is_demo
            })
        
        # 計算活動結束日期
        campaign_end_date = None
        if latest_to_time:
            from datetime import datetime
            dt = datetime.fromtimestamp(latest_to_time / 1000)
            campaign_end_date = dt.strftime('%Y-%m-%d')
        
        # 額外資訊（整合所有 AdSet）
        additional_info = {
            'name': campaign_name or f'活動 {campaign_id[:8]}',
            'adsetCount': len(adsets),
            'adsets': adset_infos,  # 個別 AdSet 詳細資訊
            'budget': campaign_budget if campaign_budget is not None else total_budget,
            'campaignBudget': campaign_budget,
            'totalAdsetBudget': total_budget,
            'adType': adsets[0].get('adType', '') if adsets else '',
            'campaignEndDate': campaign_end_date,
            'fromTimestamp': earliest_from_time,
            'toTimestamp': latest_to_time
        }
        
        # 確保有計價方式設定
        if primary_pricing is None:
            logger.warning(f"沒有找到非 demo 的 AdSet，使用預設計價方式")
            primary_pricing = {'bMode': 'CPC', 'price': 7.0, 'currency': 'TWD'}
        
        # 統計資訊
        non_demo_count = len([info for info in adset_infos if not info.get('isDemo', False)])
        demo_count = len([info for info in adset_infos if info.get('isDemo', False)])
        
        logger.info(f"查詢成功: {campaign_id} - 找到 {len(adsets)} 個廣告集 (非demo: {non_demo_count}, demo: {demo_count}), 總預算: ${campaign_budget or total_budget}")
        
        return jsonify({
            'success': True,
            'campaignId': campaign_id,
            'pricing': primary_pricing,
            'info': additional_info
        })
        
    except Exception as e:
        logger.error(f"查詢廣告活動資訊時發生錯誤: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'查詢失敗: {str(e)}'
        }), 500

def parse_budget_from_name(name):
    """從活動名稱中解析預算，支援格式如：5/25-6/8 | $100000"""
    import re
    
    if not name:
        return 0
    
    try:
        # 尋找 $ 符號後面的數字
        # 支援格式：$100000, $100,000, $ 100000 等
        pattern = r'\$\s*([0-9,]+)'
        matches = re.findall(pattern, name)
        
        if matches:
            # 取最後一個匹配的金額（通常是預算）
            budget_str = matches[-1].replace(',', '')
            return int(budget_str)
        
        # 如果沒找到 $ 符號，嘗試尋找 | 後面的純數字
        pattern = r'\|\s*([0-9,]+)'
        matches = re.findall(pattern, name)
        
        if matches:
            budget_str = matches[-1].replace(',', '')
            return int(budget_str)
            
    except (ValueError, IndexError):
        pass
    
    return 0

@main_bp.route('/api/report-proxy')
def report_proxy():
    """報表 API 代理路由，支援 Campaign ID 查詢多個 AdSet 並合併數據"""
    try:
        # 獲取查詢參數
        campaign_id = request.args.get('campaignId')
        since_date = request.args.get('sinceDate')
        to_date = request.args.get('toDate')
        
        if not all([campaign_id, since_date, to_date]):
            return jsonify({'error': '缺少必要參數：campaignId, sinceDate, toDate'}), 400
        
        # 連接 MongoDB 查詢該 Campaign 下的所有 AdSet
        client = get_mongo_client()
        if not client:
            return jsonify({'error': 'MongoDB 連接失敗'}), 500
        
        db = client['trek']
        adset_collection = db['AdSet']
        adsets = list(adset_collection.find({'campId': campaign_id}))
        
        if not adsets:
            return jsonify({'error': f'找不到廣告活動 ID: {campaign_id} 的任何廣告集'}), 404
        
        logger.info(f"找到 {len(adsets)} 個廣告集，開始查詢報表")
        
        # 設置請求標頭，包含認證信息
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'Cookie': 'AOTTERBD_SESSION=757418f543a95a889184e798ec5ab66d4fad04e5-lats=1724229220332&sso=PIg4zu/Vdnn/A15vMEimFlVAGliNhoWlVd5FTvtEMRAFpk/VvBGvAetanw8DLATSLexy9pee/t52uNojvoFS2Q==;aotter=eyJ1c2VyIjp7ImlkIjoiNjNkYjRkNDBjOTFiNTUyMmViMjk4YjBkIiwiZW1haWwiOiJpYW4uY2hlbkBhb3R0ZXIubmV0IiwiY3JlYXRlZEF0IjoxNjc1MzE2NTQ0LCJlbWFpbFZlcmlmaWVkIjp0cnVlLCJsZWdhY3lJZCI6bnVsbCwibGVnYWN5U2VxSWQiOjE2NzUzMTY1NDQ3ODI5NzQwMDB9LCJhY2Nlc3NUb2tlbiI6IjJkYjQyZTNkOTM5MDUzMjdmODgyZmYwMDRiZmI4YmEzZjBhNTlmMDQwYzhiN2Y4NGY5MmZmZTIzYTU0ZTQ2MDQiLCJ1ZWEiOm51bGx9; _Secure-1PSID=vlPPgXupFroiSjP1/A02minugZVZDgIG4K; _Secure-1PSIDCC=g.a000mwhavReSVd1vN09AVTswXkPAhyuW7Tgj8-JFhj-FZya9I_l1B6W2gqTIWAtQUTQMkTxoAwACgYKAW0SARISFQHGX2MiC--NJ2PzCzDpJ0m3odxHhxoVAUF8yKr8r49abq8oe4UxCA0t_QCW0076; _Secure-3PSID=AKEyXzUuXI1zywmFmkEBEBHfg6GRkRM9cJ9BiJZxmaR46x5im_krhaPtmL4Jhw8gQsz5uFFkfbc; _Secure-3PSIDCC=sidts-CjEBUFGohzUF6oK3ZMACCk2peoDBDp6djBwJhGc4Lxgu2zOlzbVFeVpXF4q1TYZ5ba6cEAA'
        }
        
        # 查詢每個 AdSet 的報表數據
        adset_reports = {}
        merged_html_content = ""
        
        for adset in adsets:
            adset_id = adset.get('uuid')
            adset_name = adset.get('name', adset_id[:8])
            
            # 構建目標 URL
            target_url = f"https://trek.aotter.net/dontblockme/action_adset_read/getadsetreporttemplate/?setId={quote_plus(adset_id)}&sinceDate={quote_plus(since_date)}&toDate={quote_plus(to_date)}"
            
            logger.info(f"查詢 AdSet {adset_name} 報表: {target_url}")
            
            try:
                # 發送請求到目標 API
                response = requests.get(target_url, headers=headers, timeout=30)
                
                if response.status_code == 200:
                    adset_reports[adset_id] = {
                        'name': adset_name,
                        'content': response.text,
                        'success': True
                    }
                else:
                    logger.warning(f"AdSet {adset_name} 查詢失敗: {response.status_code}")
                    adset_reports[adset_id] = {
                        'name': adset_name,
                        'content': None,
                        'success': False,
                        'error': f'HTTP {response.status_code}'
                    }
                    
            except Exception as e:
                logger.error(f"查詢 AdSet {adset_name} 時發生錯誤: {str(e)}")
                adset_reports[adset_id] = {
                    'name': adset_name,
                    'content': None,
                    'success': False,
                    'error': str(e)
                }
        
        # 檢查是否有成功的報表
        successful_reports = [report for report in adset_reports.values() if report['success']]
        
        if not successful_reports:
            return jsonify({
                'success': False,
                'error': '所有 AdSet 的報表查詢都失敗了',
                'adset_results': adset_reports
            }), 500
        
        # 合併所有成功的報表數據
        # 這裡需要解析 HTML 並合併數據，先返回第一個成功的報表加上所有報表資訊
        primary_content = successful_reports[0]['content']
        
        return jsonify({
            'success': True,
            'content': primary_content,  # 主要內容（後續前端會處理合併）
            'adset_reports': adset_reports,  # 所有個別 AdSet 的報表
            'content_type': 'text/html',
            'summary': {
                'total_adsets': len(adsets),
                'successful_reports': len(successful_reports),
                'failed_reports': len(adsets) - len(successful_reports)
            }
        })
            
    except requests.exceptions.Timeout:
        logger.error("請求超時")
        return jsonify({
            'success': False,
            'error': '請求超時，請稍後再試'
        }), 408
        
    except requests.exceptions.RequestException as e:
        logger.error(f"請求發生錯誤: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'請求失敗: {str(e)}'
        }), 500

@main_bp.route('/vote-ad')
def vote_ad():
    """投票廣告頁面"""
    # 從 session 獲取之前填寫的表單數據
    form_data = {
        'adset_id': session.get('vote_adset_id', ''),
        'display_name': session.get('vote_display_name', ''),
        'advertiser': session.get('vote_advertiser', ''),
        'main_title': session.get('vote_main_title', ''),
        'vote_title': session.get('vote_title', ''),
        'subtitle': session.get('vote_subtitle', ''),
        'landing_page': session.get('vote_landing_page', ''),
        'call_to_action': session.get('vote_call_to_action', '立即了解'),
        'image_path_m': session.get('vote_image_path_m', ''),
        'image_path_s': session.get('vote_image_path_s', ''),
        'vote_image': session.get('vote_image', ''),
        'vote_id': session.get('vote_id', 'myVoteId'),
        'divider_color': session.get('vote_divider_color', '#ff0000'),
        'vote_width': session.get('vote_width', '80%'),
        'bg_color': session.get('vote_bg_color', '#ffffff'),
        'vote_position': session.get('vote_position', 'bottom'),
        'min_position': session.get('vote_min_position', 50),
        'max_position': session.get('vote_max_position', 70),
        'timeout': session.get('vote_timeout', 2000),
        'winner_bg_color': session.get('vote_winner_bg_color', '#26D07C'),
        'winner_text_color': session.get('vote_winner_text_color', '#ffffff'),
        'loser_bg_color': session.get('vote_loser_bg_color', '#000000'),
        'loser_text_color': session.get('vote_loser_text_color', '#ffffff')
    }
    
    # 嘗試還原投票選項的數據
    vote_options = []
    index = 0
    while True:
        option_title_key = f'option_title_{index}'
        option_text_color_key = f'option_text_color_{index}'
        option_bg_color_key = f'option_bg_color_{index}'
        option_target_url_key = f'option_target_url_{index}'
        
        if option_title_key in session:
            vote_options.append({
                'index': index,
                'title': session.get(option_title_key, ''),
                'text_color': session.get(option_text_color_key, '#207AED'),
                'bg_color': session.get(option_bg_color_key, '#E7F3FF'),
                'target_url': session.get(option_target_url_key, '')
            })
            form_data[option_title_key] = session.get(option_title_key, '')
            form_data[option_text_color_key] = session.get(option_text_color_key, '#207AED')
            form_data[option_bg_color_key] = session.get(option_bg_color_key, '#E7F3FF')
            form_data[option_target_url_key] = session.get(option_target_url_key, '')
            index += 1
        else:
            break
    
    form_data['vote_options'] = vote_options
    return render_template('vote_ad.html', **form_data)

# 其他廣告類型的路由
@main_bp.route('/gif-ad', methods=['GET', 'POST'])
def gif_ad():
    """GIF 廣告頁面"""
    if request.method == 'POST':
        return create_gif_ad()
    
    # 從 session 獲取之前填寫的表單數據
    form_data = {
        'adset_id': session.get('gif_adset_id', ''),
        'display_name': session.get('gif_display_name', ''),
        'advertiser': session.get('gif_advertiser', ''),
        'main_title': session.get('gif_main_title', ''),
        'subtitle': session.get('gif_subtitle', ''),
        'landing_page': session.get('gif_landing_page', ''),
        'call_to_action': session.get('gif_call_to_action', '立即購買'),
        'image_path_m': session.get('gif_image_path_m', ''),
        'image_path_s': session.get('gif_image_path_s', ''),
        'background_image': session.get('gif_background_image', ''),
        'background_url': session.get('gif_background_url', ''),
        'target_url': session.get('gif_target_url', '')
    }
    return render_template('gif_ad.html', **form_data)

def create_gif_ad():
    """處理 GIF 廣告創建"""
    try:
        # 獲取表單數據
        ad_data = {
            'adset_id': request.form.get('adset_id', ''),
            'display_name': request.form.get('display_name', ''),
            'advertiser': request.form.get('advertiser', ''),
            'main_title': request.form.get('main_title', ''),
            'subtitle': request.form.get('subtitle', ''),
            'landing_page': request.form.get('landing_page', ''),
            'call_to_action': request.form.get('call_to_action', '立即購買'),
            'image_path_m': request.form.get('image_path_m', ''),
            'image_path_s': request.form.get('image_path_s', ''),
            'background_image': request.form.get('background_image', ''),
            'background_url': request.form.get('background_url', ''),
            'target_url': request.form.get('target_url', ''),
            'payload_game_widget': request.form.get('payload_game_widget', '')
        }
        
        # 保存表單數據到 session（以便失敗時可以重新填充）
        for key, value in ad_data.items():
            session[f'gif_{key}'] = value
        
        # 驗證必填欄位
        required_fields = ['advertiser', 'main_title', 'adset_id', 'landing_page', 
                          'image_path_m', 'image_path_s', 'background_url', 'target_url']
        missing_fields = [field for field in required_fields if not ad_data[field]]
        
        if missing_fields:
            flash(f"缺少必填欄位: {', '.join(missing_fields)}", 'error')
            return redirect(url_for('main.gif_ad'))
        
        # 驗證圖片檔案是否存在
        for image_field in ['image_path_m', 'image_path_s']:
            image_path = ad_data[image_field]
            if image_path and not os.path.exists(image_path):
                flash(f"圖片檔案不存在: {image_path}", 'error')
                return redirect(url_for('main.gif_ad'))
        
        # 嘗試創建廣告
        logger.info(f"開始創建 GIF 廣告: {ad_data['display_name'] or ad_data['main_title']}")
        
        with sync_playwright() as playwright:
            success = run_suprad(playwright, ad_data, 'gif')
        
        if success:
            # 不自動清除 session 中的表單數據，讓用戶可以重複使用
            flash(f"成功創建 GIF 廣告: {ad_data['display_name'] or ad_data['main_title']}", 'success')
            logger.info(f"成功創建 GIF 廣告: {ad_data['display_name'] or ad_data['main_title']}")
        else:
            flash("自動創建過程中發生錯誤", 'error')
            logger.error(f"創建 GIF 廣告失敗: {ad_data['display_name'] or ad_data['main_title']}")
            
    except Exception as e:
        error_msg = str(e)
        logger.error(f"創建 GIF 廣告時發生意外錯誤: {error_msg}")
        
        # 特別處理 TargetClosedError
        if "TargetClosedError" in error_msg or "Target page, context or browser has been closed" in error_msg:
            flash("瀏覽器意外關閉，請稍後再試", 'error')
        else:
            flash(f"創建 GIF 廣告時發生錯誤: {error_msg}", 'error')
    
    return redirect(url_for('main.gif_ad'))

@main_bp.route('/slide-ad')
def slide_ad():
    """水平 Slide 廣告頁面"""
    # 從 session 獲取之前填寫的表單數據
    form_data = {
        'adset_id': session.get('slide_adset_id', ''),
        'display_name': session.get('slide_display_name', ''),
        'advertiser': session.get('slide_advertiser', ''),
        'main_title': session.get('slide_main_title', ''),
        'subtitle': session.get('slide_subtitle', ''),
        'landing_page': session.get('slide_landing_page', ''),
        'call_to_action': session.get('slide_call_to_action', '立即了解'),
        'image_path_m': session.get('slide_image_path_m', ''),
        'image_path_s': session.get('slide_image_path_s', ''),
        'background_image': session.get('slide_background_image', '')
    }
    
    # 恢復滑動項目數據
    slide_items = []
    index = 0
    while True:
        image_url_key = f'image_url_{index}'
        target_url_key = f'target_url_{index}'
        if image_url_key in session or target_url_key in session:
            slide_items.append({
                'index': index,
                'image_url': session.get(image_url_key, ''),
                'target_url': session.get(target_url_key, '')
            })
            form_data[image_url_key] = session.get(image_url_key, '')
            form_data[target_url_key] = session.get(target_url_key, '')
            index += 1
        else:
            break
    
    form_data['slide_items'] = slide_items
    return render_template('slide_ad.html', **form_data)

@main_bp.route('/vertical-slide-ad')
def vertical_slide_ad():
    """垂直 Slide 廣告頁面"""
    # 從 session 獲取之前填寫的表單數據
    form_data = {
        'adset_id': session.get('vertical_slide_adset_id', ''),
        'display_name': session.get('vertical_slide_display_name', ''),
        'advertiser': session.get('vertical_slide_advertiser', ''),
        'main_title': session.get('vertical_slide_main_title', ''),
        'subtitle': session.get('vertical_slide_subtitle', ''),
        'landing_page': session.get('vertical_slide_landing_page', ''),
        'call_to_action': session.get('vertical_slide_call_to_action', '立即了解'),
        'image_path_m': session.get('vertical_slide_image_path_m', ''),
        'image_path_s': session.get('vertical_slide_image_path_s', ''),
        'background_image': session.get('vertical_slide_background_image', '')
    }
    
    # 恢復滑動項目數據
    slide_items = []
    index = 0
    while True:
        image_url_key = f'image_url_{index}'
        target_url_key = f'target_url_{index}'
        if image_url_key in session or target_url_key in session:
            slide_items.append({
                'index': index,
                'image_url': session.get(image_url_key, ''),
                'target_url': session.get(target_url_key, '')
            })
            form_data[image_url_key] = session.get(image_url_key, '')
            form_data[target_url_key] = session.get(target_url_key, '')
            index += 1
        else:
            break
    
    form_data['slide_items'] = slide_items
    return render_template('vertical_slide_ad.html', **form_data)

@main_bp.route('/vertical-cube-slide-ad')
def vertical_cube_slide_ad():
    """垂直 Cube Slide 廣告頁面"""
    # 從 session 獲取之前填寫的表單數據
    form_data = {
        'adset_id': session.get('vertical_cube_slide_adset_id', ''),
        'display_name': session.get('vertical_cube_slide_display_name', ''),
        'advertiser': session.get('vertical_cube_slide_advertiser', ''),
        'main_title': session.get('vertical_cube_slide_main_title', ''),
        'subtitle': session.get('vertical_cube_slide_subtitle', ''),
        'landing_page': session.get('vertical_cube_slide_landing_page', ''),
        'call_to_action': session.get('vertical_cube_slide_call_to_action', '立即了解'),
        'image_path_m': session.get('vertical_cube_slide_image_path_m', ''),
        'image_path_s': session.get('vertical_cube_slide_image_path_s', ''),
        'background_image': session.get('vertical_cube_slide_background_image', '')
    }
    
    # 恢復滑動項目數據
    slide_items = []
    index = 0
    while True:
        image_url_key = f'image_url_{index}'
        target_url_key = f'target_url_{index}'
        if image_url_key in session or target_url_key in session:
            slide_items.append({
                'index': index,
                'image_url': session.get(image_url_key, ''),
                'target_url': session.get(target_url_key, '')
            })
            form_data[image_url_key] = session.get(image_url_key, '')
            form_data[target_url_key] = session.get(target_url_key, '')
            index += 1
        else:
            break
    
    form_data['slide_items'] = slide_items
    return render_template('vertical_cube_slide_ad.html', **form_data)

@main_bp.route('/countdown_ad')
def countdown_ad():
    """倒數廣告頁面"""
    # 從 session 獲取之前填寫的表單數據
    form_data = {
        'adset_id': session.get('countdown_adset_id', ''),
        'display_name': session.get('countdown_display_name', ''),
        'advertiser': session.get('countdown_advertiser', ''),
        'main_title': session.get('countdown_main_title', ''),
        'subtitle': session.get('countdown_subtitle', ''),
        'landing_page': session.get('countdown_landing_page', ''),
        'call_to_action': session.get('countdown_call_to_action', '立即購買'),
        'image_path_m': session.get('countdown_image_path_m', ''),
        'image_path_s': session.get('countdown_image_path_s', ''),
        'background_image': session.get('countdown_background_image', ''),
        'background_url': session.get('countdown_background_url', ''),
        'target_url': session.get('countdown_target_url', ''),
        'end_date': session.get('countdown_end_date', ''),
        'description_text': session.get('countdown_description_text', '活動截止倒數'),
        'position': session.get('countdown_position', '3'),
        'date_number_color': session.get('countdown_date_number_color', '#FFFFFF'),
        'description_color': session.get('countdown_description_color', '#FFFFFF'),
        'date_word_color': session.get('countdown_date_word_color', '#FFFFFF'),
        'date_number_size': session.get('countdown_date_number_size', '4'),
        'description_size': session.get('countdown_description_size', '4'),
        'date_word_size': session.get('countdown_date_word_size', '4'),
        'show_day': session.get('countdown_show_day', 'true'),
        'show_hour': session.get('countdown_show_hour', 'true'),
        'show_min': session.get('countdown_show_min', 'true'),
        'show_sec': session.get('countdown_show_sec', 'true')
    }
    return render_template('countdown_ad.html', **form_data)

@main_bp.route('/create-vote-ad', methods=['POST'])
def create_vote_ad():
    """處理投票廣告創建"""
    try:
        # 獲取基本表單數據
        ad_data = {
            'adset_id': request.form.get('adset_id', ''),
            'display_name': request.form.get('display_name', ''),
            'advertiser': request.form.get('advertiser', ''),
            'main_title': request.form.get('main_title', ''),
            'vote_title': request.form.get('vote_title', ''),
            'subtitle': request.form.get('subtitle', ''),
            'landing_page': request.form.get('landing_page', ''),
            'call_to_action': request.form.get('call_to_action', '立即了解'),
            'image_path_m': request.form.get('image_path_m', ''),
            'image_path_s': request.form.get('image_path_s', ''),
            'vote_image': request.form.get('vote_image', ''),
            'vote_id': request.form.get('vote_id', 'myVoteId'),
            'divider_color': request.form.get('divider_color', '#ff0000'),
            'vote_width': request.form.get('vote_width', '80%'),
            'bg_color': request.form.get('bg_color', '#ffffff'),
            'vote_position': request.form.get('vote_position', 'bottom'),
            'min_position': request.form.get('min_position', 50),
            'max_position': request.form.get('max_position', 70),
            'timeout': request.form.get('timeout', 2000),
            'winner_bg_color': request.form.get('winner_bg_color', '#26D07C'),
            'winner_text_color': request.form.get('winner_text_color', '#ffffff'),
            'loser_bg_color': request.form.get('loser_bg_color', '#000000'),
            'loser_text_color': request.form.get('loser_text_color', '#ffffff')
        }
        
        # 保存表單數據到 session
        for key, value in ad_data.items():
            session[f'vote_{key}'] = value
            
        # 處理投票選項
        vote_options = []
        index = 0
        while True:
            option_title = request.form.get(f'option_title_{index}', '')
            if not option_title:
                break
                
            vote_options.append({
                'title': option_title,
                'text_color': request.form.get(f'option_text_color_{index}', '#207AED'),
                'bg_color': request.form.get(f'option_bg_color_{index}', '#E7F3FF'),
                'target_url': request.form.get(f'option_target_url_{index}', '')
            })
            
            # 保存到 session
            session[f'option_title_{index}'] = option_title
            session[f'option_text_color_{index}'] = request.form.get(f'option_text_color_{index}', '#207AED')
            session[f'option_bg_color_{index}'] = request.form.get(f'option_bg_color_{index}', '#E7F3FF')
            session[f'option_target_url_{index}'] = request.form.get(f'option_target_url_{index}', '')
            index += 1
            
        ad_data['vote_options'] = vote_options
        
        # 實際調用 suprad 腳本建立廣告
        try:
            # 準備 payload - 投票廣告使用 payload_vote_widget
            payload_vote_widget = request.form.get('payload_vote_widget', '')
            if not payload_vote_widget:
                flash("投票套件 payload 不能為空", 'error')
                return redirect(url_for('main.vote_ad'))
            
            # 將投票 payload 轉換為遊戲套件 payload 格式，以便使用 suprad 腳本
            ad_data['payload_game_widget'] = payload_vote_widget
            ad_data['background_url'] = ad_data.get('vote_image', '')  # 使用投票圖片作為背景
            
            # 調用 suprad 腳本
            with sync_playwright() as playwright:
                result = run_suprad(playwright, ad_data, 'vote')
            
            if result:
                flash("投票廣告創建成功！", 'success')
                # 不自動清除 session 中的表單數據，讓用戶可以重複使用
            else:
                flash("投票廣告創建失敗", 'error')
                
        except Exception as e:
            logger.error(f"調用 suprad 腳本時發生錯誤: {str(e)}")
            flash(f"調用 suprad 腳本時發生錯誤: {str(e)}", 'error')
        
    except Exception as e:
        logger.error(f"創建投票廣告時發生錯誤: {str(e)}")
        flash(f"創建投票廣告時發生錯誤: {str(e)}", 'error')
    
    return redirect(url_for('main.vote_ad'))

@main_bp.route('/create-slide-ad', methods=['POST'])
def create_slide_ad():
    """處理水平 Slide 廣告創建"""
    try:
        # 處理表單數據
        ad_data = {
            'adset_id': request.form.get('adset_id', ''),
            'display_name': request.form.get('display_name', ''),
            'advertiser': request.form.get('advertiser', ''),
            'main_title': request.form.get('main_title', ''),
            'subtitle': request.form.get('subtitle', ''),
            'landing_page': request.form.get('landing_page', ''),
            'call_to_action': request.form.get('call_to_action', '立即了解'),
            'image_path_m': request.form.get('image_path_m', ''),
            'image_path_s': request.form.get('image_path_s', ''),
            'background_url': request.form.get('background_image', '')  # 修正欄位名稱對應
        }
        
        # 保存表單數據到 session
        for key, value in ad_data.items():
            session[f'slide_{key}'] = value
            
        # 處理滑動項目
        slide_items = []
        index = 0
        while True:
            image_url = request.form.get(f'image_url_{index}', '')
            target_url = request.form.get(f'target_url_{index}', '')
            if not image_url and not target_url:
                break
                
            slide_items.append({
                'image_url': image_url,
                'target_url': target_url
            })
            
            # 保存到 session
            session[f'image_url_{index}'] = image_url
            session[f'target_url_{index}'] = target_url
            index += 1
            
        ad_data['slide_items'] = slide_items
        
        # 實際調用 suprad 腳本建立廣告
        try:
            # 準備 payload
            payload_game_widget = request.form.get('payload_game_widget', '')
            if not payload_game_widget:
                flash("遊戲套件 payload 不能為空", 'error')
                return redirect(url_for('main.slide_ad'))
            
            # 將 payload 添加到 ad_data 中
            ad_data['payload_game_widget'] = payload_game_widget
            
            # 調用 suprad 腳本
            with sync_playwright() as playwright:
                result = run_suprad(playwright, ad_data, 'slide')
            
            if result:
                flash("水平 Slide 廣告創建成功！", 'success')
                # 不自動清除 session 中的表單數據，讓用戶可以重複使用
            else:
                flash("水平 Slide 廣告創建失敗", 'error')
                
        except Exception as e:
            logger.error(f"調用 suprad 腳本時發生錯誤: {str(e)}")
            flash(f"調用 suprad 腳本時發生錯誤: {str(e)}", 'error')
        
    except Exception as e:
        logger.error(f"創建水平 Slide 廣告時發生錯誤: {str(e)}")
        flash(f"創建水平 Slide 廣告時發生錯誤: {str(e)}", 'error')
    
    return redirect(url_for('main.slide_ad'))

@main_bp.route('/create-vertical-slide-ad', methods=['POST'])
def create_vertical_slide_ad():
    """處理垂直 Slide 廣告創建"""
    try:
        # 處理表單數據
        ad_data = {
            'adset_id': request.form.get('adset_id', ''),
            'display_name': request.form.get('display_name', ''),
            'advertiser': request.form.get('advertiser', ''),
            'main_title': request.form.get('main_title', ''),
            'subtitle': request.form.get('subtitle', ''),
            'landing_page': request.form.get('landing_page', ''),
            'call_to_action': request.form.get('call_to_action', '立即了解'),
            'image_path_m': request.form.get('image_path_m', ''),
            'image_path_s': request.form.get('image_path_s', ''),
            'background_url': request.form.get('background_image', '')  # 修正欄位名稱對應
        }
        
        # 保存表單數據到 session
        for key, value in ad_data.items():
            session[f'vertical_slide_{key}'] = value
            
        # 處理滑動項目（重用相同的 key 結構）
        slide_items = []
        index = 0
        while True:
            image_url = request.form.get(f'image_url_{index}', '')
            target_url = request.form.get(f'target_url_{index}', '')
            if not image_url and not target_url:
                break
                
            slide_items.append({
                'image_url': image_url,
                'target_url': target_url
            })
            
            # 保存到 session
            session[f'image_url_{index}'] = image_url
            session[f'target_url_{index}'] = target_url
            index += 1
            
        ad_data['slide_items'] = slide_items
        
        # 實際調用 suprad 腳本建立廣告
        try:
            # 準備 payload
            payload_game_widget = request.form.get('payload_game_widget', '')
            if not payload_game_widget:
                flash("遊戲套件 payload 不能為空", 'error')
                return redirect(url_for('main.vertical_slide_ad'))
            
            # 將 payload 添加到 ad_data 中
            ad_data['payload_game_widget'] = payload_game_widget
            
            # 調用 suprad 腳本
            with sync_playwright() as playwright:
                result = run_suprad(playwright, ad_data, 'vertical_slide')
            
            if result:
                flash("垂直 Slide 廣告創建成功！", 'success')
                # 不自動清除 session 中的表單數據，讓用戶可以重複使用
            else:
                flash("垂直 Slide 廣告創建失敗", 'error')
                
        except Exception as e:
            logger.error(f"調用 suprad 腳本時發生錯誤: {str(e)}")
            flash(f"調用 suprad 腳本時發生錯誤: {str(e)}", 'error')
        
    except Exception as e:
        logger.error(f"創建垂直 Slide 廣告時發生錯誤: {str(e)}")
        flash(f"創建垂直 Slide 廣告時發生錯誤: {str(e)}", 'error')
    
    return redirect(url_for('main.vertical_slide_ad'))

@main_bp.route('/create-vertical-cube-slide-ad', methods=['POST'])
def create_vertical_cube_slide_ad():
    """處理垂直 Cube Slide 廣告創建"""
    try:
        # 處理表單數據
        ad_data = {
            'adset_id': request.form.get('adset_id', ''),
            'display_name': request.form.get('display_name', ''),
            'advertiser': request.form.get('advertiser', ''),
            'main_title': request.form.get('main_title', ''),
            'subtitle': request.form.get('subtitle', ''),
            'landing_page': request.form.get('landing_page', ''),
            'call_to_action': request.form.get('call_to_action', '立即了解'),
            'image_path_m': request.form.get('image_path_m', ''),
            'image_path_s': request.form.get('image_path_s', ''),
            'background_url': request.form.get('background_image', '')  # 修正欄位名稱對應
        }
        
        # 保存表單數據到 session
        for key, value in ad_data.items():
            session[f'vertical_cube_slide_{key}'] = value
            
        # 處理滑動項目
        slide_items = []
        index = 0
        while True:
            image_url = request.form.get(f'image_url_{index}', '')
            target_url = request.form.get(f'target_url_{index}', '')
            if not image_url and not target_url:
                break
                
            slide_items.append({
                'image_url': image_url,
                'target_url': target_url
            })
            
            # 保存到 session
            session[f'image_url_{index}'] = image_url
            session[f'target_url_{index}'] = target_url
            index += 1
            
        ad_data['slide_items'] = slide_items
        
        # 實際調用 suprad 腳本建立廣告
        try:
            # 準備 payload
            payload_game_widget = request.form.get('payload_game_widget', '')
            if not payload_game_widget:
                flash("遊戲套件 payload 不能為空", 'error')
                return redirect(url_for('main.vertical_cube_slide_ad'))
            
            # 將 payload 添加到 ad_data 中
            ad_data['payload_game_widget'] = payload_game_widget
            
            # 調用 suprad 腳本
            with sync_playwright() as playwright:
                result = run_suprad(playwright, ad_data, 'vertical_cube_slide')
            
            if result:
                flash("垂直 Cube Slide 廣告創建成功！", 'success')
                # 不自動清除 session 中的表單數據，讓用戶可以重複使用
            else:
                flash("垂直 Cube Slide 廣告創建失敗", 'error')
                
        except Exception as e:
            logger.error(f"調用 suprad 腳本時發生錯誤: {str(e)}")
            flash(f"調用 suprad 腳本時發生錯誤: {str(e)}", 'error')
        
    except Exception as e:
        logger.error(f"創建垂直 Cube Slide 廣告時發生錯誤: {str(e)}")
        flash(f"創建垂直 Cube Slide 廣告時發生錯誤: {str(e)}", 'error')
    
    return redirect(url_for('main.vertical_cube_slide_ad'))

@main_bp.route('/create-countdown-ad', methods=['POST'])
def create_countdown_ad():
    """處理倒數廣告創建"""
    try:
        # 處理表單數據
        ad_data = {
            'adset_id': request.form.get('adset_id', ''),
            'display_name': request.form.get('display_name', ''),
            'advertiser': request.form.get('advertiser', ''),
            'main_title': request.form.get('main_title', ''),
            'subtitle': request.form.get('subtitle', ''),
            'landing_page': request.form.get('landing_page', ''),
            'call_to_action': request.form.get('call_to_action', '立即購買'),
            'image_path_m': request.form.get('image_path_m', ''),
            'image_path_s': request.form.get('image_path_s', ''),
            'background_image': request.form.get('background_image', ''),
            'background_url': request.form.get('background_url', ''),
            'target_url': request.form.get('target_url', ''),
            'end_date': request.form.get('end_date', ''),
            'description_text': request.form.get('description_text', '活動截止倒數'),
            'position': request.form.get('position', '3'),
            'date_number_color': request.form.get('date_number_color', '#FFFFFF'),
            'description_color': request.form.get('description_color', '#FFFFFF'),
            'date_word_color': request.form.get('date_word_color', '#FFFFFF'),
            'date_number_size': request.form.get('date_number_size', '4'),
            'description_size': request.form.get('description_size', '4'),
            'date_word_size': request.form.get('date_word_size', '4'),
            'show_day': request.form.get('show_day', 'true'),
            'show_hour': request.form.get('show_hour', 'true'),
            'show_min': request.form.get('show_min', 'true'),
            'show_sec': request.form.get('show_sec', 'true')
        }
        
        # 保存表單數據到 session
        for key, value in ad_data.items():
            session[f'countdown_{key}'] = value
        
        # 實際調用 suprad 腳本建立廣告
        try:
            # 準備 payload
            payload_game_widget = request.form.get('payload_game_widget', '')
            if not payload_game_widget:
                flash("遊戲套件 payload 不能為空", 'error')
                return redirect(url_for('main.countdown_ad'))
            
            # 將 payload 添加到 ad_data 中
            ad_data['payload_game_widget'] = payload_game_widget
            
            # 調用 suprad 腳本
            with sync_playwright() as playwright:
                result = run_suprad(playwright, ad_data, 'countdown')
            
            if result:
                flash("倒數廣告創建成功！", 'success')
                # 不自動清除 session 中的表單數據，讓用戶可以重複使用
            else:
                flash("倒數廣告創建失敗", 'error')
                
        except Exception as e:
            logger.error(f"調用 suprad 腳本時發生錯誤: {str(e)}")
            flash(f"調用 suprad 腳本時發生錯誤: {str(e)}", 'error')
        
    except Exception as e:
        logger.error(f"創建倒數廣告時發生錯誤: {str(e)}")
        flash(f"創建倒數廣告時發生錯誤: {str(e)}", 'error')
    
    return redirect(url_for('main.countdown_ad'))

# 清除表單數據的路由
@main_bp.route('/clear-slide-form', methods=['POST'])
def clear_slide_form():
    """清除水平 Slide 廣告表單數據"""
    keys_to_remove = [key for key in session.keys() if key.startswith('slide_') or key.startswith('image_url_') or key.startswith('target_url_')]
    for key in keys_to_remove:
        session.pop(key, None)
    flash("表單內容已清除", 'info')
    return redirect(url_for('main.slide_ad'))

@main_bp.route('/clear-vertical-slide-form', methods=['POST'])
def clear_vertical_slide_form():
    """清除垂直 Slide 廣告表單數據"""
    keys_to_remove = [key for key in session.keys() if key.startswith('vertical_slide_') or key.startswith('image_url_') or key.startswith('target_url_')]
    for key in keys_to_remove:
        session.pop(key, None)
    flash("表單內容已清除", 'info')
    return redirect(url_for('main.vertical_slide_ad'))

@main_bp.route('/clear-vertical-cube-slide-form', methods=['POST'])
def clear_vertical_cube_slide_form():
    """清除垂直 Cube Slide 廣告表單數據"""
    keys_to_remove = [key for key in session.keys() if key.startswith('vertical_cube_slide_') or key.startswith('image_url_') or key.startswith('target_url_')]
    for key in keys_to_remove:
        session.pop(key, None)
    flash("表單內容已清除", 'info')
    return redirect(url_for('main.vertical_cube_slide_ad'))

@main_bp.route('/clear-gif-form', methods=['POST'])
def clear_gif_form():
    """清除 GIF 廣告表單數據"""
    keys_to_remove = [key for key in session.keys() if key.startswith('gif_')]
    for key in keys_to_remove:
        session.pop(key, None)
    flash("表單內容已清除", 'info')
    return redirect(url_for('main.gif_ad'))

@main_bp.route('/clear-vote-form', methods=['POST'])
def clear_vote_form():
    """清除投票廣告表單數據"""
    keys_to_remove = [key for key in session.keys() if key.startswith('vote_') or key.startswith('option_')]
    for key in keys_to_remove:
        session.pop(key, None)
    flash("表單內容已清除", 'info')
    return redirect(url_for('main.vote_ad'))

@main_bp.route('/clear-countdown-form', methods=['POST'])
def clear_countdown_form():
    """清除倒數廣告表單數據"""
    keys_to_remove = [key for key in session.keys() if key.startswith('countdown_')]
    for key in keys_to_remove:
        session.pop(key, None)
    flash("表單內容已清除", 'info')
    return redirect(url_for('main.countdown_ad'))

@main_bp.route('/api/adunits')
def get_adunits():
    """查詢指定 Campaign 的所有 AdUnit"""
    try:
        campaign_id = request.args.get('campaignId')
        if not campaign_id:
            return jsonify({'error': '缺少 campaignId 參數'}), 400
        
        from app.models.database import get_mongo_client, MONGO_DATABASE
        client = get_mongo_client()
        if not client:
            return jsonify({'error': 'MongoDB 連接失敗'}), 500
        
        db = client[MONGO_DATABASE]
        
        # 先查詢該 Campaign 下的所有 AdSet
        adset_collection = db['AdSet']
        adsets = list(adset_collection.find({'campId': campaign_id}, {'uuid': 1, 'name': 1}))
        
        if not adsets:
            return jsonify({'error': f'找不到廣告活動 ID: {campaign_id} 的任何廣告集'}), 404
        
        # 取得所有 AdSet ID
        adset_ids = [adset['uuid'] for adset in adsets]
        
        # 查詢所有 AdSet 的 AdUnit
        adunit_collection = db['AdUnit']
        query = {"setId": {"$in": adset_ids}}
        projection = {
            "uuid": 1,
            "name": 1, 
            "title": 1,
            "setId": 1,  # 加入 setId 以便知道屬於哪個 AdSet
            "img_main": 1,  # 添加 img_main 字段
            "interactSrc.creativeType": 1,
            "_id": 0
        }
        
        adunits = list(adunit_collection.find(query, projection))
        
        # 建立 AdSet 名稱對照表
        adset_names = {adset['uuid']: adset['name'] for adset in adsets}
        
        # 為每個 AdUnit 加上 AdSet 名稱
        for adunit in adunits:
            adunit['adsetName'] = adset_names.get(adunit.get('setId'), '未知廣告集')
        
        logger.info(f"找到 {len(adunits)} 個 AdUnit for campaign {campaign_id} (來自 {len(adsets)} 個 AdSet)")
        
        return jsonify({
            'success': True,
            'adunits': adunits,
            'count': len(adunits),
            'adsets': adsets,  # 包含 AdSet 資訊
            'summary': {
                'total_adsets': len(adsets),
                'total_adunits': len(adunits)
            }
        })
        
    except Exception as e:
        logger.error(f"查詢 AdUnit 時發生錯誤: {str(e)}")
        return jsonify({'error': f'查詢失敗: {str(e)}'}), 500

@main_bp.route('/api/cut-data')
def get_cut_data():
    """查詢 tkrecorder 的 cut 數據"""
    try:
        uuid = request.args.get('uuid')
        if not uuid:
            return jsonify({'error': '缺少 uuid 參數'}), 400
        
        # 查詢 tkrecorder API
        tkrecorder_url = f"https://tkrecorder.aotter.net/sp/list/v/{uuid}"
        
        logger.info(f"正在查詢 tkrecorder: {tkrecorder_url}")
        
        response = requests.get(tkrecorder_url, timeout=30)
        
        if response.status_code != 200:
            return jsonify({'error': f'tkrecorder API 請求失敗: {response.status_code}'}), 500
        
        data = response.json()
        
        return jsonify({
            'success': True,
            'uuid': uuid,
            'data': data
        })
        
    except requests.RequestException as e:
        logger.error(f"請求 tkrecorder API 時發生錯誤: {str(e)}")
        return jsonify({'error': f'請求失敗: {str(e)}'}), 500
    except Exception as e:
        logger.error(f"查詢 cut 數據時發生錯誤: {str(e)}")
        return jsonify({'error': f'查詢失敗: {str(e)}'}), 500

@main_bp.route('/api/adunit-reports-sequential')
def get_adunit_reports_sequential():
    """查詢指定 Campaign 所有 AdSet 下所有 AdUnit 的報表數據 - 使用逐一查詢保護線上服務"""
    try:
        campaign_id = request.args.get('campaignId')
        since_date = request.args.get('sinceDate')  # 開始時間戳
        to_date = request.args.get('toDate')  # 結束時間戳
        
        if not campaign_id:
            return jsonify({'error': '缺少 campaignId 參數'}), 400
        
        from app.models.database import get_mongo_client, MONGO_DATABASE
        import time
        
        client = get_mongo_client()
        if not client:
            return jsonify({'error': 'MongoDB 連接失敗'}), 500
        
        db = client[MONGO_DATABASE]
        
        # 先查詢該 Campaign 下的所有 AdSet
        adset_collection = db['AdSet']
        adsets = list(adset_collection.find({'campId': campaign_id}, {'uuid': 1, 'name': 1}))
        
        if not adsets:
            return jsonify({'error': f'找不到廣告活動 ID: {campaign_id} 的任何廣告集'}), 404
        
        # 取得所有 AdSet ID
        adset_ids = [adset['uuid'] for adset in adsets]
        
        # 查詢所有 AdSet 的 AdUnit
        adunit_collection = db['AdUnit']
        query = {"setId": {"$in": adset_ids}}
        projection = {
            "uuid": 1,
            "name": 1, 
            "title": 1,
            "setId": 1,
            "img_main": 1,  # 添加 img_main 字段
            "_id": 0
        }
        
        adunits = list(adunit_collection.find(query, projection))
        
        if not adunits:
            return jsonify({'error': f'找不到任何 AdUnit'}), 404
        
        # 建立 AdSet 名稱對照表
        adset_names = {adset['uuid']: adset['name'] for adset in adsets}
        
        # 設置請求標頭，包含認證信息
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'Cookie': 'AOTTERBD_SESSION=757418f543a95a889184e798ec5ab66d4fad04e5-lats=1724229220332&sso=PIg4zu/Vdnn/A15vMEimFlVAGliNhoWlVd5FTvtEMRAFpk/VvBGvAetanw8DLATSLexy9pee/t52uNojvoFS2Q==;aotter=eyJ1c2VyIjp7ImlkIjoiNjNkYjRkNDBjOTFiNTUyMmViMjk4YjBkIiwiZW1haWwiOiJpYW4uY2hlbkBhb3R0ZXIubmV0IiwiY3JlYXRlZEF0IjoxNjc1MzE2NTQ0LCJlbWFpbFZlcmlmaWVkIjp0cnVlLCJsZWdhY3lJZCI6bnVsbCwibGVnYWN5U2VxSWQiOjE2NzUzMTY1NDQ3ODI5NzQwMDB9LCJhY2Nlc3NUb2tlbiI6IjJkYjQyZTNkOTM5MDUzMjdmODgyZmYwMDRiZmI4YmEzZjBhNTlmMDQwYzhiN2Y4NGY5MmZmZTIzYTU0ZTQ2MDQiLCJ1ZWEiOm51bGx9; _Secure-1PSID=vlPPgXupFroiSjP1/A02minugZVZDgIG4K; _Secure-1PSIDCC=g.a000mwhavReSVd1vN09AVTswXkPAhyuW7Tgj8-JFhj-FZya9I_l1B6W2gqTIWAtQUTQMkTxoAwACgYKAW0SARISFQHGX2MiC--NJ2PzCzDpJ0m3odxHhxoVAUF8yKr8r49abq8oe4UxCA0t_QCW0076; _Secure-3PSID=AKEyXzUuXI1zywmFmkEBEBHfg6GRkRM9cJ9BiJZxmaR46x5im_krhaPtmL4Jhw8gQsz5uFFkfbc; _Secure-3PSIDCC=sidts-CjEBUFGohzUF6oK3ZMACCk2peoDBDp6djBwJhGc4Lxgu2zOlzbVFeVpXF4q1TYZ5ba6cEAA'
        }
        
        def fetch_adunit_report(adunit):
            """查詢單個 AdUnit 報表的函數"""
            adunit_uuid = adunit.get('uuid')
            adunit_name = adunit.get('title') or adunit.get('name') or adunit_uuid[:8]
            adset_id = adunit.get('setId')
            adset_name = adset_names.get(adset_id, '未知廣告集')
            
            # 構建目標 URL
            base_url = f"https://trek.aotter.net/dontblockme/action_adset_read/getadunitreporttemplate/?setId={quote_plus(adset_id)}&uuid={quote_plus(adunit_uuid)}"
            
            # 如果有時間參數，加入到 URL
            if since_date and to_date:
                target_url = f"{base_url}&sinceDate={quote_plus(since_date)}&toDate={quote_plus(to_date)}"
            else:
                target_url = base_url
            
            # 重試機制設定
            max_retries = 2  # 減少重試次數以保護伺服器
            retry_delay = 2  # 增加重試間隔
            timeout_duration = 60  # 減少超時時間
            
            for attempt in range(max_retries):
                try:
                    logger.info(f"[Sequential] 查詢 AdUnit {adunit_name} 報表 (嘗試 {attempt + 1}/{max_retries}): {target_url}")
                    
                    # 發送請求到目標 API
                    response = requests.get(target_url, headers=headers, timeout=timeout_duration)
                    
                    if response.status_code == 200:
                        logger.info(f"[Sequential] AdUnit {adunit_name} 查詢成功")
                        return {
                            'uuid': adunit_uuid,
                            'name': adunit_name,
                            'adsetId': adset_id,
                            'adsetName': adset_name,
                            'img_main': adunit.get('img_main', ''),  # 添加 img_main
                            'content': response.text,
                            'success': True
                        }
                    else:
                        logger.warning(f"[Sequential] AdUnit {adunit_name} 查詢失敗: HTTP {response.status_code} (嘗試 {attempt + 1}/{max_retries})")
                        if attempt < max_retries - 1:
                            time.sleep(retry_delay)
                            continue
                        else:
                            return {
                                'uuid': adunit_uuid,
                                'name': adunit_name,
                                'adsetId': adset_id,
                                'adsetName': adset_name,
                                'img_main': adunit.get('img_main', ''),  # 添加 img_main
                                'content': None,
                                'success': False,
                                'error': f'HTTP {response.status_code} (經過 {max_retries} 次重試)'
                            }
                            
                except requests.exceptions.Timeout as e:
                    logger.warning(f"[Sequential] AdUnit {adunit_name} 查詢超時 (嘗試 {attempt + 1}/{max_retries}): {str(e)}")
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay * (attempt + 1))
                        continue
                    else:
                        return {
                            'uuid': adunit_uuid,
                            'name': adunit_name,
                            'adsetId': adset_id,
                            'adsetName': adset_name,
                            'img_main': adunit.get('img_main', ''),  # 添加 img_main
                            'content': None,
                            'success': False,
                            'error': f'查詢超時 (經過 {max_retries} 次重試，每次 {timeout_duration} 秒)'
                        }
                        
                except Exception as e:
                    logger.error(f"[Sequential] 查詢 AdUnit {adunit_name} 時發生錯誤 (嘗試 {attempt + 1}/{max_retries}): {str(e)}")
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                        continue
                    else:
                        return {
                            'uuid': adunit_uuid,
                            'name': adunit_name,
                            'adsetId': adset_id,
                            'adsetName': adset_name,
                            'img_main': adunit.get('img_main', ''),  # 添加 img_main
                            'content': None,
                            'success': False,
                            'error': f'{str(e)} (經過 {max_retries} 次重試)'
                        }
        
        # 使用逐一查詢所有 AdUnit 報表，保護線上服務
        logger.info(f"開始逐一查詢 {len(adunits)} 個 AdUnit 報表，每個間隔 3 秒")
        start_time = time.time()
        
        adunit_reports = {}
        query_delay = 3  # 每個查詢間等待 3 秒
        
        for index, adunit in enumerate(adunits):
            adunit_uuid = adunit.get('uuid')
            adunit_name = adunit.get('title') or adunit.get('name') or adunit_uuid[:8]
            
            logger.info(f"[Sequential {index + 1}/{len(adunits)}] 查詢 AdUnit: {adunit_name}")
            
            # 查詢單個 AdUnit 報表
            result = fetch_adunit_report(adunit)
            adunit_reports[result['uuid']] = result
            
            # 在查詢間等待，避免對伺服器造成負擔
            if index < len(adunits) - 1:  # 最後一個不需要等待
                logger.info(f"[Sequential] 等待 {query_delay} 秒後查詢下一個 AdUnit...")
                time.sleep(query_delay)
        
        end_time = time.time()
        query_duration = round(end_time - start_time, 2)
        
        # 檢查是否有成功的報表
        successful_reports = [report for report in adunit_reports.values() if report['success']]
        
        # 按 AdSet 分組整理結果
        adunit_by_adset = {}
        for adunit_uuid, report in adunit_reports.items():
            adset_id = report['adsetId']
            if adset_id not in adunit_by_adset:
                adunit_by_adset[adset_id] = {
                    'adsetName': report['adsetName'],
                    'adunits': []
                }
            adunit_by_adset[adset_id]['adunits'].append(report)
        
        logger.info(f"逐一查詢 Campaign {campaign_id} 的 AdUnit 報表完成：{len(successful_reports)}/{len(adunits)} 成功，耗時 {query_duration} 秒")
        
        return jsonify({
            'success': True,
            'campaignId': campaign_id,
            'adunit_reports': adunit_reports,  # 所有 AdUnit 的報表
            'adunit_by_adset': adunit_by_adset,  # 按 AdSet 分組的結果
            'summary': {
                'total_adsets': len(adsets),
                'total_adunits': len(adunits),
                'successful_reports': len(successful_reports),
                'failed_reports': len(adunits) - len(successful_reports),
                'query_duration': query_duration,
                'query_delay': query_delay,
                'processing_method': 'sequential_processing'
            }
        })
        
    except Exception as e:
        logger.error(f"查詢 AdUnit 報表時發生錯誤: {str(e)}")
        return jsonify({'error': f'查詢失敗: {str(e)}'}), 500


# 保留原有的批次查詢 API 作為備用（但已停用以保護線上服務）
@main_bp.route('/api/proxy-image')
def proxy_image():
    """代理圖片下載，解決跨域問題"""
    try:
        image_url = request.args.get('url')
        if not image_url:
            return jsonify({'error': '缺少 url 參數'}), 400
        
        logger.info(f"代理下載圖片: {image_url}")
        
        # 設置請求標頭
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
            'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Referer': 'https://trek.aotter.net/'
        }
        
        # 下載圖片
        response = requests.get(image_url, headers=headers, timeout=30, stream=True)
        
        if response.status_code == 200:
            # 獲取圖片類型
            content_type = response.headers.get('content-type', 'image/jpeg')
            
            # 返回圖片數據
            return Response(
                response.content,
                mimetype=content_type,
                headers={
                    'Content-Type': content_type,
                    'Access-Control-Allow-Origin': '*',
                    'Cache-Control': 'public, max-age=3600'  # 緩存1小時
                }
            )
        else:
            logger.warning(f"圖片下載失敗: {image_url} - HTTP {response.status_code}")
            return jsonify({'error': f'圖片下載失敗: HTTP {response.status_code}'}), response.status_code
            
    except requests.RequestException as e:
        logger.error(f"下載圖片時發生錯誤: {str(e)}")
        return jsonify({'error': f'下載失敗: {str(e)}'}), 500
    except Exception as e:
        logger.error(f"代理圖片時發生錯誤: {str(e)}")
        return jsonify({'error': f'處理失敗: {str(e)}'}), 500

@main_bp.route('/api/adunit-reports')
def get_adunit_reports():
    """查詢指定 Campaign 所有 AdSet 下所有 AdUnit 的報表數據 - 已停用以保護線上服務"""
    return jsonify({
        'success': False,
        'error': '批次查詢已停用以保護線上服務，請使用逐一查詢模式'
    }), 400