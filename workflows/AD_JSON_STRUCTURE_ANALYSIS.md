# 廣告 JSON 數據結構分析

## 🎯 核心發現

從現有代碼分析，**您說得完全對！** 新增廣告類型的關鍵在於正確構造 `ad_data` JSON，而不是那些 UI/UX 細節。

## 📊 標準 JSON 結構

### 基礎必填欄位 (所有廣告類型通用)
```json
{
    "adset_id": "string",           // 必填 - Adset ID
    "display_name": "string",       // 可選 - 廣告單元顯示名稱  
    "advertiser": "string",         // 必填 - 廣告商
    "main_title": "string",         // 必填 - 主標題
    "subtitle": "string",           // 可選 - 副標題
    "landing_page": "string",       // 必填 - 目標連結
    "call_to_action": "string",     // 可選 - CTA 按鈕文字，預設"立即了解"
    "image_path_m": "string",       // 必填 - 1200x628 圖片
    "image_path_s": "string"        // 必填 - 300x300 圖片
}
```

### 廣告類型特定欄位

#### 1. 投票廣告 (Vote Ad)
```json
{
    // ...基礎欄位
    "vote_title": "string",                    // 投票標題
    "vote_image": "string",                    // 投票背景圖
    "vote_id": "string",                       // 投票 ID
    "divider_color": "#ff0000",                // 分隔線顏色
    "vote_width": "80%",                       // 投票寬度
    "bg_color": "#ffffff",                     // 背景顏色
    "vote_position": "bottom",                 // 投票位置
    "min_position": 50,                        // 最小位置
    "max_position": 70,                        // 最大位置
    "timeout": 2000,                           // 超時時間
    "winner_bg_color": "#26D07C",              // 勝利者背景色
    "winner_text_color": "#ffffff",            // 勝利者文字色
    "loser_bg_color": "#000000",               // 失敗者背景色
    "loser_text_color": "#ffffff",             // 失敗者文字色
    "vote_options": [                          // 投票選項陣列
        {
            "title": "string",
            "text_color": "#207AED",
            "bg_color": "#E7F3FF", 
            "target_url": "string"
        }
    ],
    "payload_vote_widget": "string"            // 重要：投票套件 payload
}
```

#### 2. 滑動廣告 (Slide Ad)
```json
{
    // ...基礎欄位
    "background_url": "string",                // 背景圖片
    "slide_items": [                           // 滑動項目陣列
        {
            "image_url": "string",
            "target_url": "string"
        }
    ],
    "payload_game_widget": "string"            // 重要：遊戲套件 payload
}
```

#### 3. GIF 廣告
```json
{
    // ...基礎欄位
    "background_image": "string",              // 背景圖片
    "background_url": "string",                // 背景連結
    "target_url": "string",                    // 目標連結
    "end_date": "string",                      // 結束日期
    "description_text": "活動截止倒數",         // 描述文字
    "position": "3",                           // 位置
    "date_number_color": "#FFFFFF",            // 日期數字顏色
    "description_color": "#FFFFFF",            // 描述顏色
    "date_word_color": "#FFFFFF",              // 日期文字顏色
    "date_number_size": "4",                   // 日期數字大小
    "description_size": "4",                   // 描述大小
    "date_word_size": "4",                     // 日期文字大小
    "show_day": "true",                        // 顯示天數
    "show_hour": "true",                       // 顯示小時
    "show_min": "true",                        // 顯示分鐘
    "show_sec": "true",                        // 顯示秒數
    "payload_game_widget": "string"            // 重要：遊戲套件 payload
}
```

#### 4. 彈跳影音廣告 (Popup Video)
```json
{
    // ...基礎欄位
    "background_url": "string",                // 背景圖片
    "payload_game_widget": "string",           // 遊戲套件 payload
    "payload_popupJson": "string"              // 重要：彈跳 JSON payload
}
```

## 🔑 關鍵洞察

### 1. Payload 是核心
每種廣告類型的關鍵區別在於：
- **投票廣告**：`payload_vote_widget`
- **一般廣告**：`payload_game_widget` 
- **彈跳影音**：`payload_game_widget` + `payload_popupJson`

### 2. 調用 suprad 腳本的模式
```python
with sync_playwright() as playwright:
    result = run_suprad(playwright, ad_data, '廣告類型')
```

### 3. Session 保存模式
```python
# 保存表單數據到 session（失敗時重新填充）
for key, value in ad_data.items():
    session[f'{ad_type}_{key}'] = value
```

## 🎁 寶箱廣告 JSON 結構建議

基於分析，寶箱廣告的 JSON 結構應該是：

```json
{
    // 基礎必填欄位
    "adset_id": "string",
    "display_name": "string", 
    "advertiser": "string",
    "main_title": "string",
    "subtitle": "string",
    "landing_page": "string",
    "call_to_action": "立即開啟",
    "image_path_m": "string",
    "image_path_s": "string",
    
    // 寶箱特定欄位
    "treasure_box_image": "string",        // 寶箱圖片
    "treasure_content_image": "string",    // 寶箱內容圖片
    "treasure_content_text": "string",    // 寶箱內容文字
    "animation_type": "flip",              // 動畫類型: flip, fade, rotate
    "animation_duration": 500,             // 動畫持續時間(ms)
    "reward_display_time": 3000,           // 獎品顯示時間(ms)
    "can_reopen": false,                   // 是否可重複開啟
    
    // 必要的 payload
    "payload_game_widget": "string"        // 遊戲套件 payload
}
```

## ✅ 最簡開發流程

對於寶箱廣告，您只需要告訴我：

1. **寶箱特定欄位需求**：
   - 需要哪些自定義欄位？
   - 欄位的資料類型和預設值？

2. **payload_game_widget 格式**：
   - 寶箱廣告的 payload 結構是什麼？

3. **suprad 腳本調用參數**：
   - 調用 `run_suprad()` 時的廣告類型參數是什麼？

**就這樣！其他都是標準化的實現。**

## 🚀 立即可實現

有了這個結構分析，我現在可以立即實現寶箱廣告，只需要您提供：
- 寶箱廣告特有的 JSON 欄位
- payload_game_widget 的期望格式
- 在 suprad 腳本中的廣告類型名稱

這樣確實比討論 UI 細節更有效率！