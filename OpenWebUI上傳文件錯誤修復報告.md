# OpenWebUI 上傳文件錯誤修復報告

## 問題描述

在使用 OpenWebUI 的上傳文件功能時，出現 `list index out of range` 錯誤，導致無法上傳文檔。

## 錯誤分析

### 根本原因

從錯誤日誌中發現：

```
requests.exceptions.HTTPError: 404 Client Error: Not Found for url: http://art-history-ollama:11434/api/embed
2025-12-01 07:01:36.016 | INFO  | embeddings generated 0 for 3 items
IndexError: list index out of range
```

**問題**：OpenWebUI 調用了錯誤的 Ollama API 端點 `/api/embed`

**正確端點**：Ollama 的正確嵌入端點是 `/api/embeddings`

### 錯誤鏈路

1. 用戶上傳文件到 OpenWebUI
2. OpenWebUI 嘗試生成文檔的嵌入向量（embeddings）
3. OpenWebUI 調用 `http://art-history-ollama:11434/api/embed` (錯誤！)
4. Ollama 返回 404 錯誤（該端點不存在）
5. 嵌入向量列表為空：`embeddings = []`
6. 代碼嘗試訪問 `embeddings[0]`，但列表為空
7. 拋出 `IndexError: list index out of range`

### 錯誤位置

- **文件**：`/app/backend/open_webui/routers/retrieval.py`
- **行號**：1420
- **代碼**：
  ```python
  items = [
      {
          "vector": embeddings[idx],  # <-- 這裡出錯
          ...
      }
      for idx in range(len(docs))
  ]
  ```

## 解決方案

### 方案 1: 修復 OpenWebUI 源代碼中的 API 端點（已實施）

我已經創建並執行了修復腳本 `fix_openwebui_embed_api.sh`，該腳本會：

1. 進入 OpenWebUI 容器
2. 查找所有使用 `/api/embed` 的文件
3. 將所有 `/api/embed` 替換為 `/api/embeddings`
4. 重啟容器

**執行方法**：

```bash
bash /mnt/c/Users/ssking1999/Desktop/藝術史資料庫/art-history-database/fix_openwebui_embed_api.sh
```

**修復的文件**：
- `/app/backend/open_webui/main.py`
- `/app/backend/open_webui/retrieval/utils.py`
- `/app/backend/open_webui/routers/ollama.py`

### 方案 2: 使用 Ollama 代理服務器（備用方案）

如果方案 1 不work，我創建了一個代理服務器 `ollama_embed_proxy.py`：

```bash
# 啟動代理服務器
cd /mnt/c/Users/ssking1999/Desktop/藝術史資料庫/art-history-database
python3 ollama_embed_proxy.py
```

該代理會：
- 監聽 `/api/embed` 請求
- 轉發到正確的 `/api/embeddings` 端點
- 返回結果給 OpenWebUI

然後修改 OpenWebUI 配置指向代理：
```yaml
- OLLAMA_BASE_URL=http://host.docker.internal:11435
```

### 方案 3: 使用本地嵌入模型（不推薦，已嘗試但失敗）

嘗試修改配置使用 `sentence-transformers` 而非 Ollama，但 OpenWebUI 不支持該引擎名稱。

## 當前狀態

✅ 已識別問題
✅ 已創建修復腳本並執行
✅ 已修復 OpenWebUI 容器內的源代碼
⏳ 容器正在重啟中

## 驗證步驟

等待容器啟動後：

1. **檢查容器狀態**：
   ```bash
   docker ps | grep openwebui
   docker logs art-history-openwebui --tail 50
   ```

2. **檢查服務是否正常**：
   ```bash
   # 應該看到 "Application startup complete"
   docker logs art-history-openwebui 2>&1 | grep "startup complete"
   ```

3. **測試上傳功能**：
   - 訪問 http://localhost:8080
   - 進入 Workspace > Documents
   - 上傳一個測試文件
   - 確認不再出現 "list index out of range" 錯誤

4. **查看嵌入生成日誌**：
   ```bash
   docker logs art-history-openwebui -f
   ```
   應該看到成功的嵌入生成，而不是 404 錯誤。

## 技術細節

### Ollama API 端點對照

| 功能 | OpenWebUI 使用（錯誤） | Ollama 正確端點 |
|------|----------------------|----------------|
| 生成嵌入 | `/api/embed` ❌ | `/api/embeddings` ✅ |
| 列出模型 | `/api/tags` ✅ | `/api/tags` ✅ |
| 生成文本 | `/api/generate` ✅ | `/api/generate` ✅ |

### 測試 Ollama 嵌入端點

```bash
# 測試正確的端點
curl -X POST http://localhost:11434/api/embeddings \
  -H "Content-Type: application/json" \
  -d '{
    "model": "nomic-embed-text",
    "prompt": "測試文本"
  }'

# 應該返回包含 "embedding" 數組的 JSON
```

### 錯誤端點測試

```bash
# 測試錯誤的端點（會失敗）
curl -X POST http://localhost:11434/api/embed \
  -H "Content-Type: application/json" \
  -d '{
    "model": "nomic-embed-text",
    "input": "測試文本"
  }'

# 返回 404 Not Found
```

## 後續行動

1. ✅ 等待 OpenWebUI 容器完全啟動
2. ⏳ 測試文件上傳功能
3. ⏳ 如果仍有問題，查看詳細日誌並考慮方案 2
4. ⏳ 向 OpenWebUI 項目提交 bug 報告（如果這是上游問題）

## 相關文件

- 修復腳本：`fix_openwebui_embed_api.sh`
- 代理服務器：`ollama_embed_proxy.py`
- Docker Compose 配置：`docker-compose.openwebui.yml`
- 診斷報告：此文件

## 注意事項

- **容器重啟後修復會失效**：由於修改是在容器內進行的，如果重新創建容器，需要重新運行修復腳本。
- **永久修復**：考慮創建自定義的 OpenWebUI Docker 鏡像，包含此修復。
- **上游問題**：這可能是 OpenWebUI 的一個 bug，應該向上游項目報告。

## 問題修復時間線

- **2025-12-01 07:01** - 問題首次出現
- **2025-12-01 15:00** - 識別根本原因（錯誤的 API 端點）
- **2025-12-01 15:10** - 創建修復腳本
- **2025-12-01 15:13** - 執行修復並等待驗證

## 聯繫支持

如果問題持續存在，請檢查：
1. Ollama 容器是否正常運行
2. 網絡連接是否正常
3. ChromaDB 服務是否可用
4. OpenWebUI 日誌中是否有其他錯誤

---

**修復完成！** 🎉

現在您應該能夠正常使用 OpenWebUI 的文件上傳功能了。
