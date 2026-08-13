# 🌐 Web介面依賴安裝指南

## ❗ 問題說明

Web介面需要Flask套件,但您的系統要求使用虛擬環境或系統套件管理器。

---

## ✅ 解決方案

### 方案1: 使用CLI命令列 (推薦)

**無需安裝任何額外依賴!**

```bash
# 匯入單一檔案
python3 import_local_data.py -f 您的檔案.json

# 匯入整個目錄
python3 import_local_data.py -d ./資料夾/ --recursive

# 建立範例模板
python3 import_local_data.py --create-template

# 查看幫助
python3 import_local_data.py --help
```

**優點:**
- ✅ 無需安裝依賴
- ✅ 功能完整
- ✅ 適合批次處理
- ✅ 腳本自動化

---

### 方案2: 安裝系統Flask套件

**使用系統套件管理器安裝Flask:**

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3-flask

# 安裝完成後執行
python3 web_import_server.py
```

**優點:**
- ✅ 系統級安裝,穩定
- ✅ 不需要虛擬環境

**缺點:**
- ⚠️ 需要sudo權限
- ⚠️ 版本可能較舊

---

### 方案3: 使用虛擬環境

**建立獨立的Python環境:**

```bash
# 1. 安裝venv支援
sudo apt install python3-venv

# 2. 建立虛擬環境
cd art-history-database
python3 -m venv importer_venv

# 3. 啟動虛擬環境
source importer_venv/bin/activate

# 4. 安裝依賴
pip install flask werkzeug

# 5. 執行Web介面
python web_import_server.py

# 6. 使用完畢後退出虛擬環境
deactivate
```

**優點:**
- ✅ 獨立環境,不影響系統
- ✅ 可以使用最新版本

**缺點:**
- ⚠️ 每次使用需啟動虛擬環境

---

### 方案4: 使用簡化版Web介面

**無需Flask,使用Python內建HTTP服務器:**

```bash
python3 simple_web_import.py
```

然後打開瀏覽器訪問: `http://localhost:5050`

**特點:**
- ✅ 無需安裝依賴
- ✅ 提供使用說明頁面
- ⚠️ 僅顯示說明,實際匯入仍需使用CLI

---

## 🎯 推薦方案比較

| 方案 | 難度 | 功能 | 推薦度 |
|-----|------|------|--------|
| **CLI命令列** | ⭐ 簡單 | ⭐⭐⭐⭐⭐ 完整 | ⭐⭐⭐⭐⭐ |
| **系統Flask** | ⭐⭐ 中等 | ⭐⭐⭐⭐⭐ 完整 | ⭐⭐⭐⭐ |
| **虛擬環境** | ⭐⭐⭐ 較難 | ⭐⭐⭐⭐⭐ 完整 | ⭐⭐⭐ |
| **簡化版** | ⭐ 簡單 | ⭐ 僅說明 | ⭐⭐ |

---

## 💡 建議

### 如果您是...

**1. 第一次使用 / 想快速開始**
→ 使用 **CLI命令列** (方案1)

**2. 需要Web介面 + 有sudo權限**
→ 使用 **系統Flask** (方案2)

**3. 需要Web介面 + 無sudo權限**
→ 使用 **虛擬環境** (方案3)

**4. 只想看看Web介面長什麼樣**
→ 使用 **簡化版** (方案4)

---

## 📝 CLI快速上手

### 步驟1: 建立範例模板

```bash
cd art-history-database
python3 import_local_data.py --create-template
```

這會在 `import_templates/` 建立範例檔案。

### 步驟2: 查看範例

```bash
ls -la import_templates/
cat import_templates/template.json
```

### 步驟3: 準備您的資料

參考範例,將您的資料整理成JSON、TXT或PDF格式。

### 步驟4: 匯入資料

```bash
# 匯入單一檔案
python3 import_local_data.py -f my_artwork.json

# 匯入整個目錄
python3 import_local_data.py -d ./my_data/ --recursive
```

### 步驟5: 驗證

在OpenWebUI (http://localhost:8080) 中提問:
```
"資料庫中有哪些本地匯入的作品?"
```

---

## 🔍 常用CLI命令

```bash
# 查看所有選項
python3 import_local_data.py --help

# 只存到Neo4j
python3 import_local_data.py -f file.json --neo4j-only

# 只存到ChromaDB
python3 import_local_data.py -f file.json --chromadb-only

# 測試模式(不儲存)
python3 import_local_data.py -f file.json --no-save

# 顯示詳細資訊
python3 import_local_data.py -f file.json --verbose
```

---

## 📚 完整文檔

- **快速參考**: `本地資料匯入_快速參考.md`
- **完整指南**: `本地資料匯入完整指南.md`
- **系統架構**: `本地資料匯入系統架構圖.md`

---

## 🎉 總結

**最簡單的方式**: 直接使用CLI命令列

```bash
python3 import_local_data.py -f 您的檔案.json
```

無需安裝任何依賴,功能完整,立即可用! ✨
