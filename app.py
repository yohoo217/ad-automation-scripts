from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from playwright.sync_api import sync_playwright
import logging
import os
from werkzeug.utils import secure_filename
from datetime import datetime
import time
import base64
from pymongo import MongoClient
from dotenv import load_dotenv
from urllib.parse import quote_plus

# 載入環境變數
load_dotenv()

# 從修改後的腳本導入 run 函式和 config
from native_adunit_auto_create import run as run_native # type: ignore
from suprad_adunit_auto_create import run as run_suprad # type: ignore
import config # type: ignore

app = Flask(__name__)
app.secret_key = 'your_very_secret_key' # 記得更換為一個安全的密鑰

# MongoDB 配置
MONGO_CONNECTION_STRING = os.getenv('MONGO_CONNECTION_STRING')
MONGO_DATABASE = os.getenv('MONGO_DATABASE', 'trek')

def get_mongo_client():
    """取得 MongoDB 連接"""
    try:
        if MONGO_CONNECTION_STRING:
            client = MongoClient(MONGO_CONNECTION_STRING)
            return client
        else:
            # 備用連線方式（如果環境變數不存在）
            username = os.getenv('MONGO_USERNAME', 'trekread')
            password = os.getenv('MONGO_PASSWORD', 'HNwMUr0NCKZejRMzxLbAWOnRYIrPT9qZuzL0')
            hosts = "172.105.200.150:27017,139.162.91.194:27017,172.105.208.153:27017"
            database = MONGO_DATABASE
            
            connection_string = f"mongodb://{quote_plus(username)}:{quote_plus(password)}@{hosts}/{database}?replicaSet=rs0&authMechanism=SCRAM-SHA-1"
            client = MongoClient(connection_string)
            return client
    except Exception as e:
        logger.error(f"MongoDB 連接失敗: {str(e)}")
        return None

def get_adunit_by_uuid(uuid):
    """根據 UUID 從 MongoDB 取得 AdUnit 資料"""
    try:
        client = get_mongo_client()
        if not client:
            return None
            
        db = client[MONGO_DATABASE]
        collection = db['AdUnit']
        
        # 查詢 AdUnit
        adunit = collection.find_one({"uuid": uuid})
        return adunit
        
    except Exception as e:
        logger.error(f"查詢 AdUnit 時發生錯誤: {str(e)}")
        return None
    finally:
        if client:
            client.close()

def build_screenshot_url(adunit_data):
    """根據 AdUnit 資料建構截圖網址"""
    if not adunit_data:
        return None
        
    base_url = "https://trek.aotter.net/trek-ad-preview/pages/ptt-article/index.html"
    
    # 從 AdUnit 資料中取得相關欄位
    media_title = adunit_data.get('title', '')
    media_desc = adunit_data.get('text', '')
    media_sponsor = adunit_data.get('advertiserName', '')
    media_cta = adunit_data.get('callToAction', '')
    url_original = adunit_data.get('url_original', '')
    uuid = adunit_data.get('uuid', '')
    
    # 建構 catrun 網址
    catrun_url = f"https://tkcatrun.aotter.net/b/{uuid}/1200x628"
    
    # 建構完整的網址參數
    params = [
        f"media-title={quote_plus(media_title)}",
        f"media-cta={quote_plus(media_cta)}",
        f"media-desc={quote_plus(media_desc)}",
        f"media-sponsor={quote_plus(media_sponsor)}",
        f"media-url={quote_plus(url_original)}",
        f"trek-debug-place=5a41c4d0-b268-43b2-9536-d774f46c33bf",
        f"trek-debug-catrun={quote_plus(catrun_url)}",
        f"dataSrcUrl=https%3A%2F%2Fwww.ptt.cc%2Fbbs%2FBabyMother%2FM.1724296474.A.887.html"
    ]
    
    full_url = f"{base_url}?{'&'.join(params)}"
    return full_url

# 配置上傳文件夾
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 限制上傳大小為 16MB

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 確保日誌目錄存在
if not os.path.exists('logs'):
    os.makedirs('logs')

# 主頁重定向到原生廣告頁面
@app.route('/')
def index():
    return redirect(url_for('native_ad'))

# 原生廣告頁面
@app.route('/native-ad')
def native_ad():
    # 從 session 獲取之前填寫的表單數據
    form_data = {
        'adset_id': session.get('adset_id', ''),
        'display_name': session.get('display_name', ''),
        'advertiser': session.get('advertiser', ''),
        'main_title': session.get('main_title', ''),
        'subtitle': session.get('subtitle', ''),
        'landing_page': session.get('landing_page', ''),
        'call_to_action': session.get('call_to_action', '瞭解詳情'),
        'tracking_url': session.get('tracking_url', ''),
        'image_path_m': session.get('image_path_m', ''),
        'image_path_o': session.get('image_path_o', ''),
        'image_path_p': session.get('image_path_p', ''),
        'image_path_s': session.get('image_path_s', '')
    }
    return render_template('native_ad.html', **form_data)

# 投票廣告頁面
@app.route('/vote-ad')
def vote_ad():
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

# GIF 廣告頁面
@app.route('/gif-ad')
def gif_ad():
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

# 水平 Slide 廣告頁面
@app.route('/slide-ad')
def slide_ad():
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
    
    # 嘗試還原水平滑動項目的數據
    slide_items = []
    index = 0
    while True:
        image_url_key = f'image_url_{index}'
        target_url_key = f'target_url_{index}'
        
        if image_url_key in session and target_url_key in session:
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

# 垂直 Slide 廣告頁面
@app.route('/vertical-slide-ad')
def vertical_slide_ad():
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
    
    # 嘗試還原垂直滑動項目的數據
    slide_items = []
    index = 0
    while True:
        image_url_key = f'image_url_{index}'
        target_url_key = f'target_url_{index}'
        
        if image_url_key in session and target_url_key in session:
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

# 垂直 Cube Slide 廣告頁面
@app.route('/vertical-cube-slide-ad')
def vertical_cube_slide_ad():
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
    
    # 嘗試還原垂直 Cube 滑動項目的數據
    slide_items = []
    index = 0
    while True:
        image_url_key = f'image_url_{index}'
        target_url_key = f'target_url_{index}'
        
        if image_url_key in session and target_url_key in session:
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

# 倒數廣告頁面
@app.route('/countdown_ad')
def countdown_ad():
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
        'image_cover': session.get('countdown_image_cover', ''),
        'game_winner_bg_color': session.get('countdown_game_winner_bg_color', '#26D07C'),
        'game_winner_text_color': session.get('countdown_game_winner_text_color', '#ffffff'),
        'game_bg_color': session.get('countdown_game_bg_color', '#ffffff'),
        'game_text_color': session.get('countdown_game_text_color', '#000000'),
        'game_border_color': session.get('countdown_game_border_color', '#000000')
    }
    return render_template('countdown_ad.html', **form_data)

# 自動截圖頁面
@app.route('/auto-screenshot')
def auto_screenshot():
    return render_template('auto_screenshot.html')

# Native 廣告多尺寸截圖頁面
@app.route('/native-ad-screenshot')
def native_ad_screenshot():
    return render_template('native_ad_screenshot.html')

# 報表頁面
@app.route('/report')
def report():
    return render_template('report.html')

# 建構 native 廣告截圖網址
def build_native_screenshot_url(adunit_data, size, template):
    """根據 AdUnit 資料和尺寸建構 native 廣告截圖網址"""
    if not adunit_data:
        return None
    
    # 從 AdUnit 資料中取得相關欄位
    media_title = adunit_data.get('title', '')
    media_desc = adunit_data.get('text', '')
    media_sponsor = adunit_data.get('advertiserName', '')
    media_cta = adunit_data.get('callToAction', '')
    url_original = adunit_data.get('url_original', '')
    uuid = adunit_data.get('uuid', '')
    media_img = adunit_data.get('image_path_m', '')
    
    # 建構 catrun 網址
    catrun_url = f"https://tkcatrun.aotter.net/b/{uuid}/{size}"
    
    # 根據尺寸和模板類型選擇對應的 URL 模板
    url_templates = {
        '1200x628': {
            'ptt-article': {
                'base_url': 'https://trek.aotter.net/trek-ad-preview/pages/ptt-article/index.html',
                'dataSrcUrl': 'https%3A%2F%2Fwww.ptt.cc%2Fbbs%2FBabyMother%2FM.1724296474.A.887.html'
            }
        },
        '300x300': {
            'ptt-article-list': {
                'base_url': 'https://trek.aotter.net/trek-ad-preview/pages/ptt-article-list/index.html',
                'dataSrcUrl': 'https%3A%2F%2Fwww.ptt.cc%2Fbbs%2FBabyMother%2Findex.html',
                'lastArticleNumber': '153746'
            }
        },
        '320x50': {
            'ptt-article': {
                'base_url': 'https://trek.aotter.net/trek-ad-preview/pages/ptt-article/index.html',
                'dataSrcUrl': 'https%3A%2F%2Fwww.ptt.cc%2Fbbs%2FBabyMother%2FM.1724296474.A.887.html'
            }
        },
        '300x250': {
            'moptt': {
                'base_url': 'https://moptt.tw/p/Gossiping.M.1718675708.A.183',
                'use_iframe': True
            },
            'ptt-article': {
                'base_url': 'https://trek.aotter.net/trek-ad-preview/pages/ptt-article/index.html',
                'dataSrcUrl': 'https%3A%2F%2Fwww.ptt.cc%2Fbbs%2FBabyMother%2FM.1724296474.A.887.html'
            }
        },
        '640x200': {
            'pnn-article': {
                'base_url': 'https://aotter.github.io/trek-ad-preview/pages/pnn-article/',
                'use_iframe': True
            },
            'ptt-article': {
                'base_url': 'https://trek.aotter.net/trek-ad-preview/pages/ptt-article/index.html',
                'dataSrcUrl': 'https%3A%2F%2Fwww.ptt.cc%2Fbbs%2FBabyMother%2FM.1724296474.A.887.html'
            }
        }
    }
    
    # 根據尺寸和模板決定使用哪個配置
    size_templates = url_templates.get(size, {})
    template_config = size_templates.get(template)
    
    # 如果指定的模板不存在，嘗試使用預設模板
    if not template_config:
        if size == '300x300':
            template_config = size_templates.get('ptt-article-list')
        else:
            template_config = size_templates.get('ptt-article')
    
    if not template_config:
        return None
    
    base_url = template_config.get('base_url')
    if not base_url:
        return None
    
    # 根據不同模板類型建構參數
    if template == 'ptt-article-list' and size == '300x300':
        params = [
            f"media-url={quote_plus(url_original)}",
            f"media-title={quote_plus(media_title)}",
            f"media-desc={quote_plus(media_desc)}",
            f"media-sponsor={quote_plus(media_sponsor)}",
            f"media-img={quote_plus(media_img)}",
            f"trek-debug-place=5a41c4d0-b268-43b2-9536-d774f46c33bf",
            f"dataSrcUrl={template_config.get('dataSrcUrl', '')}",
            f"lastArticleNumber={template_config.get('lastArticleNumber', '')}"
        ]
    elif template == 'moptt' and size == '300x250':
        # MoPTT 使用 iframe 參數
        params = [
            f"iframe_title={quote_plus(media_title)}",
            f"iframe_desc={quote_plus(media_desc)}",
            f"iframe_sponsor={quote_plus(media_sponsor)}",
            f"iframe_cta={quote_plus(media_cta)}",
            f"iframe_url={quote_plus(url_original)}",
            f"iframe_img={quote_plus(media_img)}",
            f"trek-debug-place=5a41c4d0-b268-43b2-9536-d774f46c33bf",
            f"trek-debug-catrun={quote_plus(catrun_url)}"
        ]
    elif template == 'pnn-article' and size == '640x200':
        # PNN 使用特定參數格式，固定使用指定的 iframe 網址
        fixed_iframe_url = "https://www.ptt.cc/bbs/NBA/M.1701151337.A.E0C.html"
        params = [
            f"iframe-url={quote_plus(fixed_iframe_url)}",
            f"trek-debug-place=f62fc7ee-2629-4977-be97-c92f4ac4ec23",
            f"trek-debug-catrun={quote_plus(catrun_url)}"
        ]
    else:
        # PTT 文章頁面的標準參數
        params = [
            f"media-title={quote_plus(media_title)}",
            f"media-cta={quote_plus(media_cta)}",
            f"media-desc={quote_plus(media_desc)}",
            f"media-sponsor={quote_plus(media_sponsor)}",
            f"trek-debug-place=5a41c4d0-b268-43b2-9536-d774f46c33bf",
            f"trek-debug-catrun={quote_plus(catrun_url)}",
            f"dataSrcUrl={template_config.get('dataSrcUrl', '')}"
        ]
    
    full_url = f"{base_url}?{'&'.join(params)}"
    return full_url

# Native 廣告多尺寸截圖處理
@app.route('/create-native-screenshot', methods=['POST'])
def create_native_screenshot():
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
            from urllib.parse import urlparse
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
                    
                    # 監聽網路請求
                    page.on('request', lambda request: logger.info(f"Network Request > {request.method} {request.url}"))
                    page.on('response', lambda response: logger.info(f"Network Response < {response.status} {response.url}"))
                    
                    # 監聽頁面關閉事件，在關閉前立即截圖
                    page_closed = False
                    emergency_screenshot_taken = False
                    
                    def on_page_close():
                        nonlocal page_closed, emergency_screenshot_taken
                        page_closed = True
                        if not emergency_screenshot_taken:
                            logger.info("頁面即將關閉，立即進行緊急截圖...")
                            try:
                                # 創建緊急截圖目錄
                                today = datetime.now().strftime('%Y%m%d')
                                emergency_dir = os.path.join('uploads', 'screenshots', today, 'emergency')
                                if not os.path.exists(emergency_dir):
                                    os.makedirs(emergency_dir)
                                
                                # 生成緊急截圖檔案名稱
                                timestamp = datetime.now().strftime('%H%M%S')
                                emergency_filename = f'before_close_{size}_{timestamp}.png'
                                emergency_path = os.path.join(emergency_dir, emergency_filename)
                                
                                # 立即截圖
                                page.screenshot(path=emergency_path, full_page=False)
                                emergency_screenshot_taken = True
                                logger.info(f"頁面關閉前緊急截圖已儲存: {emergency_path}")
                            except Exception as emergency_error:
                                logger.error(f"頁面關閉前緊急截圖失敗: {str(emergency_error)}")
                    
                    page.on('close', on_page_close)
                    
                    page.goto(url, wait_until='domcontentloaded', timeout=30000) 
                    logger.info("PNN 頁面 domcontentloaded，等待 3 秒...")
                    
                    # 在等待過程中定期檢查頁面狀態並截圖
                    for i in range(6):  # 分成 6 次，每次 500ms
                        if page_closed:
                            logger.warning("檢測到頁面已關閉，停止等待")
                            break
                        page.wait_for_timeout(500)
                        
                        # 每隔 1 秒進行一次預防性截圖
                        if i % 2 == 0 and not emergency_screenshot_taken:
                            try:
                                today = datetime.now().strftime('%Y%m%d')
                                emergency_dir = os.path.join('uploads', 'screenshots', today, 'emergency')
                                if not os.path.exists(emergency_dir):
                                    os.makedirs(emergency_dir)
                                
                                timestamp = datetime.now().strftime('%H%M%S')
                                preventive_filename = f'preventive_{size}_step{i}_{timestamp}.png'
                                preventive_path = os.path.join(emergency_dir, preventive_filename)
                                
                                page.screenshot(path=preventive_path, full_page=False)
                                logger.info(f"預防性截圖 {i//2+1} 已儲存: {preventive_path}")
                            except Exception as preventive_error:
                                logger.warning(f"預防性截圖失敗: {str(preventive_error)}")

                    if page_closed:
                        logger.warning("頁面在載入過程中被關閉")
                        return  # 直接返回，不繼續處理

                    ad_frame = None
                    try:
                        logger.info("PNN: 嘗試尋找廣告 iframe: iframe[src*=\"tkcatrun.aotter.net\"]")
                        iframe_element = page.wait_for_selector('iframe[src*="tkcatrun.aotter.net"]', timeout=10000)
                        if iframe_element:
                            ad_frame = iframe_element.content_frame()
                            logger.info("PNN: 找到並獲取到廣告 iframe")
                            if ad_frame:
                                logger.info("PNN: 在 iframe 內額外等待 2 秒讓 CatRun 初始化")
                                ad_frame.wait_for_timeout(2000) # 給 CatRun iframe 內部多一點時間
                        else:
                            logger.warning("PNN: 未找到 tkcatrun iframe 的元素")
                    except Exception as fe:
                        logger.warning(f"PNN: 尋找 tkcatrun iframe 時出錯: {str(fe)}.")

                    target_for_ad_wait = ad_frame if ad_frame else page
                    try:
                        logger.info(f"PNN: 在 {'iframe' if ad_frame else '主頁面'} 中等待廣告元素 [data-trek-ad]")
                        target_for_ad_wait.wait_for_selector('[data-trek-ad]', timeout=10000)
                        logger.info("PNN: 廣告元素 [data-trek-ad] 已找到")
                    except Exception as ad_el_err:
                        logger.warning(f"PNN: 未找到 [data-trek-ad] 廣告元素: {str(ad_el_err)}")
                    page.wait_for_timeout(1000) # 等待穩定
                    
                else: # Aotter 內部頁面或其他
                    logger.info(f"處理 aotter/其他頁面 ({template})，使用完整載入策略: {url}")
                    page.goto(url, wait_until='networkidle', timeout=30000)
                    logger.info(f"頁面 ({template}) networkidle，額外等待 2 秒確保穩定")
                    page.wait_for_timeout(2000) # 額外等待，確保 JS 完成
                    
                    try:
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
                logger.warning(f"頁面載入過程中發生警告: {str(page_error)}")
                
                # 如果是 Target closed 錯誤，說明頁面已經關閉
                if "Target page, context or browser has been closed" in str(page_error) or "TargetClosedError" in str(page_error):
                    logger.info("檢測到 Target closed 錯誤，預防性截圖應該已經捕獲了頁面關閉前的狀態")
                    # 不再嘗試截圖，因為頁面已經關閉
                else:
                    # 對於其他類型的錯誤，嘗試重新載入
                    try:
                        logger.info("嘗試重新載入頁面...")
                        page.goto(url, wait_until='load', timeout=15000)
                        page.wait_for_timeout(2000)
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
                        # PNN 640x200 截取整個手機畫面
                        logger.info("PNN 640x200: 等待頁面載入完成，準備截取整個手機畫面")
                        
                        # 等待廣告 iframe 載入（但不截取 iframe，而是截取整頁）
                        try:
                            iframe_el = page.wait_for_selector('iframe[src*="tkcatrun.aotter.net"]', timeout=10000)
                            if iframe_el:
                                logger.info("PNN: 找到廣告 iframe，等待廣告初始化")
                                ad_frame = iframe_el.content_frame()
                                if ad_frame:
                                    # 等待廣告載入完成
                                    ad_frame.wait_for_timeout(3000)
                                    try:
                                        ad_frame.wait_for_selector('[data-trek-ad]', timeout=5000)
                                        logger.info("PNN: 廣告已載入完成")
                                    except:
                                        logger.warning("PNN: 廣告元素載入超時，但繼續截圖")
                            else:
                                logger.warning("PNN: 未找到廣告 iframe")
                        except Exception as iframe_error:
                            logger.warning(f"PNN: 等待 iframe 時發生錯誤: {str(iframe_error)}")
                        
                        # 截取整個手機畫面（viewport）
                        element_to_screenshot = None  # 使用 page.screenshot 截取整個 viewport
                        screenshot_description = "PNN 整個手機畫面 (640x200)"
                        
                        # 確保頁面完全載入
                        page.wait_for_timeout(2000)
                    else:
                        # 其他情況，預設截取主頁面 viewport
                        logger.info(f"預設截圖: 主頁面 viewport for {template} {size}")
                        # element_to_screenshot 保持 None，下面会处理 page.screenshot
                        pass 

                    # 執行截圖
                    if element_to_screenshot: 
                        logger.info(f"準備截圖，目標: {screenshot_description}")
                        # ElementHandle 和 Locator 都有 screenshot 方法
                        element_to_screenshot.screenshot(path=screenshot_path)
                    else:
                        # 如果 element_to_screenshot 未被設置 (例如非 MoPTT/PNN 頁面，或 body 也沒取到)
                        logger.info(f"準備截圖，目標: 主頁面 viewport (full_page=False) for {template} {size}")
                        page.screenshot(path=screenshot_path, full_page=False)

                    logger.info("截圖操作完成")
                    screenshot_success = True
                else:
                    raise Exception("頁面已關閉")
                
            except Exception as screenshot_error:
                logger.error(f"截圖過程中發生錯誤: {str(screenshot_error)}")
                
                # 如果是 Target closed 錯誤，不嘗試重試
                if "Target page, context or browser has been closed" in str(screenshot_error) or "TargetClosedError" in str(screenshot_error):
                    logger.error("頁面已關閉，無法進行截圖重試")
                    raise screenshot_error
                
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

                    elif template == 'pnn-article' and size == '640x200':
                        # PNN 640x200 重試時也截取整個手機畫面
                        logger.info("PNN 640x200 (重試): 準備截取整個手機畫面")
                        
                        # 等待廣告載入（但不截取 iframe）
                        try:
                            iframe_el_retry = page.query_selector('iframe[src*="tkcatrun.aotter.net"]')
                            if iframe_el_retry:
                                ad_frame_retry = iframe_el_retry.content_frame()
                                if ad_frame_retry:
                                    logger.info("PNN (重試): 找到廣告 iframe，等待載入")
                                    ad_frame_retry.wait_for_timeout(2000)
                                    try:
                                        ad_frame_retry.wait_for_selector('[data-trek-ad]', timeout=3000)
                                        logger.info("PNN (重試): 廣告已載入")
                                    except:
                                        logger.warning("PNN (重試): 廣告載入超時")
                            else:
                                logger.warning("PNN (重試): 未找到廣告 iframe")
                        except Exception as retry_iframe_error:
                            logger.warning(f"PNN (重試): iframe 處理錯誤: {str(retry_iframe_error)}")
                        
                        # 截取整個手機畫面
                        retry_element_to_screenshot = None  # 使用 page.screenshot
                        retry_screenshot_description = "PNN 整個手機畫面 (640x200 重試)"
                    
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
            
            # 只有成功截圖才繼續處理檔案
            if not screenshot_success:
                raise Exception("截圖失敗")
            
            # 取得檔案資訊
            absolute_path = os.path.abspath(screenshot_path)
            file_size = os.path.getsize(absolute_path)
            
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
                'preview_url': url_for('screenshot_base64', filename=relative_path),
                'download_url': url_for('screenshot_base64', filename=relative_path)
            })
            
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        logger.error(f"Native 廣告截圖時發生錯誤: {str(e)}")
        logger.error(f"錯誤詳情：\n{error_detail}")
        return jsonify({'success': False, 'error': str(e)}), 500

# 原生廣告創建處理
@app.route('/create_native_ad', methods=['POST'])
def create_native_ad():
    try:
        # 獲取表單數據
        ad_data = {
            'display_name': request.form.get('display_name', ''),
            'advertiser': request.form.get('advertiser', ''),
            'main_title': request.form.get('main_title', ''),
            'subtitle': request.form.get('subtitle', ''),
            'adset_id': request.form.get('adset_id', ''),
            'landing_page': request.form.get('landing_page', ''),
            'call_to_action': request.form.get('call_to_action', '瞭解詳情'),
            'image_path_m': request.form.get('image_path_m', ''),
            'image_path_o': request.form.get('image_path_o', ''),
            'image_path_p': request.form.get('image_path_p', ''),
            'image_path_s': request.form.get('image_path_s', ''),
            'tracking_url': request.form.get('tracking_url', '')
        }
        
        # 保存表單數據到 session（以便失敗時可以重新填充）
        for key, value in ad_data.items():
            session[key] = value
        
        # 驗證必填欄位
        required_fields = ['advertiser', 'main_title', 'adset_id', 'landing_page', 
                          'image_path_m', 'image_path_o', 'image_path_p', 'image_path_s']
        missing_fields = [field for field in required_fields if not ad_data[field]]
        
        if missing_fields:
            flash(f"缺少必填欄位: {', '.join(missing_fields)}", 'error')
            return redirect(url_for('native_ad'))
        
        # 嘗試創建廣告
        logger.info(f"開始創建原生廣告: {ad_data['display_name'] or ad_data['main_title']}")
        
        with sync_playwright() as playwright:
            success = run_native(playwright, ad_data)
        
        if success:
            # 成功後清除 session 中的表單數據
            for key in ad_data.keys():
                session.pop(key, None)
            flash(f"成功創建廣告: {ad_data['display_name'] or ad_data['main_title']}", 'success')
            logger.info(f"成功創建廣告: {ad_data['display_name'] or ad_data['main_title']}")
        else:
            flash("自動創建過程中發生錯誤", 'error')
            logger.error(f"創建廣告失敗: {ad_data['display_name'] or ad_data['main_title']}")
            
    except Exception as e:
        error_msg = str(e)
        logger.error(f"創建原生廣告時發生意外錯誤: {error_msg}")
        
        # 特別處理 TargetClosedError
        if "TargetClosedError" in error_msg or "Target page, context or browser has been closed" in error_msg:
            flash("瀏覽器意外關閉，請稍後再試", 'error')
        else:
            flash(f"創建廣告時發生錯誤: {error_msg}", 'error')
    
    return redirect(url_for('native_ad'))

# 批量廣告創建處理
@app.route('/create_batch_ads', methods=['POST'])
def create_batch_ads():
    # 獲取批量表單數據
    ads_count = int(request.form.get('ads_count', 0))
    success_count = 0
    failed_ads = []
    form_data = {}  # 用於保存所有表單數據
    has_validation_error = False  # 標記是否有驗證錯誤
    
    # 首先收集所有表單數據，以便在驗證失敗時返回
    for i in range(1, ads_count + 1):
        prefix = f'ad{i}_'
        
        # 檢查此廣告表單是否存在
        if request.form.get(f'{prefix}display_name') is None and \
           request.form.get(f'{prefix}advertiser') is None and \
           request.form.get(f'{prefix}adset_id') is None:
            continue
            
        # 儲存這一行的所有數據
        row_data = {}
        for field in ['display_name', 'advertiser', 'main_title', 'subtitle', 
                      'adset_id', 'landing_page', 'call_to_action', 
                      'image_path_m', 'image_path_o', 'image_path_p', 'image_path_s', 
                      'tracking_url']:
            row_data[field] = request.form.get(f'{prefix}{field}', '')
        
        form_data[i] = row_data
    
    # 處理每個廣告
    for i in range(1, ads_count + 1):
        prefix = f'ad{i}_'
        
        # 檢查此廣告表單是否存在在表單集合中
        if i not in form_data:
            continue
            
        ad_data = {
            'display_name': request.form.get(f'{prefix}display_name', ''),
            'advertiser': request.form.get(f'{prefix}advertiser', ''),
            'main_title': request.form.get(f'{prefix}main_title', ''),
            'subtitle': request.form.get(f'{prefix}subtitle', ''),
            'adset_id': request.form.get(f'{prefix}adset_id', ''),
            'landing_page': request.form.get(f'{prefix}landing_page', ''),
            'call_to_action': request.form.get(f'{prefix}call_to_action', '瞭解詳情'),
            'image_path_m': request.form.get(f'{prefix}image_path_m', ''),
            'image_path_o': request.form.get(f'{prefix}image_path_o', ''),
            'image_path_p': request.form.get(f'{prefix}image_path_p', ''),
            'image_path_s': request.form.get(f'{prefix}image_path_s', ''),
            'tracking_url': request.form.get(f'{prefix}tracking_url', '')
        }
        
        # 簡單的驗證
        required_fields = ['advertiser', 'main_title', 'adset_id', 'landing_page', 
                       'image_path_m', 'image_path_o', 'image_path_p', 'image_path_s']
        missing_fields = [field for field in required_fields if not ad_data[field]]
        
        if missing_fields:
            has_validation_error = True
            failed_ads.append({
                'index': i,
                'display_name': ad_data['display_name'] or f'廣告 #{i}',
                'reason': f"缺少必填欄位: {', '.join(missing_fields)}"
            })
            continue
            
        # 如果已經有驗證錯誤，不繼續處理後續廣告，保留表單數據
        if has_validation_error:
            continue
            
        # 嘗試創建廣告
        try:
            # 在每個廣告處理之間增加短暫延遲，避免瀏覽器資源競爭
            if i > 1:  # 如果不是第一個廣告，先等待一下
                time.sleep(2)
                
            logger.info(f"開始處理廣告 #{i}: {ad_data['display_name'] or '(無名稱)'}")
            
            with sync_playwright() as playwright:
                success = run_native(playwright, ad_data)
            
            if success:
                success_count += 1
                logger.info(f"成功創建廣告: {ad_data['display_name'] or f'廣告 #{i}'}")
            else:
                failed_ads.append({
                    'index': i,
                    'display_name': ad_data['display_name'] or f'廣告 #{i}',
                    'reason': "自動創建過程中發生錯誤"
                })
                logger.error(f"創建廣告失敗: {ad_data['display_name'] or f'廣告 #{i}'}")
        except Exception as e:
            error_msg = str(e)
            logger.error(f"創建廣告 #{i} 時發生意外錯誤: {error_msg}")
            
            # 特別處理 TargetClosedError
            if "TargetClosedError" in error_msg or "Target page, context or browser has been closed" in error_msg:
                reason = "瀏覽器意外關閉，請稍後再試"
            else:
                reason = f"異常: {error_msg}"
                
            failed_ads.append({
                'index': i,
                'display_name': ad_data['display_name'] or f'廣告 #{i}',
                'reason': reason
            })
    
    # 如果有驗證錯誤，直接返回表單頁面並保留輸入數據
    if has_validation_error:
        for failed in failed_ads:
            flash(f"廣告 '{failed['display_name']}' 失敗: {failed['reason']}", 'error')
        return render_template('batch.html', form_data=form_data, ads_count=ads_count)
    
    # 返回結果摘要
    flash(f"成功創建 {success_count} 個廣告 (共 {len(form_data)} 個)", 'success' if success_count == len(form_data) else 'warning')
    
    if failed_ads:
        for failed in failed_ads:
            flash(f"廣告 '{failed['display_name']}' 失敗: {failed['reason']}", 'error')
    
    return redirect(url_for('batch'))

# 檔案上傳處理
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': '沒有檔案被上傳'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '沒有選擇檔案'}), 400
    
    if file:
        # 創建基於日期的子目錄
        today = datetime.now().strftime('%Y%m%d')
        upload_dir = os.path.join(app.config['UPLOAD_FOLDER'], today)
        
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)
        
        # 保存文件
        filename = secure_filename(file.filename)
        file_path = os.path.join(upload_dir, filename)
        file.save(file_path)
        
        # 返回文件路徑
        return jsonify({
            'success': True,
            'file_path': os.path.abspath(file_path)
        })

# 提供截圖檔案的 base64 編碼
@app.route('/screenshot_base64/<path:filename>')
def screenshot_base64(filename):
    """提供截圖檔案的 base64 編碼"""
    try:
        # 安全檢查：確保檔案路徑在允許的目錄內
        if not filename.startswith('screenshots/'):
            return "Unauthorized", 403
            
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        if not os.path.exists(file_path):
            return "File not found", 404
            
        # 讀取檔案並轉換為 base64
        with open(file_path, 'rb') as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
            
        return f"data:image/png;base64,{encoded_string}"
        
    except Exception as e:
        logger.error(f"提供截圖檔案時發生錯誤: {str(e)}")
        return "Internal server error", 500

# 批量廣告頁面
@app.route('/batch')
def batch():
    return render_template('batch.html')

# 自動截圖處理
@app.route('/create-screenshot', methods=['POST'])
def create_screenshot():
    try:
        uuid = request.form.get('uuid', '').strip()
        device = request.form.get('device', 'iphone_x')
        full_page = request.form.get('full_page') == 'true'
        scroll_distance = int(request.form.get('scroll_distance', 4800))
        wait_time = int(request.form.get('wait_time', 3)) * 1000  # 轉換為毫秒
        
        if not uuid:
            flash('請輸入有效的 UUID', 'error')
            return redirect(url_for('auto_screenshot'))
        
        # 從 MongoDB 查詢 AdUnit 資料
        logger.info(f"正在查詢 UUID: {uuid}")
        adunit_data = get_adunit_by_uuid(uuid)
        
        if not adunit_data:
            flash(f'找不到 UUID {uuid} 對應的 AdUnit 資料', 'error')
            return redirect(url_for('auto_screenshot'))
        
        # 建構截圖網址
        url = build_screenshot_url(adunit_data)
        if not url:
            flash('無法建構截圖網址', 'error')
            return redirect(url_for('auto_screenshot'))
        
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
            browser = playwright.chromium.launch(headless=True)
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
            
            # 訪問目標網址
            page.goto(url, wait_until='networkidle')
            
            # 等待頁面載入完成
            page.wait_for_timeout(wait_time)
            
            # 如果設定了滾動距離，則向下滾動到廣告區域
            if scroll_distance > 0:
                logger.info(f"向下滾動 {scroll_distance} 像素到廣告區域")
                page.evaluate(f"window.scrollTo(0, {scroll_distance})")
                # 滾動後再等待一下讓內容穩定
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
            
            # 截圖
            page.screenshot(path=screenshot_path, full_page=full_page)
            
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
        flash(f'截圖失敗: {str(e)}', 'error')
    
    return redirect(url_for('auto_screenshot'))

# 投票廣告創建處理
@app.route('/create_vote_ad', methods=['POST'])
def create_vote_ad():
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
        
        flash("投票廣告創建功能尚未實現", 'warning')
        
    except Exception as e:
        logger.error(f"創建投票廣告時發生錯誤: {str(e)}")
        flash(f"創建投票廣告時發生錯誤: {str(e)}", 'error')
    
    return redirect(url_for('vote_ad'))

# GIF 廣告創建處理
@app.route('/create_gif_ad', methods=['POST'])
def create_gif_ad():
    try:
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
            'target_url': request.form.get('target_url', '')
        }
        
        # 保存表單數據到 session
        for key, value in ad_data.items():
            session[f'gif_{key}'] = value
        
        flash("GIF 廣告創建功能尚未實現", 'warning')
        
    except Exception as e:
        logger.error(f"創建 GIF 廣告時發生錯誤: {str(e)}")
        flash(f"創建 GIF 廣告時發生錯誤: {str(e)}", 'error')
    
    return redirect(url_for('gif_ad'))

# 水平 Slide 廣告創建處理
@app.route('/create_slide_ad', methods=['POST'])
def create_slide_ad():
    try:
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
            'background_image': request.form.get('background_image', '')
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
        
        flash("水平 Slide 廣告創建功能尚未實現", 'warning')
        
    except Exception as e:
        logger.error(f"創建水平 Slide 廣告時發生錯誤: {str(e)}")
        flash(f"創建水平 Slide 廣告時發生錯誤: {str(e)}", 'error')
    
    return redirect(url_for('slide_ad'))

# 垂直 Slide 廣告創建處理
@app.route('/create_vertical_slide_ad', methods=['POST'])
def create_vertical_slide_ad():
    try:
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
            'background_image': request.form.get('background_image', '')
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
        
        flash("垂直 Slide 廣告創建功能尚未實現", 'warning')
        
    except Exception as e:
        logger.error(f"創建垂直 Slide 廣告時發生錯誤: {str(e)}")
        flash(f"創建垂直 Slide 廣告時發生錯誤: {str(e)}", 'error')
    
    return redirect(url_for('vertical_slide_ad'))

# 垂直 Cube Slide 廣告創建處理
@app.route('/create_vertical_cube_slide_ad', methods=['POST'])
def create_vertical_cube_slide_ad():
    try:
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
            'background_image': request.form.get('background_image', '')
        }
        
        # 保存表單數據到 session
        for key, value in ad_data.items():
            session[f'vertical_cube_slide_{key}'] = value
            
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
        
        flash("垂直 Cube Slide 廣告創建功能尚未實現", 'warning')
        
    except Exception as e:
        logger.error(f"創建垂直 Cube Slide 廣告時發生錯誤: {str(e)}")
        flash(f"創建垂直 Cube Slide 廣告時發生錯誤: {str(e)}", 'error')
    
    return redirect(url_for('vertical_cube_slide_ad'))

# 倒數廣告創建處理
@app.route('/create_countdown_ad', methods=['POST'])
def create_countdown_ad():
    try:
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
            'image_cover': request.form.get('image_cover', ''),
            'game_winner_bg_color': request.form.get('game_winner_bg_color', '#26D07C'),
            'game_winner_text_color': request.form.get('game_winner_text_color', '#ffffff'),
            'game_bg_color': request.form.get('game_bg_color', '#ffffff'),
            'game_text_color': request.form.get('game_text_color', '#000000'),
            'game_border_color': request.form.get('game_border_color', '#000000')
        }
        
        # 保存表單數據到 session
        for key, value in ad_data.items():
            session[f'countdown_{key}'] = value
        
        flash("倒數廣告創建功能尚未實現", 'warning')
        
    except Exception as e:
        logger.error(f"創建倒數廣告時發生錯誤: {str(e)}")
        flash(f"創建倒數廣告時發生錯誤: {str(e)}", 'error')
    
    return redirect(url_for('countdown_ad'))

# 通用廣告創建路由（用於 index.html）
@app.route('/create_ad_route', methods=['POST'])
def create_ad_route():
    """根據 active_tab 參數決定創建哪種類型的廣告"""
    try:
        active_tab = request.form.get('active_tab', 'native-ad')
        
        # 根據 active_tab 重定向到對應的創建函數
        if active_tab == 'native-ad':
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
            return redirect(url_for('index'))
        elif active_tab == 'vertical-slide-ad':
            flash("垂直 Slide 廣告創建功能尚未實現", 'warning')
            return redirect(url_for('index'))
        elif active_tab == 'vertical-cube-slide-ad':
            flash("垂直 Cube Slide 廣告創建功能尚未實現", 'warning')
            return redirect(url_for('index'))
        else:
            flash(f"未知的廣告類型: {active_tab}", 'error')
            return redirect(url_for('index'))
            
    except Exception as e:
        logger.error(f"創建廣告時發生錯誤: {str(e)}")
        flash(f"創建廣告時發生錯誤: {str(e)}", 'error')
        return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, port=5002) # 使用不同的埠號