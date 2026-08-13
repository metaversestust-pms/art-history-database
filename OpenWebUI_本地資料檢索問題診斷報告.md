# 🔍 OpenWebUI 本地資料檢索問題診斷報告

**日期**: 2025-01-30
**問題**: OpenWebUI 回答問題時無法正確使用本地匯入的資料

---

## ✅ 診斷結果

### 資料狀態確認

1. **ChromaDB** ✅
   - 狀態: 正常運行
   - 集合: `art_history_collection`
   - 文檔數: 6 個 (您匯入的所有檔案)
   - 向量維度: 768 (nomic-embed-text 模型)

2. **Neo4j** ✅
   - 狀態: 正常運行
   - 本地資料節點: 12 個 (包含測試重複匯入)
   - 資料完整性: 正常

3. **檢索測試** ✅
   - 使用正確的 Ollama 嵌入模型 (nomic-embed-text)
   - 可以成功檢索漢寶德相關資料
   - 向量搜索正常工作

---

## ❌ 問題根源

### 主要問題: **OpenWebUI 沒有連接到本地 RAG 系統**

根據診斷,發現以下問題:

1. **RAG API 服務器未運行**
   - `enhanced_rag_strategy_server.py` 應該運行在 port 8002
   - 目前 port 8002 沒有被使用
   - OpenWebUI 無法通過 RAG API 檢索資料

2. **向量模型不匹配**
   - 資料使用 `nomic-embed-text` (768 維) 存儲
   - ChromaDB 預設會使用 `all-MiniLM-L6-v2` (384 維) 查詢
   - **必須使用相同的模型** 才能正確檢索

3. **OpenWebUI 配置問題**
   - OpenWebUI 可能沒有配置使用 RAG 功能
   - 或者沒有指向正確的資料庫

---

## 💡 解決方案

提供三種解決方案,推薦按順序嘗試:

### 方案 1: 在 OpenWebUI 中使用 Documents (推薦)

**這是最簡單且直接的方法**

#### 步驟:

1. **進入 OpenWebUI** (http://localhost:8080)

2. **進入 Workspace > Documents**
   - 點擊左側菜單的 "Workspace"
   - 選擇 "Documents" 或 "Knowledge"

3. **上傳您的原始檔案**
   - 上傳您的 3 個 PDF 檔案和 3 個 TXT 檔案
   - OpenWebUI 會自動處理並建立向量索引

4. **在對話中啟用 Documents**
   - 開始新對話時
   - 點擊 "+" 按鈕選擇 Documents
   - 選擇您上傳的檔案
   - 現在提問就會使用這些文檔!

**優點**:
- ✅ 不需要額外配置
- ✅ OpenWebUI 內建功能
- ✅ 可以選擇性啟用文檔
- ✅ 立即可用

---

### 方案 2: 配置 OpenWebUI 連接到現有的 ChromaDB

#### 步驟:

1. **進入 OpenWebUI Admin 設定**
   - 打開 http://localhost:8080
   - 登入管理員帳號
   - 進入 Settings > Admin > Database

2. **配置 Vector Database**
   ```
   Vector DB Type: ChromaDB
   ChromaDB URL: http://host.docker.internal:8000
   Collection Name: art_history_collection
   ```

3. **配置 Embedding Model**
   ```
   Provider: Ollama
   Model: nomic-embed-text
   API URL: http://host.docker.internal:11434
   ```

4. **儲存並重啟 OpenWebUI**
   ```bash
   docker restart art-history-openwebui
   ```

**優點**:
- ✅ 使用現有的資料
- ✅ 不需要重新上傳
- ✅ 所有對話都會使用 RAG

**缺點**:
- ⚠️ 需要修改 OpenWebUI 設定
- ⚠️ 可能需要管理員權限

---

### 方案 3: 啟動 RAG API 服務器並配置 Pipeline

#### 步驟:

1. **啟動 RAG 服務器**
   ```bash
   cd /mnt/c/Users/ssking1999/Desktop/藝術史資料庫/art-history-database

   # 進入虛擬環境 (如果需要)
   source langchain-env/bin/activate

   # 啟動服務器
   nohup python3 enhanced_rag_strategy_server.py > rag_server.log 2>&1 &

   # 檢查是否啟動成功
   curl http://localhost:8002/health
   ```

2. **在 OpenWebUI 中安裝 Pipeline**
   - 進入 Settings > Admin > Pipelines
   - 上傳或配置 `openwebui-rag-function.py`
   - 設定 RAG API URL: `http://host.docker.internal:8002`

3. **在對話中選擇 RAG Pipeline**
   - 開始對話時選擇配置好的 RAG Pipeline
   - 提問即可使用本地資料

**優點**:
- ✅ 完整的 RAG 功能
- ✅ 支援多種 RAG 策略
- ✅ 可以自定義

**缺點**:
- ⚠️ 配置較複雜
- ⚠️ 需要維護額外的服務

---

## 🎯 快速測試 - 驗證資料可用性

在實施解決方案前,您可以直接測試資料檢索:

```bash
cd /mnt/c/Users/ssking1999/Desktop/藝術史資料庫/art-history-database
python3 test_local_data_retrieval.py
```

這個腳本會:
- 檢查 ChromaDB 中的資料
- 測試使用正確的嵌入模型檢索
- 驗證 Neo4j 中的資料

---

## 📋 測試結果摘要

根據剛才的測試:

### ChromaDB 檢索測試

**查詢**: "漢寶德是誰"
- ✅ 找到 3 個相關結果
- 最相關: "專用字" (包含漢寶德、國立臺南藝術大學等關鍵詞)

**查詢**: "南藝大"
- ✅ 找到 3 個相關結果
- 最相關: "專用字"、"漢寶德紀念館概述"

**查詢**: "漢寶德紀念館"
- ✅ 找到 3 個相關結果
- 包含: 紀念館介紹、建築設計、漢寶德生平

**結論**: 資料完整且可正確檢索!

---

## ⭐ 推薦做法

基於您的情況,我強烈推薦 **方案 1** (使用 OpenWebUI Documents):

### 實施步驟:

1. **登入 OpenWebUI** (http://localhost:8080)

2. **上傳文檔**
   - Workspace > Documents > Upload
   - 上傳這 6 個檔案:
     - 漢寶德校長生平.pdf
     - 漢寶德紀念館導覽手冊.pdf
     - 認識南藝.pdf
     - 20個測試LLM關於漢寶德的測試提問及簡短答案.txt
     - 專用字.txt
     - 通用字.txt

3. **建立新對話**
   - 點擊 "New Chat"
   - 點擊 "+" > "Documents"
   - 選擇剛才上傳的檔案
   - 開始提問!

4. **測試問題**
   ```
   漢寶德是誰?
   漢寶德出生於哪一年?
   南藝大是什麼時候成立的?
   漢寶德紀念館在哪裡?
   ```

---

## 🔧 如果方案 1 不work

那麼問題可能出在:

1. **OpenWebUI 版本太舊**
   - 更新到最新版本
   ```bash
   docker pull ghcr.io/open-webui/open-webui:main
   docker restart art-history-openwebui
   ```

2. **Ollama 嵌入模型未安裝**
   ```bash
   docker exec art-history-ollama ollama pull nomic-embed-text
   ```

3. **需要使用方案 2 或 3**
   - 參考上面的詳細步驟

---

## 📞 需要進一步協助

如果以上方案都無法解決,請提供:

1. OpenWebUI 的版本資訊
2. 上傳文檔後的截圖
3. 測試問題的回答結果
4. 錯誤日誌 (如果有)

我可以根據具體情況提供更詳細的解決方案。

---

## 📊 系統狀態總覽

```
✅ Ollama: 運行中 (port 11434)
✅ Neo4j: 運行中 (port 7687, 7474)
   - 本地資料: 12 個節點
✅ ChromaDB: 運行中 (port 8000)
   - 本地資料: 6 個文檔
✅ OpenWebUI: 運行中 (port 8080)
❌ RAG API Server: 未運行 (port 8002)
```

**結論**: 資料完整,系統正常,只需要配置 OpenWebUI 連接到資料!

---

**最後更新**: 2025-01-30
**狀態**: ✅ 問題已診斷,解決方案已提供
