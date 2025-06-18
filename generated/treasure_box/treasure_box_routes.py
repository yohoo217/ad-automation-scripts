
# TREASURE_BOX 廣告路由
# 自動生成於 2025-06-18 21:00:33
# 遵循 FINAL_RECOMMENDED_WORKFLOW.md 標準

from flask import render_template, request, flash, session, redirect, url_for, jsonify
from playwright.sync_api import sync_playwright
import json
import logging

logger = logging.getLogger(__name__)

@main_bp.route('/treasure_box-ad')
def treasure_box_ad():
    """
    Treasure Box 廣告頁面
    標準化路由實現 - 顯示頁面
    """
    try:
        # 載入表單資料（如果存在）
        form_data = session.get('treasure_box_form_data', {})
        
        return render_template(
            'treasure_box_ad.html',
            form_data=form_data,
            ad_type='treasure_box',
            page_title='Treasure Box 廣告'
        )
        
    except Exception as e:
        logger.error(f"載入treasure_box廣告頁面時發生錯誤: {str(e)}")
        flash(f"載入頁面時發生錯誤: {str(e)}", 'error')
        return redirect(url_for('main.index'))

@main_bp.route('/create-treasure_box-ad', methods=['POST'])
def create_treasure_box_ad():
    """
    Treasure Box 廣告創建處理
    標準化路由實現 - 創建處理
    """
    try:
        # 獲取表單資料
        form_data = request.get_json() if request.is_json else request.form
        
        # 基礎欄位驗證
        required_fields = ['adset_id', 'advertiser', 'main_title', 'landing_page']
        missing_fields = [field for field in required_fields if not form_data.get(field)]
        
        if missing_fields:
            return jsonify({
                'success': False,
                'error': f'缺少必要欄位: {", ".join(missing_fields)}'
            }), 400
            
        # 建構 ad_data
        ad_data = {
            # 基礎必填欄位
            'adset_id': form_data.get('adset_id'),
            'advertiser': form_data.get('advertiser'),
            'main_title': form_data.get('main_title'),
            'landing_page': form_data.get('landing_page'),
            'image_path_m': form_data.get('image_path_m', ''),
            'image_path_s': form_data.get('image_path_s', ''),
            
            # treasure_box 特定欄位
            'img_logo': form_data.get('img_logo', ''),
            'img_background': form_data.get('img_background', ''),
            'img_item_idle': form_data.get('img_item_idle', ''),
            'img_item_opening': form_data.get('img_item_opening', ''),
            'img_item_opened': form_data.get('img_item_opened', ''),
            'img_item_a_active': form_data.get('img_item_a_active', ''),
            'img_item_a_idle': form_data.get('img_item_a_idle', ''),
            'img_item_b_active': form_data.get('img_item_b_active', ''),
            'img_item_b_idle': form_data.get('img_item_b_idle', ''),
            'img_item_c_active': form_data.get('img_item_c_active', ''),
            'img_item_c_idle': form_data.get('img_item_c_idle', ''),
            'url_popup_a': form_data.get('url_popup_a', ''),
            'url_popup_b': form_data.get('url_popup_b', ''),
            'url_popup_c': form_data.get('url_popup_c', ''),
            
            # Payload 處理
            'payload_game_widget': self._build_treasure_box_payload(form_data)
        }
        
        # 儲存表單資料到 session
        session['treasure_box_form_data'] = form_data
        
        # 執行 Suprad 腳本
        with sync_playwright() as playwright:
            result = run_suprad(playwright, ad_data, "treasure_box")
            
        if result:
            flash(f'Treasure Box廣告創建成功！', 'success')
            return jsonify({'success': True, 'message': '廣告創建成功'})
        else:
            flash(f'Treasure Box廣告創建失敗', 'error')
            return jsonify({'success': False, 'error': '廣告創建失敗'}), 500
            
    except Exception as e:
        logger.error(f"創建treasure_box廣告時發生錯誤: {str(e)}")
        flash(f"創建treasure_box廣告時發生錯誤: {str(e)}", 'error')
        return jsonify({'success': False, 'error': str(e)}), 500

@main_bp.route('/clear-treasure_box-form', methods=['POST'])
def clear_treasure_box_form():
    """
    Treasure Box 廣告表單清除
    標準化路由實現 - 清除表單
    """
    try:
        session.pop('treasure_box_form_data', None)
        flash('表單已清除', 'info')
        return jsonify({'success': True, 'message': '表單已清除'})
        
    except Exception as e:
        logger.error(f"清除treasure_box表單時發生錯誤: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

def _build_treasure_box_payload(form_data):
    """建構 treasure_box 專用的 payload"""
    payload = {
        'ad_type': 'treasure_box',
        'timestamp': datetime.now().isoformat(),
        'img_logo': form_data.get('img_logo', ''),
        'img_background': form_data.get('img_background', ''),
        'img_item_idle': form_data.get('img_item_idle', ''),
        'img_item_opening': form_data.get('img_item_opening', ''),
        'img_item_opened': form_data.get('img_item_opened', ''),
        'img_item_a_active': form_data.get('img_item_a_active', ''),
        'img_item_a_idle': form_data.get('img_item_a_idle', ''),
        'img_item_b_active': form_data.get('img_item_b_active', ''),
        'img_item_b_idle': form_data.get('img_item_b_idle', ''),
        'img_item_c_active': form_data.get('img_item_c_active', ''),
        'img_item_c_idle': form_data.get('img_item_c_idle', ''),
        'url_popup_a': form_data.get('url_popup_a', ''),
        'url_popup_b': form_data.get('url_popup_b', ''),
        'url_popup_c': form_data.get('url_popup_c', ''),
    }
    
    return json.dumps(payload, ensure_ascii=False)
