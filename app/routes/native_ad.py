from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from playwright.sync_api import sync_playwright
import logging
import time

# 從修改後的腳本導入 run 函式
from native_adunit_auto_create import run as run_native # type: ignore

logger = logging.getLogger(__name__)

native_ad_bp = Blueprint('native_ad', __name__)

@native_ad_bp.route('/native_ad')
def native_ad():
    """原生廣告創建頁面"""
    form_data = session.get('form_data', {})
    return render_template('native_ad.html', **form_data)

@native_ad_bp.route('/clear-native-form', methods=['POST'])
def clear_native_form():
    """清除原生廣告表單數據"""
    session.pop('form_data', None)
    flash("表單內容已清除", 'info')
    return redirect(url_for('native_ad.native_ad'))

@native_ad_bp.route('/create_native_ad', methods=['POST'])
def create_native_ad():
    """原生廣告創建處理"""
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
        session['form_data'] = ad_data
        
        # 驗證必填欄位
        required_fields = ['advertiser', 'main_title', 'adset_id', 'landing_page', 
                          'image_path_m', 'image_path_o', 'image_path_p', 'image_path_s']
        missing_fields = [field for field in required_fields if not ad_data[field]]
        
        if missing_fields:
            flash(f"缺少必填欄位: {', '.join(missing_fields)}", 'error')
            return redirect(url_for('native_ad.native_ad'))
        
        # 嘗試創建廣告
        logger.info(f"開始創建原生廣告: {ad_data['display_name'] or ad_data['main_title']}")
        
        with sync_playwright() as playwright:
            success = run_native(playwright, ad_data)
        
        if success:
            flash(f"成功創建原生廣告: {ad_data['display_name'] or ad_data['main_title']}", 'success')
            session.pop('form_data', None)  # 成功後清除
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
            flash(f"創建原生廣告時發生錯誤: {error_msg}", 'error')
    
    return redirect(url_for('native_ad.native_ad'))

@native_ad_bp.route('/create_batch_ads', methods=['POST'])
def create_batch_ads():
    """批量廣告創建處理"""
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
    
    return redirect(url_for('main.batch'))

@native_ad_bp.route('/upload_and_get_path_native', methods=['POST'])
def upload_and_get_path_native():
    # This method is not provided in the original file or the code block
    # It's assumed to exist as it's called in the original file
    pass 