from flask import Blueprint, render_template, redirect, url_for, session, request, flash
import logging

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
    return render_template('gif_ad.html')

def create_gif_ad():
    """處理 GIF 廣告創建"""
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
    
    return redirect(url_for('main.gif_ad'))

@main_bp.route('/slide-ad')
def slide_ad():
    """水平 Slide 廣告頁面"""
    return render_template('slide_ad.html')

@main_bp.route('/vertical-slide-ad')
def vertical_slide_ad():
    """垂直 Slide 廣告頁面"""
    return render_template('vertical_slide_ad.html')

@main_bp.route('/vertical-cube-slide-ad')
def vertical_cube_slide_ad():
    """垂直 Cube Slide 廣告頁面"""
    return render_template('vertical_cube_slide_ad.html')

@main_bp.route('/countdown_ad')
def countdown_ad():
    """倒數廣告頁面"""
    return render_template('countdown_ad.html')

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
        
        flash("投票廣告創建功能尚未實現", 'warning')
        
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
    
    return redirect(url_for('main.vertical_slide_ad'))

@main_bp.route('/create-vertical-cube-slide-ad', methods=['POST'])
def create_vertical_cube_slide_ad():
    """處理垂直 Cube Slide 廣告創建"""
    try:
        # 處理表單數據（暫時只保存到 session）
        ad_data = {
            'adset_id': request.form.get('adset_id', ''),
            'advertiser': request.form.get('advertiser', ''),
            'main_title': request.form.get('main_title', ''),
            'subtitle': request.form.get('subtitle', ''),
            'landing_page': request.form.get('landing_page', ''),
            'call_to_action': request.form.get('call_to_action', '立即了解'),
            'image_path_m': request.form.get('image_path_m', ''),
            'image_path_s': request.form.get('image_path_s', ''),
        }
        
        # 保存表單數據到 session
        for key, value in ad_data.items():
            session[f'vertical_cube_slide_{key}'] = value
        
        flash("垂直 Cube Slide 廣告創建功能尚未實現", 'warning')
        
    except Exception as e:
        logger.error(f"創建垂直 Cube Slide 廣告時發生錯誤: {str(e)}")
        flash(f"創建垂直 Cube Slide 廣告時發生錯誤: {str(e)}", 'error')
    
    return redirect(url_for('main.vertical_cube_slide_ad'))

@main_bp.route('/create-countdown-ad', methods=['POST'])
def create_countdown_ad():
    """處理倒數廣告創建"""
    try:
        # 處理表單數據（暫時只保存到 session）
        ad_data = {
            'adset_id': request.form.get('adset_id', ''),
            'advertiser': request.form.get('advertiser', ''),
            'main_title': request.form.get('main_title', ''),
            'subtitle': request.form.get('subtitle', ''),
            'landing_page': request.form.get('landing_page', ''),
            'call_to_action': request.form.get('call_to_action', '立即了解'),
            'image_path_m': request.form.get('image_path_m', ''),
            'image_path_s': request.form.get('image_path_s', ''),
        }
        
        # 保存表單數據到 session
        for key, value in ad_data.items():
            session[f'countdown_{key}'] = value
        
        flash("倒數廣告創建功能尚未實現", 'warning')
        
    except Exception as e:
        logger.error(f"創建倒數廣告時發生錯誤: {str(e)}")
        flash(f"創建倒數廣告時發生錯誤: {str(e)}", 'error')
    
    return redirect(url_for('main.countdown_ad')) 