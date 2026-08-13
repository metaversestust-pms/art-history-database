# 🚀 快速開始 - 使用CLI匯入本地資料

## ✅ 好消息

**CLI命令列工具已經可以使用,無需安裝任何額外依賴!**

Web介面需要Flask套件,但CLI工具已經包含所有核心功能。

---

## 📋 三步快速開始

### 步驟1: 建立範例模板

```bash
cd art-history-database
python3 import_local_data.py --create-template
```

這會建立以下範例檔案:
- `import_templates/template.json` - JSON格式範例
- `import_templates/template_structured.txt` - 結構化文字
- `import_templates/template_markdown.md` - Markdown格式
- `import_templates/template_separated.txt` - 分隔符格式

### 步驟2: 查看範例

```bash
# 查看所有範例
ls -la import_templates/

# 查看JSON範例內容
cat import_templates/template.json
```

### 步驟3: 匯入您的資料

```bash
# 匯入單一檔案
python3 import_local_data.py -f 您的檔案.json

# 匯入整個目錄
python3 import_local_data.py -d ./資料夾/ --recursive
```

---

## 💡 常用命令

### 基本匯入

```bash
# 匯入JSON檔案
python3 import_local_data.py -f artwork.json

# 匯入文字檔
python3 import_local_data.py -f artwork.txt

# 匯入PDF檔案 (需要安裝PyPDF2或pdfplumber)
python3 import_local_data.py -f artwork.pdf
```

### 批次匯入

```bash
# 匯入目錄中的所有檔案
python3 import_local_data.py -d ./my_artworks/

# 遞迴處理所有子目錄
python3 import_local_data.py -d ./my_artworks/ --recursive
```

### 選擇儲存位置

```bash
# 只存到Neo4j圖資料庫
python3 import_local_data.py -f file.json --neo4j-only

# 只存到ChromaDB向量資料庫
python3 import_local_data.py -f file.json --chromadb-only

# 測試模式(只處理不儲存)
python3 import_local_data.py -f file.json --no-save
```

### 顯示詳細資訊

```bash
# 顯示處理過程
python3 import_local_data.py -f file.json --verbose
```

---

## 📝 準備資料格式

### JSON格式 (推薦)

```json
{
  "artworks": [
    {
      "title": "蒙娜麗莎",
      "artist": "Leonardo da Vinci",
      "date": "1503-1519",
      "period": "文藝復興",
      "description": "最著名的肖像畫之一..."
    }
  ]
}
```

### 文字格式

```
標題: 蒙娜麗莎
藝術家: Leonardo da Vinci
日期: 1503-1519
時期: 文藝復興
描述: 最著名的肖像畫之一...
```

### Markdown格式

```markdown
# 蒙娜麗莎

作者: Leonardo da Vinci
年代: 1503-1519

最著名的肖像畫之一...
```

---

## 🔍 驗證匯入成功

### 方法1: 查看命令列輸出

執行匯入後,會顯示統計資訊:
```
📊 匯入統計
====================
總檔案數:        1
成功處理:        1
處理失敗:        0
提取作品數:      2
儲存到Neo4j:     2
儲存到ChromaDB:  2
```

### 方法2: 在OpenWebUI測試

1. 打開 http://localhost:8080
2. 選擇任一RAG模型
3. 提問: "資料庫中有哪些本地匯入的作品?"

### 方法3: 查詢Neo4j

```bash
docker exec art-history-neo4j cypher-shell -u neo4j -p arthistory123 \
  "MATCH (n:Artwork) WHERE n.source CONTAINS 'local' RETURN count(n)"
```

---

## ⚠️ 注意事項

### PDF支援(選擇性)

如果需要處理PDF檔案,請安裝:

```bash
# 方法1: 系統套件
sudo apt install python3-pypdf2

# 方法2: 強制安裝(不推薦)
pip3 install --break-system-packages PyPDF2 pdfplumber
```

但如果只處理JSON和文字檔,無需安裝PDF支援。

### 資料庫連接

確保以下服務正在運行:

```bash
# 檢查Neo4j
docker ps | grep neo4j

# 檢查ChromaDB
docker ps | grep chromadb

# 如未運行,啟動服務
docker-compose up -d
```

---

## 📚 完整範例

### 範例1: 匯入一個JSON檔案

```bash
# 1. 建立測試資料
cat > my_artwork.json << 'EOF'
{
  "title": "星夜",
  "artist": "Vincent van Gogh",
  "date": "1889",
  "period": "後印象派",
  "description": "梵谷最著名的作品之一"
}
EOF

# 2. 匯入
python3 import_local_data.py -f my_artwork.json

# 3. 驗證
# 在OpenWebUI中提問: "資料庫中有星夜這幅作品嗎?"
```

### 範例2: 批次匯入多個檔案

```bash
# 1. 建立資料夾
mkdir ~/my_artworks

# 2. 放入您的JSON/TXT檔案
cp artwork1.json ~/my_artworks/
cp artwork2.txt ~/my_artworks/
cp artwork3.md ~/my_artworks/

# 3. 批次匯入
python3 import_local_data.py -d ~/my_artworks/ --recursive --verbose
```

---

## 🎯 關於Web介面

### 為什麼無法使用?

您的系統使用較新的Python版本,要求使用虛擬環境或系統套件管理器安裝Flask。

### 如何啟用Web介面?

**方法1: 使用系統套件(推薦)**
```bash
sudo apt install python3-flask
python3 web_import_server.py
```

**方法2: 使用虛擬環境**
```bash
sudo apt install python3-venv
python3 -m venv venv
source venv/bin/activate
pip install flask werkzeug
python3 web_import_server.py
```

### CLI vs Web - 該用哪個?

| 特點 | CLI | Web |
|-----|-----|-----|
| 安裝難度 | ⭐ 無需安裝 | ⭐⭐⭐ 需要Flask |
| 功能 | ⭐⭐⭐⭐⭐ 完整 | ⭐⭐⭐⭐⭐ 完整 |
| 批次處理 | ⭐⭐⭐⭐⭐ 優秀 | ⭐⭐ 一般 |
| 使用介面 | ⭐⭐⭐ 命令列 | ⭐⭐⭐⭐⭐ 拖放上傳 |
| 自動化 | ⭐⭐⭐⭐⭐ 可腳本 | ⭐ 不適合 |

**結論**: CLI功能完整且無需安裝,推薦使用!

---

## 🆘 常見問題

### Q: 沒有Flask怎麼辦?

**A**: 使用CLI就好!功能完全一樣。

### Q: 如何一次匯入多個檔案?

**A**: 把所有檔案放在一個資料夾,然後:
```bash
python3 import_local_data.py -d ./資料夾/ --recursive
```

### Q: 支援哪些檔案格式?

**A**:
- ✅ JSON (.json, .jsonl)
- ✅ 文字檔 (.txt, .md, .markdown)
- ✅ PDF (.pdf) - 需要額外套件

### Q: 匯入的資料何時可用?

**A**: **立即可用!** 匯入後在OpenWebUI中可立即查詢。

### Q: 如何查看所有命令?

**A**:
```bash
python3 import_local_data.py --help
```

---

## 📖 更多資源

- **快速參考**: `本地資料匯入_快速參考.md`
- **完整指南**: `本地資料匯入完整指南.md`
- **Web依賴安裝**: `安裝Web依賴.md`
- **系統架構**: `本地資料匯入系統架構圖.md`

---

## ✨ 總結

**您現在可以:**

1. ✅ 使用CLI匯入本地資料
2. ✅ 無需安裝任何額外依賴
3. ✅ 支援JSON、TXT、MD等格式
4. ✅ 匯入後立即在RAG系統中使用

**開始使用:**

```bash
# 建立範例
python3 import_local_data.py --create-template

# 查看範例
cat import_templates/template.json

# 匯入您的資料
python3 import_local_data.py -f 您的檔案.json
```

就是這麼簡單! 🎉
