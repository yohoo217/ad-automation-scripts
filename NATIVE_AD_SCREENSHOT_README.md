# Native 廣告多尺寸截圖工具

## 功能說明

本工具可以根據提供的 UUID，自動截取 Native 廣告的所有尺寸（1200x628、300x300、320x50、300x250、640x200），每種尺寸使用不同的裝置和滾動設定。

## 支援的廣告尺寸

### 1. 1200x628 (大圖廣告)
- **裝置**: 手機畫面 (iPhone X)
- **滾動距離**: 4800px
- **預覽頁面**: PTT 文章頁面
- **用途**: 適用於文章內大圖廣告

### 2. 300x300 (方形廣告)
- **裝置**: 手機畫面 (iPhone X) 
- **滾動距離**: 不滾動
- **預覽頁面**: PTT 文章列表
- **用途**: 適用於列表頁方形廣告

### 3. 320x50 (橫幅廣告)
- **裝置**: 手機畫面 (iPhone X)
- **滾動距離**: 不滾動  
- **預覽頁面**: PTT 文章頁面
- **用途**: 適用於頁面頂部或底部橫幅

### 4. 300x250 (中等廣告)
- **裝置**: 桌機畫面 (1920x1080)
- **滾動距離**: 4800px
- **預覽頁面**: MoPTT 頁面
- **用途**: 適用於桌面版中等尺寸廣告

### 5. 640x200 (寬幅廣告)
- **裝置**: 手機畫面 (iPhone X)
- **滾動距離**: 不滾動
- **預覽頁面**: PNN 文章頁面  
- **用途**: 適用於寬版橫幅廣告

## 使用方式

1. 訪問 `/native-ad-screenshot` 頁面
2. 輸入有效的 AdUnit UUID
3. 點擊「開始多尺寸截圖」按鈕
4. 等待所有 5 種尺寸的截圖完成（約 30-60 秒）
5. 在結果區域預覽和下載所需的截圖

## 技術實作

### URL 建構模板

每種尺寸都有對應的 URL 模板：

```python
url_templates = {
    '1200x628': {
        'ptt-article': 'https://trek.aotter.net/trek-ad-preview/pages/ptt-article/index.html'
    },
    '300x300': {
        'ptt-article-list': 'https://trek.aotter.net/trek-ad-preview/pages/ptt-article-list/index.html'
    },
    '320x50': {
        'ptt-article': 'https://trek.aotter.net/trek-ad-preview/pages/ptt-article/index.html'
    },
    '300x250': {
        'moptt': 'https://moptt.tw/p/Gossiping.M.1718675708.A.183'
    },
    '640x200': {
        'pnn-article': 'https://aotter.github.io/trek-ad-preview/pages/pnn-article/'
    }
}
```

### 前端流程

1. **AJAX 請求**: 使用 JavaScript 進行非同步請求
2. **進度條**: 即時顯示截圖進度
3. **結果展示**: 完成後顯示所有截圖的預覽和下載連結

### 後端 API

- **路由**: `/create-native-screenshot`
- **方法**: POST
- **格式**: JSON

請求格式：
```json
{
    "uuid": "84ab2622-dc2b-402d-b42b-b3ea54f9faeb",
    "size": "1200x628",
    "device": "iphone_x",
    "scroll_distance": 4800,
    "template": "ptt-article"
}
```

回應格式：
```json
{
    "success": true,
    "file_path": "/path/to/screenshot.png",
    "filename": "native_1200_628_device-iphone-x_uuid-xxx_scroll-4800px_timestamp.png",
    "file_size": "1.2MB",
    "device_name": "iPhone X",
    "preview_url": "/screenshot_base64/screenshots/...",
    "download_url": "/screenshot_base64/screenshots/..."
}
```

## 檔案命名規則

截圖檔案會自動以下列格式命名：
```
native_{size}_device-{device}_uuid-{uuid}_{scroll_suffix}_{timestamp}.png
```

例如：
```
native_1200_628_device-iphone-x_uuid-84ab2622-dc2b-402d-b42b-b3ea54f9faeb_scroll-4800px_143022.png
```

## 注意事項

1. **UUID 驗證**: 確保 UUID 存在於 MongoDB 資料庫中
2. **等待時間**: 完整的 5 尺寸截圖需要 30-60 秒
3. **檔案儲存**: 截圖儲存在 `uploads/screenshots/{YYYYMMDD}/` 目錄下
4. **瀏覽器模擬**: 使用 Playwright Chromium 進行截圖
5. **Cookie 支援**: 自動使用登入 Cookie 進行認證

## 錯誤處理

- UUID 不存在：返回 404 錯誤
- 網址建構失敗：返回 400 錯誤  
- 截圖過程異常：返回 500 錯誤並記錄詳細日誌

## 擴展性

如需新增其他尺寸，可在以下位置添加配置：

1. `build_native_screenshot_url()` 函數中的 `url_templates`
2. 前端 JavaScript 中的 `configs` 陣列
3. 模板中的尺寸配置說明區塊 