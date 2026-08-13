# 🎨 本地資料匯入系統

**版本**: v1.0
**狀態**: ✅ 可用 (CLI已就緒,Web需安裝Flask)

---

## 🎯 重要說明

### ✅ CLI命令列 - 立即可用

**無需安裝任何依賴,現在就能使用!**

```bash
# 建立範例
python3 import_local_data.py --create-template

# 匯入資料
python3 import_local_data.py -f 您的檔案.json
```

### ⚠️ Web介面 - 需要Flask

Web介面需要先安裝Flask套件才能使用。

**安裝方法**: 查看 `安裝Web依賴.md`

---

## 🚀 快速開始 (3分鐘)

### 1. 建立範例模板

```bash
python3 import_local_data.py --create-template
```

### 2. 查看範例

```bash
cat import_templates/template.json
```

### 3. 匯入資料

```bash
# 匯入單一檔案
python3 import_local_data.py -f 您的檔案.json

# 匯入整個目錄
python3 import_local_data.py -d ./資料夾/ --recursive
```

**就這麼簡單!** ✨

---

## 📚 文檔導覽

| 文檔 | 用途 | 推薦度 |
|-----|------|--------|
| **快速開始_無需Web介面.md** | 新手入門,CLI使用 | ⭐⭐⭐⭐⭐ |
| **本地資料匯入_快速參考.md** | 常用命令速查 | ⭐⭐⭐⭐⭐ |
| **本地資料匯入完整指南.md** | 詳細功能說明 | ⭐⭐⭐⭐ |
| **安裝Web依賴.md** | Web介面安裝 | ⭐⭐⭐ |
| **本地資料匯入系統架構圖.md** | 系統架構參考 | ⭐⭐ |

---

## 💡 使用建議

### 第一次使用?

👉 閱讀: **快速開始_無需Web介面.md**

### 想快速查命令?

👉 閱讀: **本地資料匯入_快速參考.md**

### 需要Web介面?

👉 閱讀: **安裝Web依賴.md**

### 想了解完整功能?

👉 閱讀: **本地資料匯入完整指南.md**

---

## ⚡ 常用命令

```bash
# 查看幫助
python3 import_local_data.py --help

# 建立範例
python3 import_local_data.py --create-template

# 匯入檔案
python3 import_local_data.py -f file.json

# 匯入目錄
python3 import_local_data.py -d ./folder/ --recursive

# 只存Neo4j
python3 import_local_data.py -f file.json --neo4j-only

# 只存ChromaDB
python3 import_local_data.py -f file.json --chromadb-only

# 測試模式
python3 import_local_data.py -f file.json --no-save

# 詳細輸出
python3 import_local_data.py -f file.json --verbose
```

---

## 📁 支援格式

| 格式 | 副檔名 | 狀態 |
|-----|--------|------|
| JSON | `.json`, `.jsonl` | ✅ 完全支援 |
| 文字檔 | `.txt`, `.md` | ✅ 完全支援 |
| PDF | `.pdf` | ⚠️ 需要額外套件 |

---

## 🔍 驗證匯入

### 在OpenWebUI測試

1. 打開 http://localhost:8080
2. 選擇任一RAG模型
3. 提問: "資料庫中有哪些本地匯入的作品?"

### 查詢Neo4j

```bash
docker exec art-history-neo4j cypher-shell -u neo4j -p arthistory123 \
  "MATCH (n:Artwork) WHERE n.source CONTAINS 'local' RETURN count(n)"
```

---

## 🎉 系統特色

✅ **多格式支援** - JSON、TXT、MD、PDF
✅ **智能處理** - 自動提取和標準化
✅ **即時可用** - 匯入後立即在RAG系統中使用
✅ **批次處理** - 一次匯入整個資料夾
✅ **無需依賴** - CLI工具開箱即用

---

## 🆘 問題排除

### CLI無法執行?

```bash
# 確認Python版本
python3 --version

# 確認檔案存在
ls -la import_local_data.py
```

### Web介面無法開啟?

**正常情況!** 需要先安裝Flask。

👉 查看: `安裝Web依賴.md`

或直接使用CLI,功能完全相同。

### 資料庫連接失敗?

```bash
# 檢查服務
docker ps | grep -E "neo4j|chromadb"

# 啟動服務
docker-compose up -d
```

---

## 📞 更多幫助

- 📖 查看文檔: `本地資料匯入完整指南.md`
- 🔧 Web安裝: `安裝Web依賴.md`
- ⚡ 快速參考: `本地資料匯入_快速參考.md`
- 🚀 快速開始: `快速開始_無需Web介面.md`

---

## ✨ 立即開始

```bash
# 1. 建立範例
python3 import_local_data.py --create-template

# 2. 查看範例
ls -la import_templates/

# 3. 匯入您的資料
python3 import_local_data.py -f 您的檔案.json
```

**就這麼簡單!** 🎨✨

---

**最後更新**: 2025-01-30
**維護者**: Art History Database Team
