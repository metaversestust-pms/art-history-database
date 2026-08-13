# ⚡ OpenWebUI 快速修復指南

**問題**: OpenWebUI 無法使用本地匯入的資料回答問題

**原因**: OpenWebUI 無法連接到 ChromaDB (DNS 解析失敗)

---

## 🎯 立即解決 (5 分鐘)

### 步驟 1: 打開 OpenWebUI

訪問: http://localhost:8080

### 步驟 2: 進入 Documents

左側菜單 > **Workspace** > **Documents**

### 步驟 3: 上傳檔案

點擊 **Upload Document** 按鈕，上傳以下檔案:

```
📁 南藝大及漢寶德校長資料整理/
  ├── 漢寶德校長生平.pdf
  ├── 漢寶德紀念館導覽手冊.pdf
  ├── 認識南藝.pdf
  ├── 20個測試LLM關於漢寶德的測試提問及簡短答案.txt
  ├── 專用字.txt
  └── 通用字.txt
```

### 步驟 4: 使用文檔

1. 點擊 **New Chat** 開始新對話
2. 點擊 **"+"** 按鈕
3. 選擇 **Documents**
4. 勾選您上傳的檔案
5. 開始提問!

### 測試問題

```
漢寶德是誰?
漢寶德出生於哪一年?
南藝大是什麼時候成立的?
漢寶德紀念館的建築特色是什麼?
```

---

## 🔧 永久解決 (15 分鐘)

### 選項 A: 找到並修改 docker-compose.yml

1. 找到配置檔案:
   ```bash
   # 可能在以下位置
   ls docker-compose.yml
   ls openwebui/docker-compose.yml
   ```

2. 修改 OpenWebUI 的環境變數:
   ```yaml
   environment:
     CHROMA_HTTP_HOST: art-history-chromadb  # 改這裡!
     CHROMA_HTTP_PORT: 8000
     OLLAMA_BASE_URL: http://art-history-ollama:11434  # 建議也改
   ```

3. 重啟:
   ```bash
   docker-compose restart art-history-openwebui
   ```

### 選項 B: 使用 docker stop/start

1. 停止容器:
   ```bash
   docker stop art-history-openwebui
   ```

2. 找到原始啟動命令並修改環境變數

3. 使用新配置啟動

---

## 📊 驗證修復

執行測試腳本:

```bash
cd /mnt/c/Users/ssking1999/Desktop/藝術史資料庫/art-history-database
python3 test_openwebui_connections.py
```

應該看到: **通過測試: 6/6** ✅

---

## 🆘 如果還有問題

查看完整診斷報告:
- `OpenWebUI資料庫連接診斷與修復.md`
- `系統連接狀態報告.md`

或執行:
```bash
bash fix_openwebui_connection.sh
```

---

## ✅ 確認清單

- [ ] 已上傳所有 6 個檔案到 OpenWebUI Documents
- [ ] 在對話中啟用了這些文檔
- [ ] 測試問題得到正確答案
- [ ] (選擇性) 修改了環境變數永久解決

---

**最快路徑**: 使用 Documents 功能 (步驟 1-4) 立即可用! 🚀
