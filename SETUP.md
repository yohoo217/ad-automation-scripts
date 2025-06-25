# 🚀 AD Automation Scripts 專案設定指南

## 📋 環境設定

### 1. 複製環境變數範本
```bash
cp .env.example .env
```

### 2. 設定環境變數
編輯 `.env` 檔案，填入正確的設定值：

```bash
# MongoDB 連線設定
MONGO_CONNECTION_STRING=your_actual_connection_string
MONGO_USERNAME=your_username
MONGO_PASSWORD=your_password
MONGO_DATABASE=your_database

# Trek 系統登入帳號（可選）
TREK_EMAIL=your_email@example.com
TREK_PASSWORD=your_password
```

### 3. Trek 帳號設定選項

#### 選項 A：設定環境變數（推薦）
在 `.env` 檔案中設定 `TREK_EMAIL` 和 `TREK_PASSWORD`

#### 選項 B：啟動時手動輸入
如果不設定環境變數，系統會在啟動時彈出輸入視窗

## 🔐 安全性說明

- ⚠️ **絕對不要** 將 `.env` 檔案上傳到版本控制系統
- ✅ `.env` 已包含在 `.gitignore` 中
- ✅ 使用 `.env.example` 作為範本供其他開發者參考

## 🚀 啟動專案

```bash
# 安裝相依套件
pip install -r requirements.txt

# 啟動專案
python run.py
```

## 🛠️ 疑難排解

### 問題：缺少 tkinter 模組
```bash
# macOS
brew install python-tk

# Ubuntu/Debian
sudo apt-get install python3-tk

# Windows
# tkinter 通常已包含在 Python 安裝中
```

### 問題：彈出視窗沒有顯示
確保你的環境支援 GUI 視窗顯示，如果在伺服器環境中執行，請設定環境變數。 