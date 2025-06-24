# 🔄 開發工作流程

本文檔描述廣告自動化專案的標準開發流程。

## 📋 開發階段

### 1. 需求分析
- 確定廣告類型和功能需求
- 分析技術可行性
- 估算開發時間
- 制定實現計畫

### 2. 設計階段
- 設計數據結構
- 規劃 API 接口
- 設計用戶界面
- 制定測試策略

### 3. 開發實現
- 建立開發分支
- 實現核心功能
- 編寫單元測試
- 進行代碼審查

### 4. 測試驗證
- 執行自動化測試
- 進行手動測試
- 性能測試
- 安全性檢查

### 5. 部署發布
- 準備生產環境
- 執行部署腳本
- 監控系統狀態
- 收集用戶反饋

## 🌿 分支管理策略

```
main
├── feature/new-ad-type
├── hotfix/critical-bug
└── release/v1.2.0
```

### 分支類型
- **main**: 主分支，穩定版本
- **feature/***: 功能開發分支
- **hotfix/***: 緊急修復分支
- **release/***: 版本發布分支

### 合併規則
- 所有功能必須通過 Pull Request
- 至少一人代碼審查
- 所有測試必須通過
- 無衝突才能合併

## 🔧 開發環境設置

### 環境需求
- Python 3.9+
- Flask 2.0+
- Node.js 16+ (用於前端工具)
- Git 2.0+

### 初始化步驟
```bash
# 1. 克隆專案
git clone <repository-url>
cd ad-automation-scripts

# 2. 建立虛擬環境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 3. 安裝依賴
pip install -r requirements.txt

# 4. 設置環境變量
cp .env.example .env
# 編輯 .env 檔案

# 5. 運行應用
python run.py
```

## 📝 提交訊息規範

使用 Conventional Commits 格式：

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

### 類型 (type)
- `feat`: 新功能
- `fix`: 錯誤修復
- `docs`: 文檔更新
- `style`: 代碼格式調整
- `refactor`: 代碼重構
- `test`: 測試相關
- `chore`: 建構過程或輔助工具變更

### 範例
```
feat(ads): 新增寶箱廣告類型

- 實現寶箱動畫效果
- 支援自定義獎勵文字
- 添加響應式設計

Closes #123
```

## 🧪 測試流程

### 測試類型
1. **單元測試**: 測試個別函數和類別
2. **集成測試**: 測試模組間互動
3. **端到端測試**: 測試完整用戶流程
4. **性能測試**: 評估系統性能

### 測試執行
```bash
# 運行所有測試
python -m pytest

# 運行特定測試
python -m pytest tests/test_ads.py

# 生成覆蓋率報告
python -m pytest --cov=app tests/
```

## 📊 代碼品質檢查

### 自動化工具
- **Black**: 代碼格式化
- **Flake8**: 代碼風格檢查
- **MyPy**: 類型檢查
- **Bandit**: 安全性掃描

### 執行檢查
```bash
# 格式化代碼
black .

# 檢查代碼風格
flake8 .

# 類型檢查
mypy app/

# 安全性掃描
bandit -r app/
```

## 🚀 部署流程

### 準備階段
1. 確認所有測試通過
2. 更新版本號
3. 準備發布說明
4. 備份現有版本

### 部署步驟
1. 合併到 main 分支
2. 創建版本標籤
3. 執行自動化部署
4. 驗證部署結果
5. 監控系統狀態

### 回滾計畫
- 準備快速回滾腳本
- 保留前一版本備份
- 監控關鍵指標
- 建立應急聯絡流程 