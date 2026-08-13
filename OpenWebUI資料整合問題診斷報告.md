# OpenWebUI 資料整合問題診斷報告

## 📋 問題現象

用戶反映：
- ✅ 資料已成功匯入 Neo4j
- ✅ 資料已成功匯入 ChromaDB
- ❌ 在 OpenWebUI 中詢問問題時，回答仍然錯誤

---

## 🔍 完整診斷過程

### 1. 檢查資料庫狀態

#### Neo4j
```cypher
MATCH (n:Artwork)
WHERE n.source = 'local_text_import' OR n.source = 'local_import'
RETURN count(n);
```
**結果**: ✅ 資料存在

#### ChromaDB
```python
collection = client.get_collection('art_history_collection')
print(collection.count())  # 19 個文檔
```
**結果**: ✅ 19 個文檔存在，包括漢寶德相關資料

---

### 2. 檢查 OpenWebUI 連接

#### ChromaDB 連接
```bash
docker exec art-history-openwebui python3 -c "
import chromadb
client = chromadb.HttpClient(host='art-history-chromadb', port=8000)
print(client.heartbeat())
"
```
**結果**: ✅ OpenWebUI 可以連接到 ChromaDB

#### 環境變數配置
```
VECTOR_DB=chroma
CHROMA_HTTP_HOST=art-history-chromadb
CHROMA_HTTP_PORT=8000
RAG_EMBEDDING_ENGINE=ollama
RAG_EMBEDDING_MODEL=nomic-embed-text:latest
ENABLE_RAG_LOCAL=true
RAG_TOP_K=5
```
**結果**: ✅ 配置正確

---

### 3. 檢查 OpenWebUI 內部資料庫

#### Knowledge Base
```sql
SELECT * FROM knowledge;
```
**結果**:
- ✅ 有 Knowledge Base: "國立台南藝術大學歷史"
- ID: `e4590fbc-7c59-4915-b730-0cc8a16296df`

#### Files
```sql
SELECT COUNT(*) FROM file;
```
**結果**: ✅ 37 個檔案，包括南藝大資料

#### ⚠️ **關鍵發現：Documents 表**
```sql
SELECT COUNT(*) FROM document WHERE collection_name = 'art_history_collection';
```
**結果**: ❌ **0 個文檔**！

---

## 🎯 問題根源

### OpenWebUI 的 RAG 架構

```
┌─────────────────────────────────────────────────────────┐
│                      OpenWebUI                          │
│                                                         │
│  ┌─────────────┐      ┌──────────────┐                │
│  │   webui.db  │      │   Backend    │                │
│  │             │      │              │                │
│  │ • user      │      │ • RAG 引擎   │                │
│  │ • knowledge │◄────►│ • 查詢處理   │                │
│  │ • file      │      │              │                │
│  │ • document  │      └──────┬───────┘                │
│  └─────────────┘             │                         │
└──────────────────────────────┼─────────────────────────┘
                               │
                               ▼
                        ┌──────────────┐
                        │   ChromaDB   │
                        │              │
                        │ Collections: │
                        │ • art_...    │ ◄── CLI 直接匯入
                        └──────────────┘
```

### 問題分析

1. **CLI 匯入路徑**:
   ```
   import_local_data.py → ChromaDB + Neo4j
                        ↑ (直接寫入)
   ```

2. **OpenWebUI 預期路徑**:
   ```
   Web UI 上傳 → OpenWebUI Backend → webui.db (document 表)
                                    ↓
                                  ChromaDB
   ```

3. **根本原因**:
   - CLI 工具直接將資料寫入 ChromaDB
   - 但 **OpenWebUI 不知道這些資料的存在**
   - OpenWebUI 只會查詢 `webui.db` 的 `document` 表來決定哪些文檔應該用於 RAG
   - `document` 表中沒有記錄 = OpenWebUI 不會使用這些資料

---

## 🔧 解決方案

### ❌ 方案 1: 直接操作 document 表（不可行）

嘗試直接插入記錄到 `document` 表失敗，因為：
- `document` 表有 UNIQUE 約束在 `collection_name` 上
- 每個 collection 只能有一筆記錄
- 這不符合我們的需求

### ✅ 方案 2: 通過 OpenWebUI Web 介面上傳（推薦）

**這是正確且唯一可靠的方法！**

#### 步驟：

1. **訪問 OpenWebUI**
   ```
   http://localhost:8080
   ```

2. **進入 Workspace → Knowledge**
   - 選擇或創建 Knowledge Base: "國立台南藝術大學歷史"

3. **上傳檔案**
   - 點擊 "Add File" 或 "Upload"
   - 選擇南藝大資料夾中的檔案：
     - `漢寶德校長生平.pdf`
     - `漢寶德紀念館導覽手冊.pdf`
     - `認識南藝.pdf`
     - `20個測試LLM關於漢寶德的測試提問及簡短答案.txt`
     - `專用字.txt`
     - `通用字.txt`

4. **等待處理**
   - OpenWebUI 會自動：
     - 解析文件內容
     - 生成嵌入向量
     - 儲存到 ChromaDB
     - 在 `webui.db` 中註冊

5. **驗證**
   - 檢查 Knowledge Base 中的文檔數量
   - 測試問題

---

### ✅ 方案 3: 使用 OpenWebUI API（進階）

如果有大量檔案需要批次上傳，可以使用 OpenWebUI 的 API：

```python
import requests

# OpenWebUI API
api_url = "http://localhost:8080/api/v1/files"
api_key = "sk-art-history-rag"  # 從環境變數取得

# 上傳檔案
with open('漢寶德校長生平.pdf', 'rb') as f:
    files = {'file': f}
    headers = {'Authorization': f'Bearer {api_key}'}

    response = requests.post(
        f"{api_url}/upload",
        files=files,
        headers=headers,
        data={'knowledge_id': 'e4590fbc-7c59-4915-b730-0cc8a16296df'}
    )
```

---

### ⚠️ 方案 4: 修改 OpenWebUI 設定（暫時解決）

修改 OpenWebUI 的 RAG 設定，讓它直接使用整個 ChromaDB collection：

```python
# 需要在 OpenWebUI 容器內執行
# 修改 /app/backend/open_webui/config.py 或透過環境變數

# 設定預設 collection
RAG_CHROMA_COLLECTION=art_history_collection

# 或在 Admin Settings 中設定
```

但這個方法**不推薦**，因為繞過了 OpenWebUI 的權限和組織系統。

---

## 📊 當前狀態總結

| 組件 | 狀態 | 說明 |
|-----|------|------|
| **Neo4j** | ✅ 正常 | 資料已匯入，可查詢 |
| **ChromaDB** | ✅ 正常 | 19 個文檔，可檢索 |
| **OpenWebUI → ChromaDB** | ✅ 連接正常 | 可以連接和通信 |
| **OpenWebUI → webui.db** | ❌ **缺少關聯** | document 表為空 |
| **RAG 檢索** | ❌ **無法運作** | OpenWebUI 不知道要使用哪些文檔 |

---

## 🎯 推薦行動步驟

### 立即可行（手動上傳）

```bash
# 1. 訪問 OpenWebUI
瀏覽器打開: http://localhost:8080

# 2. 登入並進入 Workspace → Knowledge

# 3. 上傳南藝大資料夾中的所有檔案

# 4. 測試問題：
#    - 漢寶德出生於哪一年？
#    - 南藝大的創校校長是誰？
```

### 驗證上傳成功

```bash
# 檢查 OpenWebUI 資料庫
docker exec art-history-openwebui python3 -c "
import sqlite3
conn = sqlite3.connect('/app/backend/data/webui.db')
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM document')
print(f'Documents: {cursor.fetchone()[0]}')
conn.close()
"
```

應該看到文檔數量 > 0。

---

## 💡 關於「重新訓練」的說明

### ❌ **不需要重新訓練！**

你提到的「是否需要用 GPU 重新訓練」是個誤解。RAG 系統**不需要訓練**，它是：

1. **檢索增強生成 (Retrieval-Augmented Generation)**
   - 不是訓練模型
   - 是在推理時動態檢索相關文檔

2. **工作流程**:
   ```
   用戶問題
   → 生成查詢嵌入 (使用 nomic-embed-text)
   → 在 ChromaDB 中檢索相似文檔
   → 將相關文檔加入 LLM 的 context
   → LLM 根據文檔內容回答
   ```

3. **為什麼不需要訓練**:
   - 嵌入模型 (nomic-embed-text) 已經預訓練好
   - LLM (你使用的模型) 也已經預訓練好
   - RAG 只是將檢索到的文檔作為上下文傳給 LLM
   - **沒有任何模型參數需要更新**

4. **新增資料只需要**:
   - 生成新文檔的嵌入向量（使用現有模型）
   - 儲存到向量資料庫
   - 即時可用，無需訓練

---

## 🔍 為什麼 CLI 匯入不能直接被 OpenWebUI 使用？

### OpenWebUI 的資料管理方式

OpenWebUI 使用**三層資料結構**：

1. **File 層** (file 表)
   - 儲存檔案 metadata
   - 檔案名稱、大小、類型等

2. **Document 層** (document 表)
   - **關聯** File 和 Knowledge Base
   - **追蹤** 哪些文檔屬於哪個 collection
   - **權限控制** 誰可以訪問哪些文檔

3. **Storage 層** (ChromaDB)
   - 實際的向量和內容儲存
   - 嵌入向量
   - 文檔文本

### CLI 匯入繞過了前兩層

```
CLI 匯入:
  ✅ ChromaDB (Storage 層)
  ❌ document 表 (Document 層) - 缺少！
  ❌ file 表 (File 層) - 不完整

OpenWebUI 預期:
  file 表 → document 表 → ChromaDB
    ↓          ↓              ↓
  有記錄    有關聯        有資料
```

---

## 📝 結論

### 問題本質

**OpenWebUI 無法回答問題的原因不是資料庫或訓練問題，而是資料沒有通過 OpenWebUI 正確註冊！**

### 解決方案

**必須通過 OpenWebUI Web 介面上傳檔案**，這樣才能：
1. ✅ 建立完整的資料追蹤
2. ✅ 正確關聯到 Knowledge Base
3. ✅ 啟用 RAG 檢索
4. ✅ 正確回答問題

### 後續優化

上傳完成後，如果仍有問題，可能需要調整：
- RAG_TOP_K (檢索的文檔數量)
- 查詢提示詞模板
- 嵌入模型的選擇

但首先**必須**確保資料正確上傳到 OpenWebUI！

---

**診斷完成時間**: 2025-12-02 18:00
**問題類型**: 資料整合架構問題
**解決方案**: 通過 OpenWebUI Web 介面重新上傳檔案
**是否需要重新訓練**: ❌ 不需要
