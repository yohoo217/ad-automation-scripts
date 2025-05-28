from flask import Blueprint, render_template, redirect, url_for, session, request, flash
import logging
import os
from playwright.sync_api import sync_playwright

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
        'target_url': session.get('countdown_target_url', '')
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
            'target_url': request.form.get('target_url', '')
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