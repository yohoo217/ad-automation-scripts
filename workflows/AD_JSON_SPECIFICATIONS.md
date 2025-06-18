# 📋 廣告 JSON Payload 規格文件

## 🎯 Overview

根據現有廣告類型分析，每個廣告都需要兩個主要的 JSON payload：
- **`payload_game_widget`**: 定義廣告的互動邏輯和視覺效果
- **`payload_popup_json`**: 定義彈跳層內容（僅彈跳影音類需要）

## 📊 現有廣告類型的 JSON 結構

### 1. 🎮 GIF 廣告 (SIMPLE 類型)
```json
{
  "type": "SIMPLE",
  "data": {
    "img_background": "https://example.com/background.gif"
  },
  "invokes": [
    {
      "action": "OPEN_EXTERNAL_BROWSER",
      "payload": {
        "url": "https://target-landing-page.com"
      }
    }
  ],
  "_sys": {
    "popupActionKeys": [
      "a"
    ]
  }
}
```

### 2. ⏰ 倒數廣告 (COUNTDOWN 類型)
```json
{
  "type": "COUNTDOWN",
  "imgProperty": {
    "endDate": "2025-12-31 23:59:59",
    "backgroundImage": "https://example.com/background.jpg",
    "descriptionText": "活動截止倒數",
    "position": 3,
    "dateNumberColor": "#FFFFFF",
    "descriptionColor": "#FFFFFF", 
    "dateWordColor": "#FFFFFF",
    "dateNumberSize": "4",
    "descriptionSize": "4",
    "dateWordSize": "4",
    "showDay": true,
    "showHour": true,
    "showMin": true,
    "showSec": true
  },
  "invokes": [
    {
      "action": "OPEN_EXTERNAL_BROWSER",
      "payload": {
        "url": "https://target-landing-page.com"
      }
    }
  ]
}
```

### 3. 🗳️ 投票廣告 (PURE_VOTE 類型)
```json
{
  "type": "PURE_VOTE",
  "assets": {
    "dividerColor": "#ff0000",
    "voteId": "myVoteId",
    "title": "投票標題",
    "image": "https://example.com/vote-image.jpg",
    "width": "80%",
    "bgColor": "#ffffff",
    "votePosition": "bottom",
    "display": {
      "minPosition": 50,
      "maxPosition": 70,
      "timeout": 2000
    },
    "displayAnimation": ["fade", "slide"],
    "options": [
      {
        "title": "選項一",
        "textColor": "#207AED",
        "bgColor": "#E7F3FF",
        "invokes": [
          {
            "action": "OPEN_EXTERNAL_BROWSER", 
            "payload": {
              "url": "https://option1-target.com"
            }
          }
        ]
      },
      {
        "title": "選項二",
        "textColor": "#207AED",
        "bgColor": "#E7F3FF",
        "invokes": [
          {
            "action": "OPEN_EXTERNAL_BROWSER",
            "payload": {
              "url": "https://option2-target.com"
            }
          }
        ]
      }
    ],
    "winner": {
      "bgColor": "#26D07C",
      "textColor": "#ffffff"
    },
    "loser": {
      "bgColor": "#000000", 
      "textColor": "#ffffff"
    }
  }
}
```

### 4. 🎞️ 滑動廣告 (SLIDE 相關類型)
```json
{
  "type": "SLIDE_HORIZONTAL", // 或 SLIDE_VERTICAL, SLIDE_CUBE_VERTICAL
  "data": {
    "img_background": "https://example.com/background.jpg",
    "slides": [
      {
        "image_url": "https://example.com/slide1.jpg",
        "target_url": "https://slide1-target.com"
      },
      {
        "image_url": "https://example.com/slide2.jpg", 
        "target_url": "https://slide2-target.com"
      }
    ]
  },
  "invokes": [
    {
      "action": "OPEN_EXTERNAL_BROWSER",
      "payload": {
        "url": "https://default-landing-page.com"
      }
    }
  ]
}
```

## 📦 寶箱廣告 JSON 規格設計

基於您的需求，我建議寶箱廣告使用以下 JSON 結構：

### 🎁 寶箱廣告 (TREASURE_BOX 類型)
```json
{
  "type": "TREASURE_BOX",
  "assets": {
    "treasureBox": {
      "closedImage": "https://example.com/treasure-box-closed.png",
      "openedImage": "https://example.com/treasure-box-opened.png",
      "position": {
        "x": "center", // "left", "center", "right" 或具體像素值
        "y": "center"  // "top", "center", "bottom" 或具體像素值
      },
      "size": {
        "width": 120,
        "height": 120
      },
      "animation": {
        "openType": "flip",    // "flip", "fade", "scale", "bounce"
        "duration": 500,       // 動畫持續時間 (毫秒)
        "easing": "ease-out"   // 動畫緩動函數
      }
    },
    "treasure": {
      "type": "image_text",   // "image", "text", "image_text", "video"
      "content": {
        "image": "https://example.com/treasure-content.jpg",
        "title": "恭喜獲得優惠券！",
        "description": "立即使用享受 50% 折扣",
        "ctaText": "立即領取",
        "ctaStyle": {
          "backgroundColor": "#FF6B35",
          "textColor": "#FFFFFF",
          "borderRadius": 8
        }
      },
      "display": {
        "duration": 3000,      // 顯示持續時間 (毫秒)，0 表示永久顯示
        "position": "overlay", // "overlay", "replace", "below"
        "showCloseButton": true
      }
    },
    "backgroundImage": "https://example.com/background.jpg",
    "interaction": {
      "clickLimit": 1,        // 點擊次數限制，-1 表示無限制
      "resetOnRefresh": true, // 重新整理後是否重置點擊次數
      "hapticFeedback": true  // 是否提供觸覺反饋 (手機)
    },
    "sound": {
      "enabled": false,
      "openSound": "https://example.com/open-sound.mp3",
      "treasureSound": "https://example.com/treasure-sound.mp3"
    }
  },
  "invokes": [
    {
      "action": "OPEN_EXTERNAL_BROWSER",
      "payload": {
        "url": "https://treasure-landing-page.com"
      }
    }
  ],
  "_sys": {
    "popupActionKeys": ["click"],
    "trackingEvents": [
      "treasure_box_view",
      "treasure_box_click", 
      "treasure_opened",
      "treasure_cta_click"
    ]
  }
}
```

## 🔧 JSON 結構說明

### 必要欄位 (Required)
- `type`: 廣告類型標識符
- `assets` 或 `data`: 廣告的核心數據
- `invokes`: 點擊行為定義

### 可選欄位 (Optional)
- `_sys`: 系統相關設定
- `imgProperty`: 圖片相關屬性 (倒數廣告專用)
- `sound`: 音效設定
- `animation`: 動畫設定

### 通用 Action 類型
- `OPEN_EXTERNAL_BROWSER`: 開啟外部瀏覽器
- `TRACK_EVENT`: 追蹤事件
- `SHOW_POPUP`: 顯示彈跳窗
- `PLAY_SOUND`: 播放音效

## 🎯 寶箱廣告開發所需資訊

為了完善寶箱廣告的 JSON 規格，我需要您提供：

### 1. 視覺設計需求
- **寶箱外觀**：靜態圖片還是動畫？
- **開啟效果**：翻蓋、縮放、漸變還是其他？
- **獎品展示**：純文字、圖片、影片還是混合？

### 2. 互動邏輯需求  
- **觸發方式**：點擊、懸停還是自動？
- **重複性**：可重複開啟還是一次性？
- **時間控制**：獎品顯示多久？

### 3. 內容格式需求
- **獎品類型**：優惠券、禮品、資訊還是其他？
- **行動呼籲**：需要 CTA 按鈕嗎？導向哪裡？
- **多獎品**：是否支援隨機或多種獎品？

### 4. 表單管理需求
- **管理者配置**：哪些項目需要讓管理者自定義？
- **素材上傳**：需要上傳哪些圖片/影片？
- **預設值**：有哪些合理的預設設定？

## 🚀 下一步開發流程

一旦您提供上述資訊，我將：

1. **完善 JSON 規格**：根據您的需求調整 JSON 結構
2. **創建表單模板**：設計對應的 HTML 表單
3. **實現 JavaScript 邏輯**：動態生成 JSON payload
4. **創建預覽功能**：即時預覽寶箱互動效果
5. **整合後端邏輯**：連接到現有的自動化系統

請您回答上述問題，我就能為您量身定制完整的寶箱廣告 JSON 規格和開發方案！