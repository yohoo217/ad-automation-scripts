from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from playwright.sync_api import sync_playwright
import logging
import os
from werkzeug.utils import secure_filename
from datetime import datetime
import time

# 從修改後的腳本導入 run 函式和 config
from native_adunit_auto_create import run as run_native # type: ignore
from suprad_adunit_auto_create import run as run_suprad # type: ignore
import config # type: ignore

app = Flask(__name__)
app.secret_key = 'your_very_secret_key' # 記得更換為一個安全的密鑰

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

# 批量廣告頁面
@app.route('/batch')
def batch():
    return render_template('batch.html')

# 創建原生廣告處理
@app.route('/create-native-ad', methods=['POST'])
def create_native_ad():
    logger.info("原生廣告表單提交開始處理")
    
    # 保存所有表單數據到 session
    for key, value in request.form.items():
        session[key] = value
    
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
    
    required_fields = ['advertiser', 'main_title', 'adset_id', 'landing_page', 
                        'image_path_m', 'image_path_o', 'image_path_p', 'image_path_s']
    missing_fields = [field for field in required_fields if not ad_data[field]]

    if missing_fields:
        logger.error(f"缺少必填欄位: {missing_fields}")
        flash(f"以下為必填欄位，不得為空： {', '.join(missing_fields)}", 'error')
        return render_template('native_ad.html', **ad_data), 400

    try:
        logger.info("開始執行原生廣告創建")
        with sync_playwright() as playwright:
            success = run_native(playwright, ad_data)
            logger.info(f"廣告創建結果: {'成功' if success else '失敗'}")
        
        if success:
            flash(f"廣告 '{ad_data.get('display_name') or ad_data.get('main_title') or '(無名稱)'}' 已成功創建！", 'success')
            logger.info(f"成功創建廣告: {ad_data.get('display_name') or ad_data.get('main_title') or '(無名稱)'}")
        else:
            flash(f"創建廣告 '{ad_data.get('display_name') or ad_data.get('main_title') or '(無名稱)'}' 失敗。請查看日誌獲取更多信息。", 'error')
            logger.error(f"創建廣告失敗: {ad_data.get('display_name') or ad_data.get('main_title') or '(無名稱)'}")
    except Exception as e:
        logger.error(f"創建廣告時發生意外錯誤: {str(e)}")
        flash(f"創建廣告時發生意外錯誤: {str(e)}", 'error')

    return redirect(url_for('native_ad'))

# 創建GIF廣告處理
@app.route('/create-gif-ad', methods=['POST'])
def create_gif_ad():
    logger.info("GIF廣告表單提交開始處理")
    
    # 保存所有表單數據到 session，加上前綴 'gif_'
    for key, value in request.form.items():
        session[f"gif_{key}"] = value
    
    ad_data = {
        'display_name': request.form.get('display_name', ''),
        'advertiser': request.form.get('advertiser', ''),
        'main_title': request.form.get('main_title', ''),
        'subtitle': request.form.get('subtitle', ''),
        'adset_id': request.form.get('adset_id', ''),
        'landing_page': request.form.get('landing_page', ''),
        'call_to_action': request.form.get('call_to_action', '立即購買'),
        'image_path_m': request.form.get('image_path_m', ''),
        'image_path_s': request.form.get('image_path_s', ''),
        'background_image': request.form.get('background_image', ''),
        'payload_game_widget': request.form.get('payload_game_widget', '')
    }
    
    required_fields = ['advertiser', 'main_title', 'adset_id', 'landing_page', 
                       'image_path_m', 'image_path_s', 'background_image', 'payload_game_widget']
    missing_fields = [field for field in required_fields if not ad_data[field]]
    
    if missing_fields:
        logger.error(f"缺少必填欄位: {missing_fields}")
        flash(f"以下為必填欄位，不得為空： {', '.join(missing_fields)}", 'error')
        return render_template('gif_ad.html', **ad_data), 400
    
    try:
        logger.info("開始執行GIF廣告創建")
        with sync_playwright() as playwright:
            success = run_suprad(playwright, ad_data)
            logger.info(f"廣告創建結果: {'成功' if success else '失敗'}")
        
        if success:
            flash(f"GIF廣告 '{ad_data.get('display_name') or ad_data.get('main_title') or '(無名稱)'}' 已成功創建！", 'success')
            logger.info(f"成功創建GIF廣告: {ad_data.get('display_name') or ad_data.get('main_title') or '(無名稱)'}")
        else:
            flash(f"創建GIF廣告 '{ad_data.get('display_name') or ad_data.get('main_title') or '(無名稱)'}' 失敗。請查看日誌獲取更多信息。", 'error')
            logger.error(f"創建GIF廣告失敗: {ad_data.get('display_name') or ad_data.get('main_title') or '(無名稱)'}")
    except Exception as e:
        logger.error(f"創建廣告時發生意外錯誤: {str(e)}")
        flash(f"創建廣告時發生意外錯誤: {str(e)}", 'error')
    
    return redirect(url_for('gif_ad'))

# 創建水平Slide廣告處理
@app.route('/create-slide-ad', methods=['POST'])
def create_slide_ad():
    logger.info("水平Slide廣告表單提交開始處理")
    
    # 保存所有表單數據到 session，加上前綴 'slide_' 
    for key, value in request.form.items():
        if key.startswith('image_url_') or key.startswith('target_url_'):
            # 這些是滑動項目的數據，保存時不加前綴
            session[key] = value
        else:
            # 其他表單字段加上前綴
            session[f"slide_{key}"] = value
    
    ad_data = {
        'display_name': request.form.get('display_name', ''),
        'advertiser': request.form.get('advertiser', ''),
        'main_title': request.form.get('main_title', ''),
        'subtitle': request.form.get('subtitle', ''),
        'adset_id': request.form.get('adset_id', ''),
        'landing_page': request.form.get('landing_page', ''),
        'call_to_action': request.form.get('call_to_action', '立即了解'),
        'image_path_m': request.form.get('image_path_m', ''),
        'image_path_s': request.form.get('image_path_s', ''),
        'background_image': request.form.get('background_image', ''),
        'payload_game_widget': request.form.get('payload_game_widget', '')
    }
    
    required_fields = ['advertiser', 'main_title', 'adset_id', 'landing_page', 
                       'image_path_m', 'image_path_s', 'background_image', 'payload_game_widget']
    missing_fields = [field for field in required_fields if not ad_data[field]]
    
    if missing_fields:
        logger.error(f"缺少必填欄位: {missing_fields}")
        flash(f"以下為必填欄位，不得為空： {', '.join(missing_fields)}", 'error')
        return render_template('slide_ad.html', **ad_data), 400
    
    try:
        logger.info("開始執行水平Slide廣告創建")
        with sync_playwright() as playwright:
            success = run_suprad(playwright, ad_data)
            logger.info(f"廣告創建結果: {'成功' if success else '失敗'}")
        
        if success:
            flash(f"水平Slide廣告 '{ad_data.get('display_name') or ad_data.get('main_title') or '(無名稱)'}' 已成功創建！", 'success')
            logger.info(f"成功創建水平Slide廣告: {ad_data.get('display_name') or ad_data.get('main_title') or '(無名稱)'}")
        else:
            flash(f"創建水平Slide廣告 '{ad_data.get('display_name') or ad_data.get('main_title') or '(無名稱)'}' 失敗。請查看日誌獲取更多信息。", 'error')
            logger.error(f"創建水平Slide廣告失敗: {ad_data.get('display_name') or ad_data.get('main_title') or '(無名稱)'}")
    except Exception as e:
        logger.error(f"創建廣告時發生意外錯誤: {str(e)}")
        flash(f"創建廣告時發生意外錯誤: {str(e)}", 'error')
    
    return redirect(url_for('slide_ad'))

# 創建垂直Slide廣告處理
@app.route('/create-vertical-slide-ad', methods=['POST'])
def create_vertical_slide_ad():
    logger.info("垂直Slide廣告表單提交開始處理")
    
    # 保存所有表單數據到 session，加上前綴 'vertical_slide_'
    for key, value in request.form.items():
        if key.startswith('image_url_') or key.startswith('target_url_'):
            # 這些是滑動項目的數據，保存時不加前綴
            session[key] = value
        else:
            # 其他表單字段加上前綴
            session[f"vertical_slide_{key}"] = value
    
    ad_data = {
        'display_name': request.form.get('display_name', ''),
        'advertiser': request.form.get('advertiser', ''),
        'main_title': request.form.get('main_title', ''),
        'subtitle': request.form.get('subtitle', ''),
        'adset_id': request.form.get('adset_id', ''),
        'landing_page': request.form.get('landing_page', ''),
        'call_to_action': request.form.get('call_to_action', '立即了解'),
        'image_path_m': request.form.get('image_path_m', ''),
        'image_path_s': request.form.get('image_path_s', ''),
        'background_image': request.form.get('background_image', ''),
        'payload_game_widget': request.form.get('payload_game_widget', '')
    }
    
    required_fields = ['advertiser', 'main_title', 'adset_id', 'landing_page', 
                       'image_path_m', 'image_path_s', 'background_image', 'payload_game_widget']
    missing_fields = [field for field in required_fields if not ad_data[field]]
    
    if missing_fields:
        logger.error(f"缺少必填欄位: {missing_fields}")
        flash(f"以下為必填欄位，不得為空： {', '.join(missing_fields)}", 'error')
        return render_template('vertical_slide_ad.html', **ad_data), 400
    
    try:
        logger.info("開始執行垂直Slide廣告創建")
        with sync_playwright() as playwright:
            success = run_suprad(playwright, ad_data)
            logger.info(f"廣告創建結果: {'成功' if success else '失敗'}")
        
        if success:
            flash(f"垂直Slide廣告 '{ad_data.get('display_name') or ad_data.get('main_title') or '(無名稱)'}' 已成功創建！", 'success')
            logger.info(f"成功創建垂直Slide廣告: {ad_data.get('display_name') or ad_data.get('main_title') or '(無名稱)'}")
        else:
            flash(f"創建垂直Slide廣告 '{ad_data.get('display_name') or ad_data.get('main_title') or '(無名稱)'}' 失敗。請查看日誌獲取更多信息。", 'error')
            logger.error(f"創建垂直Slide廣告失敗: {ad_data.get('display_name') or ad_data.get('main_title') or '(無名稱)'}")
    except Exception as e:
        logger.error(f"創建廣告時發生意外錯誤: {str(e)}")
        flash(f"創建廣告時發生意外錯誤: {str(e)}", 'error')
    
    return redirect(url_for('vertical_slide_ad'))

# 創建垂直 Cube Slide 廣告處理
@app.route('/create-vertical-cube-slide-ad', methods=['POST'])
def create_vertical_cube_slide_ad():
    logger.info("垂直 Cube Slide 廣告表單提交開始處理")
    
    # 使用 'vertical_cube_slide_' 前綴保存表單數據到 session
    prefix = 'vertical_cube_slide_'
    for key, value in request.form.items():
        session[f"{prefix}{key}" if not key.startswith(prefix) else key] = value
    
    ad_data = {
        'display_name': request.form.get('display_name', ''),
        'advertiser': request.form.get('advertiser', ''),
        'main_title': request.form.get('main_title', ''),
        'subtitle': request.form.get('subtitle', ''),
        'adset_id': request.form.get('adset_id', ''),
        'landing_page': request.form.get('landing_page', ''),
        'call_to_action': request.form.get('call_to_action', '立即了解'),
        'image_path_m': request.form.get('image_path_m', ''),
        'image_path_s': request.form.get('image_path_s', ''),
        'payload_game_widget': request.form.get('payload_game_widget', '')
    }
    
    required_fields = ['advertiser', 'main_title', 'adset_id', 'landing_page', 
                        'image_path_m', 'image_path_s', 'payload_game_widget']
    missing_fields = [field for field in required_fields if not ad_data[field]]

    if missing_fields:
        logger.error(f"缺少必填欄位: {missing_fields}")
        flash(f"以下為必填欄位，不得為空： {', '.join(missing_fields)}", 'error')
        return redirect(url_for('vertical_cube_slide_ad')), 400
    
    try:
        # 上傳素材
        upload_success, image_paths = upload_materials(request.form)
        if not upload_success:
            logger.error("上傳素材失敗")
            flash("上傳素材失敗，請檢查圖片路徑是否正確", 'error')
            return redirect(url_for('vertical_cube_slide_ad')), 400
        
        # 更新 ad_data 中的圖片路徑
        for key, value in image_paths.items():
            ad_data[key] = value
            
        logger.info("開始執行垂直 Cube Slide 廣告創建")
        with sync_playwright() as playwright:
            # 在這裡使用 run_cube_slide 或適當的函數
            success = run_suprad(playwright, ad_data, ad_type='vertical_cube_slide')
            logger.info(f"廣告創建結果: {'成功' if success else '失敗'}")
        
        if success:
            flash(f"廣告 '{ad_data.get('display_name') or ad_data.get('main_title') or '(無名稱)'}' 已成功創建！", 'success')
            logger.info(f"成功創建廣告: {ad_data.get('display_name') or ad_data.get('main_title') or '(無名稱)'}")
            return redirect(url_for('vertical_cube_slide_ad')), 200
        else:
            flash(f"創建廣告 '{ad_data.get('display_name') or ad_data.get('main_title') or '(無名稱)'}' 失敗。請查看日誌獲取更多信息。", 'error')
            logger.error(f"創建廣告失敗: {ad_data.get('display_name') or ad_data.get('main_title') or '(無名稱)'}")
            return redirect(url_for('vertical_cube_slide_ad')), 400
    
    except Exception as e:
        logger.exception(f"創建垂直 Cube Slide 廣告時發生錯誤: {str(e)}")
        flash(f"發生錯誤: {str(e)}", 'error')
        return redirect(url_for('vertical_cube_slide_ad')), 500

# 創建投票廣告處理
@app.route('/create-vote-ad', methods=['POST'])
def create_vote_ad():
    logger.info("投票廣告表單提交開始處理")
    
    # 使用 'vote_' 前綴保存表單數據到 session
    prefix = 'vote_'
    for key, value in request.form.items():
        session[f"{prefix}{key}" if not key.startswith(prefix) else key] = value
    
    ad_data = {
        'display_name': request.form.get('display_name', ''),
        'advertiser': request.form.get('advertiser', ''),
        'main_title': request.form.get('main_title', ''),
        'subtitle': request.form.get('subtitle', ''),
        'adset_id': request.form.get('adset_id', ''),
        'landing_page': request.form.get('landing_page', ''),
        'call_to_action': request.form.get('call_to_action', '立即了解'),
        'image_path_m': request.form.get('image_path_m', ''),
        'image_path_s': request.form.get('image_path_s', ''),
        'background_image': request.form.get('background_image', ''),
        'vote_image': request.form.get('vote_image', ''),
        'payload_game_widget': request.form.get('payload_game_widget', '')
    }
    
    required_fields = ['advertiser', 'main_title', 'adset_id', 'landing_page', 
                        'image_path_m', 'image_path_s', 'background_image', 'vote_image', 'payload_game_widget']
    missing_fields = [field for field in required_fields if not ad_data[field]]

    if missing_fields:
        logger.error(f"缺少必填欄位: {missing_fields}")
        flash(f"以下為必填欄位，不得為空： {', '.join(missing_fields)}", 'error')
        return redirect(url_for('vote_ad')), 400
    
    try:
        logger.info("開始執行投票廣告創建")
        with sync_playwright() as playwright:
            # 使用 suprad (special ad) 創建函數
            success = run_suprad(playwright, ad_data)
            logger.info(f"廣告創建結果: {'成功' if success else '失敗'}")
        
        if success:
            flash(f"廣告 '{ad_data.get('display_name') or ad_data.get('main_title') or '(無名稱)'}' 已成功創建！", 'success')
            logger.info(f"成功創建廣告: {ad_data.get('display_name') or ad_data.get('main_title') or '(無名稱)'}")
            return redirect(url_for('vote_ad'))
        else:
            flash(f"創建廣告 '{ad_data.get('display_name') or ad_data.get('main_title') or '(無名稱)'}' 失敗。請查看日誌獲取更多信息。", 'error')
            logger.error(f"創建廣告失敗: {ad_data.get('display_name') or ad_data.get('main_title') or '(無名稱)'}")
            return redirect(url_for('vote_ad'))
    
    except Exception as e:
        logger.exception(f"創建投票廣告時發生錯誤: {str(e)}")
        flash(f"發生錯誤: {str(e)}", 'error')
        return redirect(url_for('vote_ad'))

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

if __name__ == '__main__':
    app.run(debug=True, port=5002) # 使用不同的埠號 