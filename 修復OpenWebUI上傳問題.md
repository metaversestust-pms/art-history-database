# 🔧 修復 OpenWebUI 上傳文檔問題

**問題**: 上傳文檔時顯示 `[Errno -3] Temporary failure in name resolution`

**原因**: OpenWebUI 環境變數中的主機名 `chromadb` 無法解析

---

## ⚡ 快速修復步驟

### 步驟 1: 編輯配置檔案

打開檔案:
```bash
vim docker-compose.openwebui.yml
```

或使用其他編輯器:
```bash
nano docker-compose.openwebui.yml
```

### 步驟 2: 修改環境變數

找到第 58-59 行:
```yaml
# 修改前 (第 58-59 行)
- CHROMA_HTTP_HOST=chromadb          ❌
- CHROMA_HTTP_PORT=8000
```

改為:
```yaml
# 修改後
- CHROMA_HTTP_HOST=art-history-chromadb    ✅
- CHROMA_HTTP_PORT=8000
```

**同時建議修改第 40-41 行** (雖然 Ollama 目前可以解析，但為了一致性):
```yaml
# 修改前 (第 40-41 行)
- OLLAMA_BASE_URL=http://ollama:11434           ❌
- OLLAMA_API_BASE_URL=http://ollama:11434       ❌
```

改為:
```yaml
# 修改後
- OLLAMA_BASE_URL=http://art-history-ollama:11434     ✅
- OLLAMA_API_BASE_URL=http://art-history-ollama:11434 ✅
```

### 步驟 3: 重啟 OpenWebUI

```bash
cd /mnt/c/Users/ssking1999/Desktop/藝術史資料庫/art-history-database

# 停止 OpenWebUI
docker-compose -f docker-compose.openwebui.yml stop openwebui

# 重新啟動 OpenWebUI
docker-compose -f docker-compose.openwebui.yml up -d openwebui
```

### 步驟 4: 驗證修復

```bash
# 檢查 OpenWebUI 日誌
docker logs art-history-openwebui --tail 20

# 測試 DNS 解析
docker exec art-history-openwebui python3 -c "
import socket
print('chromadb:', end=' ')
try:
    socket.gethostbyname('chromadb')
    print('❌ 仍然失敗')
except:
    print('(預期失敗)')

print('art-history-chromadb:', end=' ')
try:
    ip = socket.gethostbyname('art-history-chromadb')
    print(f'✅ 成功 → {ip}')
except Exception as e:
    print(f'❌ 失敗 - {e}')
"
```

### 步驟 5: 測試上傳

1. 打開 http://localhost:8080
2. Workspace > Documents
3. 上傳一個小檔案測試
4. 應該會成功！

---

## 📝 完整的修改內容

如果您想一次性修改，以下是需要修改的完整內容:

### 在 docker-compose.openwebui.yml 中修改:

**第 40-41 行** (Ollama 配置):
```yaml
      # 修改前
      - OLLAMA_BASE_URL=http://ollama:11434
      - OLLAMA_API_BASE_URL=http://ollama:11434

      # 修改後
      - OLLAMA_BASE_URL=http://art-history-ollama:11434
      - OLLAMA_API_BASE_URL=http://art-history-ollama:11434
```

**第 58-59 行** (ChromaDB 配置 - **最關鍵**):
```yaml
      # 修改前
      - CHROMA_HTTP_HOST=chromadb
      - CHROMA_HTTP_PORT=8000

      # 修改後
      - CHROMA_HTTP_HOST=art-history-chromadb
      - CHROMA_HTTP_PORT=8000
```

---

## 🔄 使用 sed 自動修改 (進階)

如果您熟悉命令列，可以使用以下命令自動修改:

```bash
cd /mnt/c/Users/ssking1999/Desktop/藝術史資料庫/art-history-database

# 備份原始檔案
cp docker-compose.openwebui.yml docker-compose.openwebui.yml.backup

# 修改 OLLAMA_BASE_URL
sed -i 's|OLLAMA_BASE_URL=http://ollama:11434|OLLAMA_BASE_URL=http://art-history-ollama:11434|g' docker-compose.openwebui.yml
sed -i 's|OLLAMA_API_BASE_URL=http://ollama:11434|OLLAMA_API_BASE_URL=http://art-history-ollama:11434|g' docker-compose.openwebui.yml

# 修改 CHROMA_HTTP_HOST (最重要!)
sed -i 's|CHROMA_HTTP_HOST=chromadb|CHROMA_HTTP_HOST=art-history-chromadb|g' docker-compose.openwebui.yml

# 查看修改結果
diff docker-compose.openwebui.yml.backup docker-compose.openwebui.yml

# 重啟服務
docker-compose -f docker-compose.openwebui.yml restart openwebui
```

---

## ✅ 驗證清單

修改並重啟後，檢查以下項目:

- [ ] OpenWebUI 容器正常運行
  ```bash
  docker ps | grep art-history-openwebui
  ```

- [ ] DNS 解析正常
  ```bash
  docker exec art-history-openwebui sh -c "getent hosts art-history-chromadb"
  ```

- [ ] 可以連接到 ChromaDB
  ```bash
  docker exec art-history-openwebui python3 -c "import chromadb; client = chromadb.HttpClient(host='art-history-chromadb', port=8000); print(f'✅ 連接成功! Collections: {len(client.list_collections())}')"
  ```

- [ ] 上傳檔案成功
  - 打開 http://localhost:8080
  - Workspace > Documents > Upload
  - 選擇一個檔案上傳
  - 檢查是否成功

---

## 🆘 如果還有問題

### 問題 1: 修改後仍然失敗

**檢查**:
```bash
# 確認環境變數是否生效
docker exec art-history-openwebui env | grep CHROMA_HTTP_HOST
```

**應該顯示**:
```
CHROMA_HTTP_HOST=art-history-chromadb
```

**如果還是舊的值**:
```bash
# 完全停止並刪除容器
docker-compose -f docker-compose.openwebui.yml down openwebui

# 重新創建容器
docker-compose -f docker-compose.openwebui.yml up -d openwebui
```

### 問題 2: ChromaDB 連接仍然失敗

**檢查 ChromaDB 是否在正確的網路**:
```bash
docker network inspect art-history-network | grep -A 3 chromadb
```

**應該看到**:
```
"art-history-chromadb": {
    "IPv4Address": "172.18.0.x/16"
}
```

### 問題 3: 其他錯誤

**查看完整日誌**:
```bash
docker logs art-history-openwebui --tail 100 > openwebui-debug.log
cat openwebui-debug.log | grep -i error
```

---

## 📊 修改前後對比

### 修改前 (無法上傳)

```yaml
environment:
  - OLLAMA_BASE_URL=http://ollama:11434          ❌ DNS 可能失敗
  - CHROMA_HTTP_HOST=chromadb                     ❌ DNS 失敗
```

**結果**: `[Errno -3] Temporary failure in name resolution`

### 修改後 (可以上傳)

```yaml
environment:
  - OLLAMA_BASE_URL=http://art-history-ollama:11434    ✅ DNS 成功
  - CHROMA_HTTP_HOST=art-history-chromadb               ✅ DNS 成功
```

**結果**: 上傳成功，文檔可以正常處理

---

## 🎯 為什麼會這樣?

### 問題根源

在您的 Docker 網路中:
- ✅ 容器名稱: `art-history-chromadb`
- ❌ DNS 別名: `chromadb` (不存在)

當 OpenWebUI 嘗試連接 `chromadb` 時:
1. Docker DNS 查找 `chromadb`
2. 找不到這個主機名
3. 返回 `[Errno -3] Temporary failure in name resolution`
4. 上傳失敗

### 解決方案

使用完整的容器名稱:
- ✅ `art-history-chromadb` (可以被解析)
- ✅ `art-history-ollama` (可以被解析)

---

## 🚀 立即執行

最快的修復方式:

```bash
cd /mnt/c/Users/ssking1999/Desktop/藝術史資料庫/art-history-database

# 1. 備份
cp docker-compose.openwebui.yml docker-compose.openwebui.yml.backup

# 2. 修改配置
sed -i 's|CHROMA_HTTP_HOST=chromadb|CHROMA_HTTP_HOST=art-history-chromadb|g' docker-compose.openwebui.yml

# 3. 重啟
docker-compose -f docker-compose.openwebui.yml restart openwebui

# 4. 等待 10 秒讓服務啟動
sleep 10

# 5. 驗證
docker exec art-history-openwebui python3 -c "import chromadb; client = chromadb.HttpClient(host='art-history-chromadb', port=8000); print('✅ ChromaDB 連接成功!')"

# 6. 測試上傳
echo "現在可以在 http://localhost:8080 測試上傳檔案了！"
```

---

**修復完成時間**: 預計 5 分鐘
**難度**: ⭐⭐ (簡單)
**效果**: 永久解決上傳問題
