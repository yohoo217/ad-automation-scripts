
# treasure_box 廣告路由 - Agent 自動生成
@main_bp.route('/treasure_box-ad')
def treasure_box_ad():
    """顯示 寶箱廣告 創建頁面"""
    form_data = session.get('treasure_box_form_data', {})
    return render_template('treasure_box_ad.html', **form_data)

@main_bp.route('/create-treasure_box-ad', methods=['POST'])
def create_treasure_box_ad():
    """處理 寶箱廣告 創建請求"""
    try:
        # 收集標準欄位
        ad_data = {
            'adset_id': request.form.get('adset_id'),
            'advertiser': request.form.get('advertiser'),
            'main_title': request.form.get('main_title'),
            'landing_page': request.form.get('landing_page'),
            'image_path_m': request.form.get('image_path_m'),
            'image_path_s': request.form.get('image_path_s'),
            'display_name': request.form.get('display_name', ''),
            'subtitle': request.form.get('subtitle', ''),
            'call_to_action': request.form.get('call_to_action', '立即了解')
        }
        
        # 收集特殊欄位
        ad_data['treasure_image'] = request.form.get('treasure_image', '')
        ad_data['reward_text'] = request.form.get('reward_text', '恭喜獲得獎勵！')
        ad_data['unlock_duration'] = request.form.get('unlock_duration', 2)
        ad_data['treasure_color'] = request.form.get('treasure_color', '#FFD700')
        
        # 保存到 session
        session['treasure_box_form_data'] = ad_data
        
        # 執行廣告創建
        with sync_playwright() as playwright:
            result = run_suprad(playwright, ad_data, "treasure_box")
        
        if result:
            flash('寶箱廣告創建成功！', 'success')
            session.pop('treasure_box_form_data', None)
        else:
            flash('寶箱廣告創建失敗', 'error')
            
    except Exception as e:
        logger.error(f"創建寶箱廣告時發生錯誤: {str(e)}")
        flash(f"創建寶箱廣告時發生錯誤: {str(e)}", 'error')
    
    return redirect(url_for('main.treasure_box_ad'))

@main_bp.route('/clear-treasure_box-form', methods=['POST'])
def clear_treasure_box_form():
    """清除 寶箱廣告 表單數據"""
    session.pop('treasure_box_form_data', None)
    flash('表單內容已清除', 'info')
    return redirect(url_for('main.treasure_box_ad'))
