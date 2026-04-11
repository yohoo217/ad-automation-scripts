from flask import Blueprint, render_template, redirect, url_for, session, request, flash, jsonify, Response
import logging
import os
from playwright.sync_api import sync_playwright
import requests
from urllib.parse import quote_plus
import concurrent.futures
import time
import json

# 導入 MongoDB 連接
from app.models.database import get_mongo_client, get_activity_name_by_adset_id, MONGO_DATABASE

# 導入登入驗證
from app.utils.auth import login_required

logger = logging.getLogger(__name__)

main_bp = Blueprint('main', __name__)


def _build_proxy_headers():
    """建立查詢外部報表時使用的基本 headers。"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache',
    }
    cookie_value = os.getenv('PLATFORM_COOKIE', '')
    if cookie_value:
        headers['Cookie'] = cookie_value
    return headers

@main_bp.route('/')
@login_required
def index():
    """主頁重定向到原生廣告頁面"""
    return redirect(url_for('native_ad.native_ad'))

@main_bp.route('/batch')
@login_required
def batch():
    """批量廣告頁面"""
    return render_template('batch.html')

@main_bp.route('/report')
@login_required
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
        db = client[MONGO_DATABASE]
        adset_collection = db['AdSet']
        
        # 查詢該 Campaign 下的所有 AdSet
        adsets = list(adset_collection.find({'campId': campaign_id}, {'_id': 0}))
        
        if not adsets:
            return jsonify({'error': f'找不到廣告活動 ID: {campaign_id} 的任何廣告集'}), 404
        
        logger.info(f"找到 {len(adsets)} 個廣告集")
        
        # 特別為測試廣告活動顯示所有 AdSet 名稱
        if campaign_id == 'YOUR_TEST_CAMPAIGN_ID_HERE':
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
            if campaign_id == 'YOUR_TEST_CAMPAIGN_ID_HERE':
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
        
        db = client[MONGO_DATABASE]
        adset_collection = db['AdSet']
        adsets = list(adset_collection.find({'campId': campaign_id}))
        
        if not adsets:
            return jsonify({'error': f'找不到廣告活動 ID: {campaign_id} 的任何廣告集'}), 404
        
        # 過濾掉名稱包含 "demo" 的 AdSet
        original_adset_count = len(adsets)
        filtered_adsets = []
        filtered_out_adsets = []
        
        for adset in adsets:
            adset_name = adset.get('name', '').lower()
            if 'demo' in adset_name:
                filtered_out_adsets.append(adset)
                logger.info(f"[Report-Proxy] 過濾掉包含 demo 的 AdSet: {adset.get('name')}")
            else:
                filtered_adsets.append(adset)
        
        if not filtered_adsets:
            logger.warning(f"[Report-Proxy] 過濾後沒有可用的 AdSet (原有 {original_adset_count} 個，全部包含 demo)")
            return jsonify({'error': f'該廣告活動的所有廣告集都包含 demo，已被過濾'}), 404
        
        logger.info(f"[Report-Proxy] AdSet 過濾結果: {len(filtered_adsets)}/{original_adset_count} 個可用 ({len(filtered_out_adsets)} 個包含 demo 被過濾)")
        
        adsets = filtered_adsets  # 更新為過濾後的結果
        logger.info(f"找到 {len(adsets)} 個廣告集，開始查詢報表")
        
        # 設置請求標頭，包含認證信息
        headers = _build_proxy_headers()
        
        # 查詢每個 AdSet 的報表數據
        adset_reports = {}
        merged_html_content = ""
        
        for adset in adsets:
            adset_id = adset.get('uuid')
            adset_name = adset.get('name', adset_id[:8])
            
            # 構建目標 URL
            target_url = f"https://adplatform.example.com/dontblockme/action_adset_read/getadsetreporttemplate/?setId={quote_plus(adset_id)}&sinceDate={quote_plus(since_date)}&toDate={quote_plus(to_date)}"
            
            logger.info(f"查詢 AdSet {adset_name} 報表: {target_url}")
            
            try:
                # 發送請求到目標 API
                response = requests.get(target_url, headers=headers, timeout=90)
                
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
                'original_adsets': original_adset_count,
                'filtered_out_adsets': len(filtered_out_adsets),
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
@login_required
def vote_ad():
    """投票廣告頁面"""
    form_data = session.get('form_data', {})
    if 'vote_options' not in form_data:
        form_data['vote_options'] = []
    return render_template('vote_ad.html', **form_data)

@main_bp.route('/clear-vote-form', methods=['POST'])
def clear_vote_form():
    """清除投票廣告表單數據"""
    session.pop('form_data', None)
    flash("表單內容已清除", 'info')
    return redirect(url_for('main.vote_ad'))

@main_bp.route('/gif-ad')
@login_required
def gif_ad():
    """GIF 廣告頁面"""
    form_data = session.get('form_data', {})
    return render_template('gif_ad.html', **form_data)

@main_bp.route('/clear-gif-form', methods=['POST'])
def clear_gif_form():
    """清除 GIF 廣告表單數據"""
    session.pop('form_data', None)
    flash("表單內容已清除", 'info')
    return redirect(url_for('main.gif_ad'))

@main_bp.route('/slide-ad')
@login_required
def slide_ad():
    """水平 Slide 廣告頁面"""
    form_data = session.get('form_data', {})
    if 'slide_items' not in form_data:
        form_data['slide_items'] = []
    return render_template('slide_ad.html', **form_data)

@main_bp.route('/clear-slide-form', methods=['POST'])
def clear_slide_form():
    """清除水平 Slide 廣告表單數據"""
    session.pop('form_data', None)
    flash("表單內容已清除", 'info')
    return redirect(url_for('main.slide_ad'))

@main_bp.route('/vertical-slide-ad')
@login_required
def vertical_slide_ad():
    """垂直 Slide 廣告頁面"""
    form_data = session.get('form_data', {})
    if 'slide_items' not in form_data:
        form_data['slide_items'] = []
    return render_template('vertical_slide_ad.html', **form_data)

@main_bp.route('/clear-vertical-slide-form', methods=['POST'])
def clear_vertical_slide_form():
    """清除垂直 Slide 廣告表單數據"""
    session.pop('form_data', None)
    flash("表單內容已清除", 'info')
    return redirect(url_for('main.vertical_slide_ad'))

@main_bp.route('/vertical-cube-slide-ad')
@login_required
def vertical_cube_slide_ad():
    """垂直 Cube Slide 廣告頁面"""
    form_data = session.get('form_data', {})
    if 'slide_items' not in form_data:
        form_data['slide_items'] = []
    return render_template('vertical_cube_slide_ad.html', **form_data)

@main_bp.route('/clear-vertical-cube-slide-form', methods=['POST'])
def clear_vertical_cube_slide_form():
    """清除垂直 Cube Slide 廣告表單數據"""
    session.pop('form_data', None)
    flash("表單內容已清除", 'info')
    return redirect(url_for('main.vertical_cube_slide_ad'))

@main_bp.route('/countdown-ad')
@login_required
def countdown_ad():
    """倒數廣告頁面"""
    form_data = session.get('form_data', {})
    return render_template('countdown_ad.html', **form_data)

@main_bp.route('/clear-countdown-form', methods=['POST'])
def clear_countdown_form():
    """清除倒數廣告表單數據"""
    session.pop('form_data', None)
    flash("表單內容已清除", 'info')
    return redirect(url_for('main.countdown_ad'))

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
        
        # 實際調用 rich_media 腳本建立廣告
        try:
            # 準備 payload - 投票廣告使用 payload_vote_widget
            payload_vote_widget = request.form.get('payload_vote_widget', '')
            if not payload_vote_widget:
                flash("投票套件 payload 不能為空", 'error')
                return redirect(url_for('main.vote_ad'))
            
            # 將投票 payload 轉換為遊戲套件 payload 格式，以便使用 rich_media 腳本
            ad_data['payload_game_widget'] = payload_vote_widget
            ad_data['background_url'] = ad_data.get('vote_image', '')  # 使用投票圖片作為背景
            
            # 調用 rich_media 腳本
            with sync_playwright() as playwright:
                result = run_rich_media(playwright, ad_data, 'vote')
            
            if result:
                flash("投票廣告創建成功！", 'success')
                # 不自動清除 session 中的表單數據，讓用戶可以重複使用
            else:
                flash("投票廣告創建失敗", 'error')
                
        except Exception as e:
            logger.error(f"調用 rich_media 腳本時發生錯誤: {str(e)}")
            flash(f"調用 rich_media 腳本時發生錯誤: {str(e)}", 'error')
        
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
        
        # 實際調用 rich_media 腳本建立廣告
        try:
            # 準備 payload
            payload_game_widget = request.form.get('payload_game_widget', '')
            if not payload_game_widget:
                flash("遊戲套件 payload 不能為空", 'error')
                return redirect(url_for('main.slide_ad'))
            
            # 將 payload 添加到 ad_data 中
            ad_data['payload_game_widget'] = payload_game_widget
            
            # 調用 rich_media 腳本
            with sync_playwright() as playwright:
                result = run_rich_media(playwright, ad_data, 'slide')
            
            if result:
                flash("水平 Slide 廣告創建成功！", 'success')
                # 不自動清除 session 中的表單數據，讓用戶可以重複使用
            else:
                flash("水平 Slide 廣告創建失敗", 'error')
                
        except Exception as e:
            logger.error(f"調用 rich_media 腳本時發生錯誤: {str(e)}")
            flash(f"調用 rich_media 腳本時發生錯誤: {str(e)}", 'error')
        
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
        
        # 實際調用 rich_media 腳本建立廣告
        try:
            # 準備 payload
            payload_game_widget = request.form.get('payload_game_widget', '')
            if not payload_game_widget:
                flash("遊戲套件 payload 不能為空", 'error')
                return redirect(url_for('main.vertical_slide_ad'))
            
            # 將 payload 添加到 ad_data 中
            ad_data['payload_game_widget'] = payload_game_widget
            
            # 調用 rich_media 腳本
            with sync_playwright() as playwright:
                result = run_rich_media(playwright, ad_data, 'vertical_slide')
            
            if result:
                flash("垂直 Slide 廣告創建成功！", 'success')
                # 不自動清除 session 中的表單數據，讓用戶可以重複使用
            else:
                flash("垂直 Slide 廣告創建失敗", 'error')
                
        except Exception as e:
            logger.error(f"調用 rich_media 腳本時發生錯誤: {str(e)}")
            flash(f"調用 rich_media 腳本時發生錯誤: {str(e)}", 'error')
        
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
        
        # 實際調用 rich_media 腳本建立廣告
        try:
            # 準備 payload
            payload_game_widget = request.form.get('payload_game_widget', '')
            if not payload_game_widget:
                flash("遊戲套件 payload 不能為空", 'error')
                return redirect(url_for('main.vertical_cube_slide_ad'))
            
            # 將 payload 添加到 ad_data 中
            ad_data['payload_game_widget'] = payload_game_widget
            
            # 調用 rich_media 腳本
            with sync_playwright() as playwright:
                result = run_rich_media(playwright, ad_data, 'vertical_cube_slide')
            
            if result:
                flash("垂直 Cube Slide 廣告創建成功！", 'success')
                # 不自動清除 session 中的表單數據，讓用戶可以重複使用
            else:
                flash("垂直 Cube Slide 廣告創建失敗", 'error')
                
        except Exception as e:
            logger.error(f"調用 rich_media 腳本時發生錯誤: {str(e)}")
            flash(f"調用 rich_media 腳本時發生錯誤: {str(e)}", 'error')
        
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
        
        # 實際調用 rich_media 腳本建立廣告
        try:
            # 準備 payload
            payload_game_widget = request.form.get('payload_game_widget', '')
            if not payload_game_widget:
                flash("遊戲套件 payload 不能為空", 'error')
                return redirect(url_for('main.countdown_ad'))
            
            # 將 payload 添加到 ad_data 中
            ad_data['payload_game_widget'] = payload_game_widget
            
            # 調用 rich_media 腳本
            with sync_playwright() as playwright:
                result = run_rich_media(playwright, ad_data, 'countdown')
            
            if result:
                flash("倒數廣告創建成功！", 'success')
                # 不自動清除 session 中的表單數據，讓用戶可以重複使用
            else:
                flash("倒數廣告創建失敗", 'error')
                
        except Exception as e:
            logger.error(f"調用 rich_media 腳本時發生錯誤: {str(e)}")
            flash(f"調用 rich_media 腳本時發生錯誤: {str(e)}", 'error')
        
    except Exception as e:
        logger.error(f"創建倒數廣告時發生錯誤: {str(e)}")
        flash(f"創建倒數廣告時發生錯誤: {str(e)}", 'error')
    
    return redirect(url_for('main.countdown_ad'))

@main_bp.route('/create-gif-ad', methods=['POST'])
def create_gif_ad():
    """處理 GIF 廣告創建"""
    try:
        # 獲取基本表單數據
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
            session[f'gif_{key}'] = value
        
        # 實際調用 rich_media 腳本建立廣告
        try:
            # 準備 payload
            payload_game_widget = request.form.get('payload_game_widget', '')
            if not payload_game_widget:
                flash("遊戲套件 payload 不能為空", 'error')
                return redirect(url_for('main.gif_ad'))
            
            # 將 payload 添加到 ad_data 中
            ad_data['payload_game_widget'] = payload_game_widget
            
            # 調用 rich_media 腳本
            with sync_playwright() as playwright:
                result = run_rich_media(playwright, ad_data, 'gif')
            
            if result:
                flash("GIF 廣告創建成功！", 'success')
                session.pop('form_data', None)
                return redirect(url_for('main.gif_ad'))
            else:
                flash("GIF 廣告創建失敗", 'error')
                return redirect(url_for('main.gif_ad'))
            
        except Exception as e:
            logger.error(f"調用 rich_media 腳本時發生錯誤: {str(e)}")
            flash(f"調用 rich_media 腳本時發生錯誤: {str(e)}", 'error')
            return redirect(url_for('main.gif_ad'))
    
    except Exception as e:
        logger.error(f"創建 GIF 廣告時發生錯誤: {str(e)}")
        flash(f"創建 GIF 廣告時發生錯誤: {str(e)}", 'error')
        return redirect(url_for('main.gif_ad'))

@main_bp.route('/create-treasure-box-ad', methods=['POST'])
def create_treasure_box_ad():
    """處理寶箱廣告創建"""
    try:
        # 獲取基本表單數據（支援來自 index.html 的 treasure_ 前綴欄位）
        ad_data = {
            'adset_id': request.form.get('treasure_adset_id', request.form.get('adset_id', '')),
            'display_name': request.form.get('treasure_display_name', request.form.get('display_name', '')),
            'advertiser': request.form.get('treasure_advertiser', request.form.get('advertiser', '')),
            'main_title': request.form.get('treasure_main_title', request.form.get('main_title', '')),
            'subtitle': request.form.get('treasure_subtitle', request.form.get('subtitle', '')),
            'landing_page': request.form.get('treasure_landing_page', request.form.get('landing_page', '')),
            'call_to_action': request.form.get('treasure_call_to_action', request.form.get('call_to_action', '開啟寶箱')),
            'image_path_m': request.form.get('image_path_m', ''),
            'image_path_s': request.form.get('image_path_s', ''),
            
            # rich_media 腳本需要的 background_url 欄位 (對應 background_image)
            'background_url': request.form.get('background_image', ''),
            
            # 寶箱廣告特定欄位（支援 treasure_ 前綴）
            'img_logo': request.form.get('treasure_img_logo', request.form.get('img_logo', '')),
            'img_background': request.form.get('treasure_img_background', request.form.get('img_background', '')),
            'img_item_idle': request.form.get('treasure_img_item_idle', request.form.get('img_item_idle', '')),
            'img_item_pressed': request.form.get('treasure_img_item_pressed', request.form.get('img_item_pressed', '')),
            'img_item_activated': request.form.get('treasure_img_item_activated', request.form.get('img_item_activated', '')),
            'items_active_1': request.form.get('treasure_items_active_1', request.form.get('items_active_1', '')),
            'items_idle_1': request.form.get('treasure_items_idle_1', request.form.get('items_idle_1', '')),
            'items_active_2': request.form.get('treasure_items_active_2', request.form.get('items_active_2', '')),
            'items_idle_2': request.form.get('treasure_items_idle_2', request.form.get('items_idle_2', '')),
            'items_active_3': request.form.get('treasure_items_active_3', request.form.get('items_active_3', '')),
            'items_idle_3': request.form.get('treasure_items_idle_3', request.form.get('items_idle_3', ''))
        }
        
        # 保存表單數據到 session
        session['treasure_box_form_data'] = ad_data
        
        # 建構寶箱專用的 payload_game_widget
        treasure_box_payload = {
            "type": "CHEST",
            "data": {
                "items": [
                    {
                        "active": ad_data.get('items_active_1', ''),
                        "idle": ad_data.get('items_idle_1', '')
                    },
                    {
                        "active": ad_data.get('items_active_2', ''),
                        "idle": ad_data.get('items_idle_2', '')
                    },
                    {
                        "active": ad_data.get('items_active_3', ''),
                        "idle": ad_data.get('items_idle_3', '')
                    }
                ],
                "img_logo": ad_data.get('img_logo', ''),
                "img_background": ad_data.get('img_background', ''),
                "img_item_idle": ad_data.get('img_item_idle', ''),
                "img_item_pressed": ad_data.get('img_item_pressed', ''),
                "img_item_activated": ad_data.get('img_item_activated', '')
            }
        }
        
        # 將 payload 和廣告類型添加到 ad_data
        ad_data['payload_game_widget'] = json.dumps(treasure_box_payload, ensure_ascii=False)
        ad_data['ad_type'] = 'treasure_box'
        
        # 實際調用 rich_media 腳本建立廣告
        try:
            # 調用 rich_media 腳本
            with sync_playwright() as playwright:
                result = run_rich_media(playwright, ad_data, 'treasure_box')
            
            if result:
                flash("寶箱廣告創建成功！", 'success')
                return redirect(url_for('main.treasure_box_ad'))
            else:
                flash("寶箱廣告創建失敗", 'error')
                return redirect(url_for('main.treasure_box_ad'))
                
        except Exception as e:
            logger.error(f"調用 rich_media 腳本時發生錯誤: {str(e)}")
            flash(f"調用 rich_media 腳本時發生錯誤: {str(e)}", 'error')
            return redirect(url_for('main.treasure_box_ad'))
    
    except Exception as e:
        logger.error(f"創建寶箱廣告時發生錯誤: {str(e)}")
        flash(f"創建寶箱廣告時發生錯誤: {str(e)}", 'error')
        return redirect(url_for('main.treasure_box_ad'))

def parse_popup_payloads(form_data):
    """從表單數據中解析 payload_popup_json 和 payload_game_widget。"""
    popup_payload = {}
    payload_popup_json = form_data.get('payload_popup_json', '{}')
    payload_game_widget = form_data.get('payload_game_widget', '{}')

    try:
        popup_data = json.loads(payload_popup_json)
        if isinstance(popup_data, dict) and 'popupList' in popup_data and len(popup_data['popupList']) >= 3:
            video_item = popup_data['popupList'][1]
            image_item = popup_data['popupList'][2]
            
            popup_payload['video_url'] = video_item.get('url')
            if video_item.get('actionList'):
                popup_payload['video_landing_url'] = video_item['actionList'][0].get('payload', {}).get('browser', {}).get('url')
            
            popup_payload['image_source_url'] = image_item.get('imgUrl')
            popup_payload['image_landing_url'] = image_item.get('url')

    except (json.JSONDecodeError, IndexError, KeyError) as e:
        logger.warning(f"解析 payload_popup_json 時出錯: {e}")

    try:
        game_widget_data = json.loads(payload_game_widget)
        if isinstance(game_widget_data, dict):
            popup_payload['img_background'] = game_widget_data.get('data', {}).get('img_background')
            
    except json.JSONDecodeError as e:
        logger.warning(f"解析 payload_game_widget 時出錯: {e}")

    return popup_payload

@main_bp.route('/native-video-ad')
@login_required
def native_video_ad():
    """原生彈跳影音廣告頁面"""
    form_data = session.pop('form_data', {})
    
    # 解析 payload
    popup_payload = parse_popup_payloads(form_data)
    
    # 將解析後的 payload 加入 form_data
    form_data['popup_payload'] = popup_payload
    
    return render_template('native_video_ad.html', **form_data)

@main_bp.route('/create-native-video-ad', methods=['POST'])
def create_native_video_ad():
    """處理原生彈跳影音廣告創建請求"""
    form_data = request.form.to_dict()
    session['form_data'] = form_data
    logger.info(f"收到原生彈跳影音廣告創建請求: {form_data}")

    required_fields = ['adset_id', 'advertiser', 'main_title', 'landing_page', 'image_path_m', 'image_path_s', 'background_image']
    if not all(form_data.get(field) for field in required_fields):
        flash('請填寫所有必填欄位。', 'error')
        return redirect(url_for('main.native_video_ad'))

    # 準備 ad_data
    ad_data = {
        'adset_id': form_data.get('adset_id'),
        'display_name': form_data.get('display_name'),
        'advertiser': form_data.get('advertiser'),
        'main_title': form_data.get('main_title'),
        'subtitle': form_data.get('subtitle'),
        'call_to_action': form_data.get('call_to_action'),
        'landing_page': form_data.get('landing_page'),
        'image_path_m': form_data.get('image_path_m'),
        'image_path_s': form_data.get('image_path_s'),
        'background_url': form_data.get('background_image'), # 注意鍵名匹配
        'payload_game_widget': form_data.get('payload_game_widget'),
        'payload_popupJson': form_data.get('payload_popup_json') # 注意這裡的鍵名
    }

    try:
        with sync_playwright() as p:
            success = run_rich_media(p, ad_data, ad_type='native_video')
        
        if success:
            flash('原生彈T跳影音廣告創建成功！', 'success')
            session.pop('form_data', None)
            return redirect(url_for('main.native_video_ad'))
        else:
            flash('廣告創建過程中發生錯誤，請檢查後台日誌。', 'error')
            return redirect(url_for('main.native_video_ad'))
            
    except Exception as e:
        logger.error(f"創建原生彈跳影音廣告時發生未預期的錯誤: {str(e)}")
        flash(f'創建失敗: {str(e)}', 'error')
        return redirect(url_for('main.native_video_ad'))

@main_bp.route('/clear-native-video-form', methods=['POST'])
def clear_native_video_form():
    """清除原生彈跳影音廣告表單數據"""
    keys_to_remove = [key for key in session.keys() if key.startswith('native_video_')]
    for key in keys_to_remove:
        session.pop(key, None)
    flash("表單內容已清除", 'info')
    return redirect(url_for('main.native_video_ad'))

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
        adsets = list(adset_collection.find({'campId': campaign_id}, {'uuid': 1, 'name': 1, '_id': 0}))
        
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
        tkrecorder_url = f"https://tkrecorder.example.com/sp/list/v/{uuid}"
        
        logger.info(f"[Cut Data] 正在查詢 tkrecorder: {tkrecorder_url}")
        
        # 增加超時時間至 3 分鐘，並加強錯誤處理
        # 使用更長的超時時間，因為 tkrecorder API 可能需要處理大量數據
        timeout_duration = 240  # 4 分鐘
        max_retries = 2
        retry_delay = 5  # 5 秒重試間隔
        
        for attempt in range(max_retries):
            try:
                logger.info(f"[Cut Data] 嘗試查詢 tkrecorder (第 {attempt + 1}/{max_retries} 次): {tkrecorder_url}")
                response = requests.get(tkrecorder_url, timeout=timeout_duration)
                break  # 成功時跳出重試循環
            except requests.Timeout:
                if attempt < max_retries - 1:
                    logger.warning(f"[Cut Data] tkrecorder API 請求超時 (第 {attempt + 1}/{max_retries} 次)，{retry_delay} 秒後重試...")
                    import time
                    time.sleep(retry_delay)
                    continue
                else:
                    raise  # 最後一次嘗試失敗時拋出異常
        
        if response.status_code != 200:
            logger.warning(f"[Cut Data] tkrecorder API 請求失敗: HTTP {response.status_code}")
            return jsonify({'error': f'tkrecorder API 請求失敗: {response.status_code}'}), 500
        
        data = response.json()
        
        # 簡單統計 cut 數據
        success_data = data.get('success', {})
        cut_count = len(success_data) if success_data else 0
        total_clicks = 0
        
        if success_data:
            for cut_info in success_data.values():
                if isinstance(cut_info, list):
                    total_clicks += sum(item.get('totalCount', 0) for item in cut_info)
        
        logger.info(f"[Cut Data] AdUnit {uuid}: 找到 {cut_count} 個 cut，總點擊 {total_clicks}")
        
        return jsonify({
            'success': True,
            'uuid': uuid,
            'data': data,
            'summary': {
                'cut_count': cut_count,
                'total_clicks': total_clicks
            }
        })
        
    except requests.Timeout as e:
        logger.error(f"[Cut Data] tkrecorder API 請求超時: {str(e)}")
        return jsonify({'error': 'tkrecorder API 請求超時，請稍後再試'}), 500
    except requests.RequestException as e:
        logger.error(f"[Cut Data] 請求 tkrecorder API 時發生錯誤: {str(e)}")
        return jsonify({'error': f'請求失敗: {str(e)}'}), 500
    except Exception as e:
        logger.error(f"[Cut Data] 查詢 cut 數據時發生錯誤: {str(e)}")
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
        adsets = list(adset_collection.find({'campId': campaign_id}, {'uuid': 1, 'name': 1, '_id': 0}))
        
        if not adsets:
            return jsonify({'error': f'找不到廣告活動 ID: {campaign_id} 的任何廣告集'}), 404
        
        # 過濾掉名稱包含 "demo" 的 AdSet
        original_adset_count = len(adsets)
        filtered_adsets = []
        filtered_out_adsets = []
        
        for adset in adsets:
            adset_name = adset.get('name', '').lower()
            if 'demo' in adset_name:
                filtered_out_adsets.append(adset)
                logger.info(f"過濾掉包含 demo 的 AdSet: {adset.get('name')}")
            else:
                filtered_adsets.append(adset)
        
        if not filtered_adsets:
            logger.warning(f"過濾後沒有可用的 AdSet (原有 {original_adset_count} 個，全部包含 demo)")
            return jsonify({'error': f'該廣告活動的所有廣告集都包含 demo，已被過濾'}), 404
        
        logger.info(f"AdSet 過濾結果: {len(filtered_adsets)}/{original_adset_count} 個可用 ({len(filtered_out_adsets)} 個包含 demo 被過濾)")
        
        # 取得過濾後的 AdSet ID
        adset_ids = [adset['uuid'] for adset in filtered_adsets]
        adsets = filtered_adsets  # 更新 adsets 變數為過濾後的結果
        
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
        headers = _build_proxy_headers()
        
        def fetch_adunit_report(adunit):
            """查詢單個 AdUnit 報表的函數"""
            adunit_uuid = adunit.get('uuid')
            adunit_name = adunit.get('title') or adunit.get('name') or adunit_uuid[:8]
            adset_id = adunit.get('setId')
            adset_name = adset_names.get(adset_id, '未知廣告集')
            
            # 構建目標 URL
            base_url = f"https://adplatform.example.com/dontblockme/action_adset_read/getadunitreporttemplate/?setId={quote_plus(adset_id)}&uuid={quote_plus(adunit_uuid)}"
            
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
                'total_adsets': len(adsets),  # 過濾後的 AdSet 數量
                'total_adunits': len(adunits),  # 過濾後的 AdUnit 數量
                'successful_reports': len(successful_reports),
                'failed_reports': len(adunits) - len(successful_reports),
                'query_duration': query_duration,
                'query_delay': query_delay,
                'processing_method': 'sequential_processing',
                'filtered_adsets': len(filtered_out_adsets),  # 被過濾的 AdSet 數量
                'original_adset_count': original_adset_count  # 原始 AdSet 總數
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
            'Referer': 'https://adplatform.example.com/'
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

@main_bp.route('/popup-video-ad')
@login_required
def popup_video_ad():
    """原生彈跳影音廣告頁面"""
    form_data = session.get('form_data', {})
    
    # 解析 payload
    popup_payload = parse_popup_payloads(form_data)
    
    # 將解析後的 payload 加入 form_data
    form_data['popup_payload'] = popup_payload
    
    return render_template('popup_video_ad.html', **form_data)

@main_bp.route('/create-popup-video-ad', methods=['POST'])
def create_popup_video_ad():
    """處理原生彈跳影音廣告創建請求"""
    form_data = request.form.to_dict()
    session['form_data'] = form_data
    logger.info(f"收到原生彈跳影音廣告創建請求: {form_data}")

    required_fields = ['adset_id', 'advertiser', 'main_title', 'landing_page', 'image_path_m', 'image_path_s', 'background_image']
    if not all(form_data.get(field) for field in required_fields):
        flash('請填寫所有必填欄位。', 'error')
        return redirect(url_for('main.popup_video_ad'))

    # 準備 ad_data
    ad_data = {
        'adset_id': form_data.get('adset_id'),
        'display_name': form_data.get('display_name'),
        'advertiser': form_data.get('advertiser'),
        'main_title': form_data.get('main_title'),
        'subtitle': form_data.get('subtitle'),
        'call_to_action': form_data.get('call_to_action'),
        'landing_page': form_data.get('landing_page'),
        'image_path_m': form_data.get('image_path_m'),
        'image_path_s': form_data.get('image_path_s'),
        'background_url': form_data.get('background_image'), # 注意鍵名匹配
        'payload_game_widget': form_data.get('payload_game_widget'),
        'payload_popupJson': form_data.get('payload_popup_json') # 注意這裡的鍵名
    }

    try:
        with sync_playwright() as p:
            success = run_rich_media(p, ad_data, ad_type='native_video')
        
        if success:
            session.pop('form_data', None)
            return redirect(url_for('main.popup_video_ad'))
        else:
            flash('廣告創建過程中發生錯誤，請檢查後台日誌。', 'error')
            return redirect(url_for('main.popup_video_ad'))
            
    except Exception as e:
        logger.error(f"創建原生彈跳影音廣告時發生未預期的錯誤: {str(e)}")
        flash(f'創建失敗: {str(e)}', 'error')
        return redirect(url_for('main.popup_video_ad'))

@main_bp.route('/clear-popup-video-form', methods=['POST'])
def clear_popup_video_form():
    """清除原生彈跳影音廣告表單數據"""
    session.pop('form_data', None)
    flash("表單內容已清除", 'info')
    return redirect(url_for('main.popup_video_ad'))

@main_bp.route('/popup-video-slide-ad')
@login_required
def popup_video_slide_ad():
    """原生彈跳影音滑動廣告頁面"""
    form_data = session.get('form_data_slide', {})
    
    # 解析 payload
    popup_payload = parse_popup_payloads(form_data)
    
    # 將解析後的 payload 加入 form_data
    form_data['popup_payload'] = popup_payload
    
    return render_template('popup_video_slide.html', **form_data)

@main_bp.route('/create-popup-video-slide-ad', methods=['POST'])
def create_popup_video_slide_ad():
    """處理原生彈跳影音滑動廣告創建請求"""
    form_data = request.form.to_dict()
    session['form_data_slide'] = form_data
    logger.info(f"收到原生彈跳影音滑動廣告創建請求: {form_data}")

    required_fields = ['adset_id', 'advertiser', 'main_title', 'landing_page', 'image_path_m', 'image_path_s', 'background_image']
    if not all(form_data.get(field) for field in required_fields):
        flash('請填寫所有必填欄位。', 'error')
        return redirect(url_for('main.popup_video_slide_ad'))

    # 準備 ad_data
    ad_data = {
        'adset_id': form_data.get('adset_id'),
        'display_name': form_data.get('display_name'),
        'advertiser': form_data.get('advertiser'),
        'main_title': form_data.get('main_title'),
        'subtitle': form_data.get('subtitle'),
        'call_to_action': form_data.get('call_to_action'),
        'landing_page': form_data.get('landing_page'),
        'image_path_m': form_data.get('image_path_m'),
        'image_path_s': form_data.get('image_path_s'),
        'background_url': form_data.get('background_image'), # 注意鍵名匹配
        'payload_game_widget': form_data.get('payload_game_widget'),
        'payload_popupJson': form_data.get('payload_popup_json') # 注意這裡的鍵名
    }

    try:
        with sync_playwright() as p:
            success = run_rich_media(p, ad_data, ad_type='native_video')
        
        if success:
            session.pop('form_data_slide', None)
            return redirect(url_for('main.popup_video_slide_ad'))
        else:
            flash('廣告創建過程中發生錯誤，請檢查後台日誌。', 'error')
            return redirect(url_for('main.popup_video_slide_ad'))
            
    except Exception as e:
        logger.error(f"創建原生彈跳影音滑動廣告時發生未預期的錯誤: {str(e)}")
        flash(f'創建失敗: {str(e)}', 'error')
        return redirect(url_for('main.popup_video_slide_ad'))

@main_bp.route('/clear-popup-video-slide-form', methods=['POST'])
def clear_popup_video_slide_form():
    """清除原生彈跳影音滑動廣告表單數據"""
    session.pop('form_data_slide', None)
    flash("表單內容已清除", 'info')
    return redirect(url_for('main.popup_video_slide_ad'))

@main_bp.route('/api/save-form-data', methods=['POST'])
def save_form_data():
    """非同步儲存表單資料到 session"""
    try:
        data = request.form.to_dict()
        if data:
            # 檢查是否為滑動版本的表單
            if 'popup_video_url' in data or 'slide_autoplay_delay' in data:
                session['form_data_slide'] = data
            else:
                session['form_data'] = data
            session.modified = True
            return jsonify({'status': 'success', 'message': 'Form data saved.'})
        return jsonify({'status': 'nodata', 'message': 'No data received.'})
    except Exception as e:
        logger.error(f"Error saving form data to session: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@main_bp.route('/treasure-box-ad')
@login_required
def treasure_box_ad():
    """寶箱廣告頁面"""
    form_data = session.get('treasure_box_form_data', {})
    return render_template('treasure_box_ad.html', form_data=form_data)

@main_bp.route('/clear-treasure-box-form', methods=['POST'])
def clear_treasure_box_form():
    """清除寶箱廣告表單數據"""
    session.pop('treasure_box_form_data', None)
    flash("表單內容已清除", 'info')
    return redirect(url_for('main.treasure_box_ad'))

@main_bp.route('/create_ad_route', methods=['POST'])
def create_ad_route():
    """根據 active_tab 參數決定創建哪種類型的廣告"""
    try:
        active_tab = request.form.get('active_tab', 'native-ad')
        
        # 根據 active_tab 重定向到對應的創建函數
        if active_tab == 'native-ad':
            # 重定向到原生廣告創建
            from .native_ad import create_native_ad
            return create_native_ad()
        elif active_tab == 'gif-ad':
            # 需要重新映射字段名稱（去掉 gif_ 前綴）
            adjusted_form_data = {}
            for key, value in request.form.items():
                if key.startswith('gif_'):
                    adjusted_form_data[key[4:]] = value  # 移除 'gif_' 前綴
                else:
                    adjusted_form_data[key] = value
            
            # 創建一個新的 request.form 對象
            from werkzeug.datastructures import ImmutableMultiDict
            request.form = ImmutableMultiDict(adjusted_form_data)
            
            return create_gif_ad()
        elif active_tab == 'slide-ad':
            # 類似處理其他廣告類型...
            flash("水平 Slide 廣告創建功能尚未實現", 'warning')
            return redirect(url_for('main.index'))
        elif active_tab == 'vertical-slide-ad':
            flash("垂直 Slide 廣告創建功能尚未實現", 'warning')
            return redirect(url_for('main.index'))
        elif active_tab == 'vertical-cube-slide-ad':
            flash("垂直 Cube Slide 廣告創建功能尚未實現", 'warning')
            return redirect(url_for('main.index'))
        elif active_tab == 'treasure-box-ad':
            # 直接處理寶箱廣告創建
            try:
                # 獲取基本表單數據（支援 treasure_ 前綴欄位）
                ad_data = {
                    'adset_id': request.form.get('treasure_adset_id', ''),
                    'display_name': request.form.get('treasure_display_name', ''),
                    'advertiser': request.form.get('treasure_advertiser', ''),
                    'main_title': request.form.get('treasure_main_title', ''),
                    'subtitle': request.form.get('treasure_subtitle', ''),
                    'landing_page': request.form.get('treasure_landing_page', ''),
                    'call_to_action': request.form.get('treasure_call_to_action', '開啟寶箱'),
                    'image_path_m': request.form.get('image_path_m', ''),
                    'image_path_s': request.form.get('image_path_s', ''),
                    
                    # 寶箱廣告特定欄位
                    'img_logo': request.form.get('treasure_img_logo', ''),
                    'img_background': request.form.get('treasure_img_background', ''),
                    'img_item_idle': request.form.get('treasure_img_item_idle', ''),
                    'img_item_pressed': request.form.get('treasure_img_item_pressed', ''),
                    'img_item_activated': request.form.get('treasure_img_item_activated', ''),
                    'items_active_1': request.form.get('treasure_items_active_1', ''),
                    'items_idle_1': request.form.get('treasure_items_idle_1', ''),
                    'items_active_2': request.form.get('treasure_items_active_2', ''),
                    'items_idle_2': request.form.get('treasure_items_idle_2', ''),
                    'items_active_3': request.form.get('treasure_items_active_3', ''),
                    'items_idle_3': request.form.get('treasure_items_idle_3', ''),
                    'url_interactive_a': request.form.get('treasure_url_interactive_a', ''),
                    'url_interactive_b': request.form.get('treasure_url_interactive_b', ''),
                    'url_interactive_c': request.form.get('treasure_url_interactive_c', '')
                }
                
                # 保存表單數據到 session
                session['treasure_box_form_data'] = ad_data
                
                # 建構寶箱專用的 payload_game_widget
                treasure_box_payload = {
                    "type": "CHEST",
                    "data": {
                        "items": [
                            {
                                "active": ad_data.get('items_active_1', ''),
                                "idle": ad_data.get('items_idle_1', '')
                            },
                            {
                                "active": ad_data.get('items_active_2', ''),
                                "idle": ad_data.get('items_idle_2', '')
                            },
                            {
                                "active": ad_data.get('items_active_3', ''),
                                "idle": ad_data.get('items_idle_3', '')
                            }
                        ],
                        "img_logo": ad_data.get('img_logo', ''),
                        "img_background": ad_data.get('img_background', ''),
                        "img_item_idle": ad_data.get('img_item_idle', ''),
                        "img_item_pressed": ad_data.get('img_item_pressed', ''),
                        "img_item_activated": ad_data.get('img_item_activated', '')
                    }
                }
                
                # 建構 urlInteractivePopups
                url_interactive_popups = [
                    {
                        "key": "a",
                        "url": ad_data.get('url_interactive_a', '')
                    },
                    {
                        "key": "b", 
                        "url": ad_data.get('url_interactive_b', '')
                    },
                    {
                        "key": "c",
                        "url": ad_data.get('url_interactive_c', '')
                    }
                ]
                
                # 將 payload 和 urlInteractivePopups 添加到 ad_data
                import json
                ad_data['payload_game_widget'] = json.dumps(treasure_box_payload, ensure_ascii=False)
                ad_data['urlInteractivePopups'] = json.dumps(url_interactive_popups, ensure_ascii=False)
                
                # 實際調用 rich_media 腳本建立廣告
                try:
                    with sync_playwright() as p:
                        result = run_rich_media(p, ad_data, 'treasure_box')
                    
                    if result:
                        flash("寶箱廣告創建成功！", 'success')
                    else:
                        flash("寶箱廣告創建失敗", 'error')
                        
                    return redirect(url_for('main.index'))
                    
                except Exception as e:
                    logger.error(f"調用 rich_media 時發生錯誤: {str(e)}")
                    flash(f"寶箱廣告創建失敗: {str(e)}", 'error')
                    return redirect(url_for('main.index'))
                    
            except Exception as e:
                logger.error(f"創建寶箱廣告時發生錯誤: {str(e)}")
                flash(f"創建寶箱廣告時發生錯誤: {str(e)}", 'error')
                return redirect(url_for('main.index'))
        else:
            flash(f"未知的廣告類型: {active_tab}", 'error')
            return redirect(url_for('main.index'))
            
    except Exception as e:
        logger.error(f"創建廣告時發生錯誤: {str(e)}")
        flash(f"創建廣告時發生錯誤: {str(e)}", 'error')
        return redirect(url_for('main.index'))
