# 日誌控制說明

## 如何關閉特定日誌

在 `app.py` 檔案的開頭部分，您可以看到以下兩個控制變數：

```python
# 日誌級別控制
LOG_LEVEL_VERBOSE = False  # 設為 False 可關閉詳細日誌
LOG_LEVEL_BEFORE_AFTER = True  # 設為 False 可關閉前後截圖日誌
```

## 控制選項

### 1. 關閉詳細日誌 (`LOG_LEVEL_VERBOSE`)
- **設為 `False`**：只顯示重要的 WARNING 和 ERROR 級別日誌
- **設為 `True`**：顯示所有 INFO 級別的詳細日誌

### 2. 關閉前後截圖日誌 (`LOG_LEVEL_BEFORE_AFTER`)
- **設為 `False`**：不顯示 640x200 PNN 前後截圖的日誌訊息
- **設為 `True`**：顯示前後截圖的詳細進度

## 常見組合

### 🔇 完全安靜模式（只顯示錯誤）
```python
LOG_LEVEL_VERBOSE = False
LOG_LEVEL_BEFORE_AFTER = False
```

### 📊 只顯示前後截圖進度
```python
LOG_LEVEL_VERBOSE = False
LOG_LEVEL_BEFORE_AFTER = True
```

### 📝 顯示所有日誌
```python
LOG_LEVEL_VERBOSE = True
LOG_LEVEL_BEFORE_AFTER = True
```

### 📋 只顯示詳細日誌（但不顯示前後截圖）
```python
LOG_LEVEL_VERBOSE = True
LOG_LEVEL_BEFORE_AFTER = False
```

## 快速修改方法

如果您想要關閉前後截圖的日誌輸出，只需要：

1. 打開 `app.py` 檔案
2. 找到第 31 行左右的：
   ```python
   LOG_LEVEL_BEFORE_AFTER = True  # 設為 False 可關閉前後截圖日誌
   ```
3. 將 `True` 改為 `False`：
   ```python
   LOG_LEVEL_BEFORE_AFTER = False  # 設為 False 可關閉前後截圖日誌
   ```
4. 重新啟動 Flask 應用程式

## 效果對比

### 開啟前後截圖日誌時：
```
📸 PNN 640x200: 主截圖前 2 秒截圖完成: /path/to/BEFORE_123456.png
📸 PNN 640x200: 等待 2 秒後準備主截圖
📸 PNN 640x200: 等待 2 秒後準備後續截圖
📸 PNN 640x200: 主截圖後 2 秒截圖完成: /path/to/AFTER_123459.png
```

### 關閉前後截圖日誌時：
```
截圖完成，檔案儲存至: /path/to/main_screenshot.png
640x200 使用 PNN 模板截圖完成
``` 