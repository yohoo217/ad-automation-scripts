# 🤖 Agent 模式開發指南

## 📋 概覽
這份指南確保任何 AI agent 都能按照標準化 workflow 開發新廣告類型，產出高度一致且可預期的結果。

---

## 🎯 Agent 開發標準流程

### 階段 1：需求收集與驗證 (Agent 必須完成)

**第1步：初步需求推測**
Agent 根據用戶描述推測基本資訊，並向用戶確認。

**第2步：關鍵資訊收集**
```yaml
必須收集的資訊:
  廣告類型名稱: "string (英文, snake_case)"
  中文顯示名稱: "string (繁體中文)"
  特殊欄位定義: 
    - 欄位名稱: "string"
    - 資料類型: "text|url|number|color|select"
    - 是否必填: "boolean"
    - 預設值: "string"
    - 說明文字: "string"
  Payload JSON 結構: "完整的 JSON 範例"
  互動邏輯描述: "string"
```

**第3步：Payload 結構確認**
Agent 必須要求用戶提供具體的 payload JSON 結構範例：
```markdown
請提供前端應該生成的 payload_game_widget JSON 結構，例如：
{
  type: "YOUR_TYPE",
  data: {
    field1: "value1",
    field2: "value2"
  }
}
```

**Agent 驗證檢查點:**
- [ ] 廣告類型名稱符合 snake_case 格式
- [ ] 所有特殊欄位都有完整定義
- [ ] Payload 類型選擇合理
- [ ] 互動邏輯描述清晰

### 階段 2：模板生成 (Agent 自動執行)
**Agent 必須按照以下順序執行:**

1. **選擇基礎模板**
```python
template_selection_logic = {
    "simple_display": "native_ad.html",
    "interactive_widget": "vote_ad.html", 
    "slide_animation": "slide_ad.html",
    "popup_video": "popup_video_ad.html",
    "countdown_timer": "countdown_ad.html"
}
```

2. **執行模板複製與替換**
```bash
# Agent 必須執行的命令序列
cp templates/{base_template} templates/{ad_type}_ad.html
```

3. **標準化替換規則**
```python
replacements = {
    # 基礎替換
    "{base_type}": "{new_ad_type}",
    "{base_chinese}": "{new_chinese_name}",
    
    # 路由替換
    "url_for('main.{base_type}_ad')": "url_for('main.{new_ad_type}_ad')",
    "create_{base_type}_ad": "create_{new_ad_type}_ad",
    
    # 表單 ID 替換
    "id=\"{base_type}_": "id=\"{new_ad_type}_",
    "name=\"{base_type}_": "name=\"{new_ad_type}_"
}
```

### 階段 3：路由代碼生成 (Agent 自動執行)
**Agent 必須在 `app/routes/main.py` 中新增:**

```python
# {ad_type} 廣告路由 - Agent 自動生成
@main_bp.route('/{ad_type}-ad')
def {ad_type}_ad():
    """顯示 {chinese_name} 創建頁面"""
    form_data = session.get('{ad_type}_form_data', {{}})
    return render_template('{ad_type}_ad.html', **form_data)

@main_bp.route('/create-{ad_type}-ad', methods=['POST'])
def create_{ad_type}_ad():
    """處理 {chinese_name} 創建請求"""
    try:
        # 收集標準欄位
        ad_data = {{
            'adset_id': request.form.get('adset_id'),
            'advertiser': request.form.get('advertiser'),
            'main_title': request.form.get('main_title'),
            'landing_page': request.form.get('landing_page'),
            'image_path_m': request.form.get('image_path_m'),
            'image_path_s': request.form.get('image_path_s'),
            'display_name': request.form.get('display_name', ''),
            'subtitle': request.form.get('subtitle', ''),
            'call_to_action': request.form.get('call_to_action', '立即了解')
        }}
        
        # 收集特殊欄位
        {special_fields_code}
        
        # 保存到 session
        session['{ad_type}_form_data'] = ad_data
        
        # 執行廣告創建
        with sync_playwright() as playwright:
            result = run_suprad(playwright, ad_data, "{ad_type}")
        
        if result:
            flash('{chinese_name}創建成功！', 'success')
            session.pop('{ad_type}_form_data', None)
        else:
            flash('{chinese_name}創建失敗', 'error')
            
    except Exception as e:
        logger.error(f"創建{chinese_name}時發生錯誤: {{str(e)}}")
        flash(f"創建{chinese_name}時發生錯誤: {{str(e)}}", 'error')
    
    return redirect(url_for('main.{ad_type}_ad'))

@main_bp.route('/clear-{ad_type}-form', methods=['POST'])
def clear_{ad_type}_form():
    """清除 {chinese_name} 表單數據"""
    session.pop('{ad_type}_form_data', None)
    flash('表單內容已清除', 'info')
    return redirect(url_for('main.{ad_type}_ad'))
```

### 階段 4：表單欄位生成 (Agent 自動執行)
**Agent 必須根據欄位定義生成標準化表單:**

```html
<!-- Agent 生成的特殊欄位區域 -->
<div class="field-group">
    <h3>⚙️ {chinese_name}設定</h3>
    
    {form_fields_html}
</div>
```

**欄位生成規則:**
```python
field_templates = {
    "text": '''
    <div class="form-row">
        <label for="{field_name}">{label} {required_mark}</label>
        <input type="text" id="{field_name}" name="{field_name}" 
               value="{{{{ {field_name} or '{default_value}' }}}}" {required_attr}
               placeholder="{placeholder}">
        <div class="help-text">{help_text}</div>
    </div>''',
    
    "url": '''
    <div class="form-row">
        <label for="{field_name}">{label} {required_mark}</label>
        <input type="url" id="{field_name}" name="{field_name}" 
               value="{{{{ {field_name} or '{default_value}' }}}}" {required_attr}
               placeholder="{placeholder}">
        <div class="help-text">{help_text}</div>
    </div>''',
    
    "number": '''
    <div class="form-row">
        <label for="{field_name}">{label} {required_mark}</label>
        <input type="number" id="{field_name}" name="{field_name}" 
               value="{{{{ {field_name} or {default_value} }}}}" {required_attr}
               placeholder="{placeholder}">
        <div class="help-text">{help_text}</div>
    </div>''',
    
    "color": '''
    <div class="form-row">
        <label for="{field_name}">{label}</label>
        <div class="color-input-group">
            <input type="color" id="{field_name}" name="{field_name}" 
                   value="{{{{ {field_name} or '{default_value}' }}}}">
            <input type="text" value="{{{{ {field_name} or '{default_value}' }}}}" readonly>
        </div>
        <div class="help-text">{help_text}</div>
    </div>'''
}
```

### 階段 5：JavaScript 生成 (Agent 自動執行)
**Agent 必須生成標準化 JavaScript:**

```javascript
// Agent 自動生成的 JavaScript 區塊
{% block additional_scripts %}
<script>
    // Debounce 函數
    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    // 自動儲存表單
    const autoSaveForm = debounce(() => {
        const form = document.getElementById('ad-form');
        const formData = new FormData(form);
        
        fetch('/api/save-{ad_type}-form', {
            method: 'POST',
            body: formData
        }).catch(console.error);
    }, 500);

    // 即時預覽更新
    function updatePreview() {
        {preview_update_logic}
    }

    // Payload 生成邏輯
    function updatePayload() {
        const payload = {
            {payload_structure}
        };
        
        document.getElementById('payload_game_widget').value = JSON.stringify(payload);
    }

    // 事件監聽器
    document.addEventListener('DOMContentLoaded', function() {
        // 表單欄位變更監聽
        {event_listeners}
        
        // 初始化
        updatePreview();
        updatePayload();
    });

    // 表單提交前驗證
    document.getElementById('ad-form').addEventListener('submit', function(e) {
        {validation_logic}
    });
</script>
{% endblock %}
```

---

## 🎯 Agent 檢查清單

### 生成完成後必須驗證的項目:
```markdown
### 檔案生成檢查 ✅
- [ ] templates/{ad_type}_ad.html 已生成
- [ ] 路由代碼已添加到 app/routes/main.py
- [ ] 導航連結已更新到 base.html

### 結構完整性檢查 ✅
- [ ] 模板繼承 base.html 正確
- [ ] 使用標準 CSS 類別 (main-content-wrapper, form-column, preview-column)
- [ ] 表單結構符合三區域劃分
- [ ] JavaScript 包含所有必要函數

### 功能性檢查 ✅
- [ ] 所有特殊欄位已正確生成
- [ ] Payload 生成邏輯符合需求
- [ ] 路由命名符合約定
- [ ] 錯誤處理邏輯完整

### 測試驗證 ✅
- [ ] 頁面載入無錯誤
- [ ] 表單提交功能正常
- [ ] 預覽功能運作
- [ ] 清除表單功能正常
```

---

## 📝 標準化命名約定

### 檔案命名
```
templates/{ad_type}_ad.html
routes: /{ad_type}-ad, /create-{ad_type}-ad, /clear-{ad_type}-form
functions: {ad_type}_ad(), create_{ad_type}_ad(), clear_{ad_type}_form()
session_key: {ad_type}_form_data
```

### CSS 類別 (Agent 必須使用)
```css
.main-content-wrapper    /* 主容器 */
.form-column            /* 表單欄 */
.preview-column         /* 預覽欄 */
.field-group            /* 區域分組 */
.form-grid-2            /* 雙欄格線 */
.form-grid-3            /* 三欄格線 */
.form-row               /* 表單行 */
.help-text              /* 幫助文字 */
.clear-form-btn         /* 清除按鈕 */
```

### JavaScript 函數 (Agent 必須實作)
```javascript
debounce()              /* 防抖函數 */
autoSaveForm()          /* 自動儲存 */
updatePreview()         /* 預覽更新 */
updatePayload()         /* Payload 生成 */
```

---

## 🔧 Agent 輔助工具

### 1. 欄位定義驗證器
```python
def validate_field_definition(field_def):
    required_keys = ['name', 'type', 'label', 'required']
    optional_keys = ['default_value', 'placeholder', 'help_text', 'options']
    
    for key in required_keys:
        if key not in field_def:
            raise ValueError(f"Missing required key: {key}")
    
    if field_def['type'] not in ['text', 'url', 'number', 'color', 'select']:
        raise ValueError(f"Invalid field type: {field_def['type']}")
    
    return True
```

### 2. 模板生成器
```python
def generate_ad_template(ad_type, chinese_name, special_fields, base_template):
    """Agent 使用的模板生成器"""
    # 讀取基礎模板
    # 執行標準化替換
    # 生成特殊欄位 HTML
    # 生成 JavaScript 邏輯
    # 返回完整模板
    pass
```

### 3. 路由生成器
```python
def generate_route_code(ad_type, chinese_name, special_fields):
    """Agent 使用的路由代碼生成器"""
    # 生成三個標準路由
    # 處理特殊欄位邏輯
    # 返回完整路由代碼
    pass
```

---

## 🎉 Agent 成功標準

### 開發時間標準
- **需求收集**: ≤ 5 分鐘
- **代碼生成**: ≤ 10 分鐘  
- **測試驗證**: ≤ 5 分鐘
- **總計**: ≤ 20 分鐘

### 品質標準
- **功能完整性**: 100% 標準功能實作
- **架構一致性**: 100% 符合現有模式
- **代碼品質**: 無語法錯誤，符合命名約定
- **測試通過率**: 100% 基礎功能測試通過

### 可預期性標準
- **結構標準化**: 任何 agent 生成的代碼結構完全一致
- **命名標準化**: 檔案、函數、變數命名完全符合約定
- **風格標準化**: HTML、CSS、JavaScript 風格完全一致

---

## 📋 Agent 使用範例

```markdown
### 範例請求格式:
"請使用標準化 workflow 創建一個新的廣告類型"

廣告類型名稱: treasure_box
中文顯示名稱: 寶箱廣告
特殊欄位:
  - treasure_image: url, 必填, "寶箱圖片URL"
  - reward_text: text, 可選, "獎勵文字"
  - unlock_duration: number, 可選, "解鎖動畫時長(秒)", 預設值: 2
Payload 類型: payload_game_widget
互動邏輯: 點擊寶箱觸發開啟動畫，顯示獎勵內容

### Agent 預期回應:
✅ 已完成 treasure_box 廣告類型開發
✅ 檔案生成: templates/treasure_box_ad.html
✅ 路由新增: 3個標準路由
✅ 導航更新: 已添加寶箱廣告連結
✅ 開發時間: 18分鐘
✅ 測試狀態: 所有基礎功能測試通過
```

這份指南確保任何 AI agent 都能產出**高度一致、可預期且符合標準**的廣告開發結果！ 