# 專案設定指南

## 1. 建立本機設定

```bash
cp .env.example .env
```

建議至少設定以下欄位：

```bash
SECRET_KEY=change-me
ALLOWED_EMAILS=portfolio-owner@example.com,reviewer@example.edu

MONGO_CONNECTION_STRING=mongodb://localhost:27017/automation_demo
MONGO_DATABASE=automation_demo

PLATFORM_EMAIL=automation.user@example.com
PLATFORM_PASSWORD=change-me
PLATFORM_COOKIE=
PREVIEW_COOKIE=
PLATFORM_ORG_LABEL=Example Organization
```

## 2. 安裝依賴

```bash
pip install -r requirements.txt
playwright install
```

## 3. 啟動服務

```bash
python run.py
```

應用預設啟動於 `http://localhost:5002`。

## 4. 作品集模式的建議設定

- 不要填入真實客戶資料、真實 Cookie 或正式環境帳號
- 只保留足以展示流程的測試資料與匿名化設定
- 如果要 Demo 截圖或報表頁，請準備自己的測試資料來源

## 安全性注意事項

- `.env` 不應提交到版本控制
- 真實 Cookie、API key、service account 檔案不應放在 repo 中
- 公開展示時，建議使用專門的示範帳號與示範資料庫

## 常見問題

### MongoDB 連線失敗

1. 確認 MongoDB 正在執行
2. 檢查 `.env` 內的連線字串與資料庫名稱
3. 若只想展示 UI，可以先略過需要資料庫的頁面

### Playwright 啟動失敗

```bash
playwright install --with-deps
```

### 截圖或報表沒有載入

- 這個公開版不再內建任何正式環境 Cookie
- 若要示範這些頁面，請在 `.env` 內自行填入測試環境 Cookie

## 開發提示

- `app/routes/` 放主要流程路由
- `templates/` 放各種內容格式頁面
- `app/services/url_builder.py` 與 `app/routes/screenshot.py` 可以展示截圖流程的工程設計
- `app/routes/main.py` 可以展示資料查詢與報表整合邏輯
