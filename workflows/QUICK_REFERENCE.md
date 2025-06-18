# ⚡ Agent 快速參考指南

## 🎯 一句話總結
使用標準化 workflow 在 20 分鐘內開發新廣告類型，效率提升 95%，品質保證 100%。

---

## 📋 快速檢查清單

### 用戶需求評估 (5分鐘)
```markdown
✅ 廣告類型名稱 (snake_case)
✅ 中文顯示名稱
✅ 至少1個特殊欄位
✅ 互動邏輯描述
✅ 完整 Payload JSON 結構範例
```

### 立即開發流程 (15分鐘)
```python
# 1. 使用生成器
from workflows.templates.standard_ad_template import AdTemplateGenerator
generator = AdTemplateGenerator()

# 2. 定義廣告
ad_definition = {
    'ad_type': 'example_ad',
    'chinese_name': '範例廣告',
    'special_fields': [...],
    'payload_type': 'payload_game_widget'
}

# 3. 生成代碼
result = generator.generate_complete_ad_type(ad_definition)
```

### 最終驗證 (3分鐘)
```markdown
✅ 頁面載入正常
✅ 表單提交功能
✅ 導航連結存在
✅ 命名符合約定
```

---

## 🏗️ 架構速查

### 檔案位置
```
templates/{ad_type}_ad.html     ← 模板文件
app/routes/main.py             ← 路由代碼
templates/base.html            ← 導航更新
```

### 路由格式
```python
@main_bp.route('/{ad_type}-ad')                    # 顯示頁面
@main_bp.route('/create-{ad_type}-ad', methods=['POST'])  # 創建處理
@main_bp.route('/clear-{ad_type}-form', methods=['POST']) # 清除表單
```

### CSS 類別
```css
.main-content-wrapper  .form-column      .preview-column
.field-group          .form-grid-2       .form-row
.help-text           .clear-form-btn
```

---

## 🎨 欄位類型速查

### 基本欄位模板
```yaml
text:   # 文字輸入
  type: "text"
  required: true|false
  default_value: "預設文字"

url:    # 網址輸入
  type: "url"
  placeholder: "https://example.com"

number: # 數字輸入
  type: "number"
  default_value: 0

color:  # 顏色選擇器
  type: "color"
  default_value: "#FF0000"

select: # 下拉選單
  type: "select"
  options: [
    {value: "option1", text: "選項1", default: true},
    {value: "option2", text: "選項2"}
  ]
```

---

## 🚀 常見廣告類型

### 互動型廣告
```yaml
interaction_type: "interactive_widget"
base_template: "vote_ad.html"
payload_type: "payload_game_widget"
範例: 寶箱廣告、輪盤廣告、按鈕互動
```

### 動畫型廣告
```yaml
interaction_type: "slide_animation"
base_template: "slide_ad.html"
payload_type: "payload_game_widget"
範例: 滑動展示、動畫效果、轉場
```

### 影音型廣告
```yaml
interaction_type: "popup_video"
base_template: "popup_video_ad.html"
payload_type: "payload_popup_json"
範例: 彈跳影音、影片互動
```

### 時間型廣告
```yaml
interaction_type: "countdown_timer"
base_template: "countdown_ad.html"
payload_type: "payload_game_widget"
範例: 倒數計時、限時優惠
```

### 簡單型廣告
```yaml
interaction_type: "simple_display"
base_template: "native_ad.html"
payload_type: "payload_game_widget"
範例: 靜態展示、基本資訊
```

---

## ⚡ Payload 結構速查

### payload_game_widget (最常用)
```javascript
{
  type: "CUSTOM",
  data: {
    field1: "value1",
    field2: "value2"
  }
}
```

### payload_vote_widget (投票類)
```javascript
{
  type: "VOTE",
  data: {
    options: [...],
    settings: {...}
  }
}
```

### payload_popup_json (彈窗類)
```javascript
{
  type: "POPUP",
  data: {
    video: "url",
    style: {...}
  }
}
```

---

## 🎯 回應模板

### 標準成功回應
```markdown
### 🎉 {chinese_name} 開發完成

**生成檔案：**
✅ templates/{ad_type}_ad.html
✅ app/routes/main.py (3個路由)
✅ templates/base.html (導航更新)

**功能特色：**
{列出主要功能}

**存取路徑：** `/{ad_type}-ad`
**開發時間：** {actual_time} 分鐘
**效率提升：** {percentage}%

立即可用！🚀
```

### 需求不足回應
```markdown
### ❓ 需要更多資訊

請提供：
1. 廣告類型名稱 (英文)
2. 中文顯示名稱
3. 特殊功能需求 (至少1個)
4. 互動方式描述

範例："我想要一個 [刮刮樂] 廣告，用戶 [滑動刮開] 獎區"
```

### 複雜需求回應
```markdown
### 🤖 需求分析

您的需求涉及 {complex_feature}，超出標準功能範圍。

**建議替代方案：**
- 方案A：{simple_alternative}
- 方案B：{medium_alternative}

建議選擇方案A，可立即使用標準 workflow 開發。
```

---

## 🚫 常見錯誤

### 命名錯誤
```markdown
❌ "TreasureBox"     → ✅ "treasure_box"
❌ "treasure-box"    → ✅ "treasure_box"
❌ "treasurebox"     → ✅ "treasure_box"
```

### 欄位定義錯誤
```markdown
❌ 缺少 required 屬性
❌ type 使用錯誤值
❌ 沒有 label 或 help_text
✅ 完整的欄位定義
```

### 架構違規
```markdown
❌ 創建新的 CSS 類別
❌ 修改 base.html 核心結構
❌ 跳過檢查清單項目
✅ 嚴格遵循標準約定
```

---

## 📊 效率指標

### 時間目標
- 需求收集: ≤ 5 分鐘
- 代碼生成: ≤ 15 分鐘
- 測試驗證: ≤ 5 分鐘
- **總計: ≤ 25 分鐘**

### 品質目標
- 功能完整性: 100%
- 架構一致性: 100%
- 命名規範性: 100%
- 測試通過率: 100%

---

## 🔧 除錯速查

### 頁面載入失敗
```python
# 檢查路由是否正確添加
# 檢查模板文件是否存在
# 檢查繼承 base.html 語法
```

### 表單提交失敗
```python
# 檢查 POST 路由
# 檢查表單 action URL
# 檢查 CSRF token
```

### JavaScript 錯誤
```javascript
// 檢查 updatePayload() 函數
// 檢查事件監聽器
// 檢查 debounce 函數
```

### Session 問題
```python
# 檢查 session key 命名
# 檢查 session.pop() 邏輯
# 檢查 form_data 傳遞
```

---

## 💡 專家技巧

### 快速判斷廣告類型
- 有**點擊互動** → interactive_widget
- 有**滑動動畫** → slide_animation  
- 有**影片播放** → popup_video
- 有**時間相關** → countdown_timer
- **純展示類** → simple_display

### 欄位數量建議
- **2-4個欄位**: 最佳用戶體驗
- **5-6個欄位**: 可接受範圍
- **超過6個**: 考慮分組或簡化

### Payload 選擇原則
- **95%情況**: 使用 payload_game_widget
- **投票相關**: 使用 payload_vote_widget
- **彈窗影片**: 使用 payload_popup_json

記住：**簡單、快速、一致** 是成功的關鍵！🎯