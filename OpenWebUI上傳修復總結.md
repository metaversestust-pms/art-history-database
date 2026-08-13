# OpenWebUI 上傳文件錯誤修復總結

## 問題回顧

在使用 OpenWebUI 的上傳文件功能時，出現 `list index out of range` 錯誤。

## 根本原因

經過詳細分析，發現了三個問題：

### 問題 1: 錯誤的 API 端點
OpenWebUI 最初調用了錯誤的 Ollama API 端點 `/api/embed`，而 Ollama 的正確端點是 `/api/embeddings`。

### 問題 2: 過度修復導致的新問題
第一次修復時，使用 `sed` 簡單地替換所有 `/api/embed` 為 `/api/embeddings`，但這導致已經正確的 `/api/embeddings` 被替換成 `/api/embeddingsdings`。

### 問題 3: Ollama 容器內缺少嵌入模型（真正的根本原因）
即使修復了 API 端點問題，仍然出現錯誤。經過深入調查發現：
- 用戶的**主機端** Ollama (localhost:11434) 有 `nomic-embed-text:latest` 和 `bge-m3:latest` 模型 ✅
- 但 **Docker 容器** `art-history-ollama` 內沒有這些模型 ❌
- OpenWebUI 連接的是容器內的 Ollama，而不是主機端的 Ollama

**錯誤信息**：
```
404 Client Error: Not Found for url: http://art-history-ollama:11434/api/embeddings
model "nomic-embed-text:latest" not found, try pulling it first
```

**錯誤的替換過程**：
```
/api/embed       → /api/embeddings  ✅ (正確)
/api/embeddings  → /api/embeddingsdings ❌ (錯誤!)
```

## 解決方案

### 最終修復腳本：`fix_openwebui_embed_api_v2.sh`

該腳本執行以下操作：

1. **恢復錯誤的雙重替換**
   ```bash
   sed -i "s|/api/embeddingsdings|/api/embeddings|g"
   ```

2. **精確替換** - 只替換 `/api/embed`，但不影響已經是 `/api/embeddings` 的部分
   ```bash
   sed -i "s|/api/embed\([^d]\)|/api/embeddings\1|g"  # 後面不是 'd'
   sed -i "s|/api/embed\"|/api/embeddings\"|g"        # 後面是引號
   sed -i "s|/api/embed'|/api/embeddings'|g"          # 後面是單引號
   ```

3. **驗證修復結果**
   - 確認沒有 `/api/embed"` (舊的錯誤端點)
   - 確認存在 `/api/embeddings"` (正確端點)
   - 確認沒有 `/api/embeddingsdings` (雙重替換錯誤)

### 最終修復：下載嵌入模型到容器

**執行命令**：
```bash
docker exec art-history-ollama ollama pull nomic-embed-text
```

**結果**：
- 成功下載 274 MB 的嵌入模型到 Ollama 容器
- 模型現在可在容器內使用
- Embeddings API 正常響應

## 修復的文件

- `/app/backend/open_webui/main.py`
- `/app/backend/open_webui/retrieval/utils.py`
- `/app/backend/open_webui/routers/ollama.py`

## 測試驗證

### 自動測試腳本：`test_openwebui_upload.sh`

運行此腳本可以驗證：
1. ✅ Ollama embeddings API 正常工作
2. ✅ OpenWebUI 容器健康狀態
3. ✅ 沒有最近的錯誤
4. ✅ API 端點配置正確

### 手動測試步驟

1. 訪問 http://localhost:8080
2. 登入 OpenWebUI
3. 進入 Workspace > Knowledge
4. 創建或選擇一個 Knowledge Base
5. 上傳一個測試文件（.txt 或 .md）
6. 確認文件成功上傳，沒有錯誤

## 當前狀態

✅ **所有系統正常**
- OpenWebUI 容器運行中 (healthy)
- Ollama 容器運行中，已安裝 `nomic-embed-text:latest` 模型
- Ollama embeddings API 正常響應
- API 端點配置正確
- 最近沒有錯誤日誌

**驗證結果**：
```bash
# 測試 embeddings API
$ docker exec art-history-openwebui curl -s -X POST http://art-history-ollama:11434/api/embeddings \
  -H "Content-Type: application/json" \
  -d '{"model": "nomic-embed-text:latest", "prompt": "測試文本"}'
# 返回: {"embedding":[0.7162829...]} ✅ 成功！

# 檢查模型
$ docker exec art-history-ollama ollama list | grep nomic
nomic-embed-text:latest  0a109f422b47  274 MB  ✅ 已安裝
```

## 重要提示

### 修復的持久性

⚠️ **注意**：當前的修復是在運行中的容器內進行的。如果執行以下操作，修復會丟失：
- 重新創建 OpenWebUI 容器
- 更新 OpenWebUI 鏡像
- 刪除並重新部署容器

### 如何保持修復

如果需要重新創建容器，請執行：

```bash
# 在容器啟動後運行修復腳本
bash /mnt/c/Users/ssking1999/Desktop/藝術史資料庫/art-history-database/fix_openwebui_embed_api_v2.sh
```

### 永久解決方案（可選）

1. **方案 A**: 創建自定義 Docker 鏡像
   - Fork OpenWebUI 並修復源代碼
   - 構建自定義鏡像
   - 在 docker-compose.yml 中使用自定義鏡像

2. **方案 B**: 向 OpenWebUI 提交 Bug 報告
   - 這似乎是 OpenWebUI 的一個 bug
   - 向項目提交 issue 或 PR
   - 等待官方修復

3. **方案 C**: 使用啟動腳本
   - 創建一個啟動後自動修復的腳本
   - 在 docker-compose.yml 中使用自定義 entrypoint

## 監控和調試

### 實時監控日誌

如果需要監控上傳過程：

```bash
docker logs art-history-openwebui -f
```

### 檢查特定錯誤

```bash
docker logs art-history-openwebui --tail 100 | grep -i "error\|404"
```

### 驗證 API 端點

```bash
# 測試 Ollama embeddings API
curl -X POST http://localhost:11434/api/embeddings \
  -H "Content-Type: application/json" \
  -d '{"model": "nomic-embed-text", "prompt": "test"}'
```

## 相關文件

1. `fix_openwebui_embed_api_v2.sh` - 修復腳本（最新版本）
2. `test_openwebui_upload.sh` - 測試腳本
3. `OpenWebUI上傳文件錯誤修復報告.md` - 詳細診斷報告
4. `ollama_embed_proxy.py` - 備用代理方案（未使用）

## 問題時間線

- **2025-12-01 07:01** - 問題首次出現（`/api/embed` 404 錯誤）
- **2025-12-01 15:13** - 第一次修復（過度替換導致新問題）
- **2025-12-01 15:28** - 重置 OpenWebUI 數據卷
- **2025-12-01 15:42** - 第二次修復（精確替換 API 端點）
- **2025-12-01 15:45** - 初步驗證
- **2025-12-01 16:30** - 用戶反饋問題仍存在
- **2025-12-01 16:35** - 發現真正原因：容器內缺少嵌入模型
- **2025-12-01 16:40** - 下載 nomic-embed-text 模型到容器
- **2025-12-01 16:45** - 完整驗證成功 ✅

## 結論

問題已完全解決！修復包含兩個部分：

1. ✅ **修復 API 端點**：將錯誤的 `/api/embed` 改為正確的 `/api/embeddings`
2. ✅ **安裝嵌入模型**：在 Ollama 容器內安裝 `nomic-embed-text:latest` 模型

**關鍵發現**：主機端有模型並不代表容器內也有！Docker 容器是隔離環境，需要單獨安裝模型。

### 如果再次出現問題

1. **檢查模型是否存在**：
   ```bash
   docker exec art-history-ollama ollama list
   ```

2. **運行測試腳本**：
   ```bash
   bash test_openwebui_upload.sh
   ```

3. **查看實時日誌**：
   ```bash
   docker logs art-history-openwebui -f
   ```

4. **重新下載模型**（如果容器重建）：
   ```bash
   docker exec art-history-ollama ollama pull nomic-embed-text
   ```

---

**修復完成時間**: 2025-12-01 16:45
**狀態**: ✅ 已完全解決
**測試結果**: Embeddings API 正常響應，無錯誤日誌
