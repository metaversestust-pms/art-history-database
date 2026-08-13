# 在 OpenWebUI 中添加 42 種 RAG+LLM 組合

## 方法 1：通過 OpenWebUI 管理界面添加（推薦）

1. **打開 OpenWebUI**
   - 瀏覽器訪問：http://localhost:8080

2. **進入設置**
   - 點擊左下角的 ⚙️ 設置圖標
   - 或點擊右上角的用戶頭像 → Settings

3. **添加外部 API 連接**
   - 找到 "Connections" 或"外部連接"選項卡
   - 點擊 "Add Connection" 或 "添加連接"

4. **填寫連接信息**
   ```
   Name: Art History RAG Manager
   API Type: OpenAI Compatible
   API Base URL: http://art-history-openwebui-integration:8009/v1
   API Key: sk-art-history-rag
   ```

5. **保存並刷新**
   - 點擊 Save 保存
   - 返回主界面
   - 點擊左上角的模型選擇下拉菜單

6. **驗證**
   - 您應該能看到 42 個新模型，每個模型名稱格式為：
     - 🦙 Llama 3.1 8B + 🔍 向量RAG
     - 🦙 Llama 3.1 8B + 🕸️ 圖譜RAG
     - 等等...

## 方法 2：使用命令行腳本添加

如果 OpenWebUI 界面中沒有"Connections"選項，使用以下腳本：

```bash
# 測試整合服務
curl http://localhost:8009/v1/models

# 如果返回 42 個模型列表，說明整合服務正常
```

然後在 OpenWebUI 中：
1. 進入 Settings → Admin Settings
2. 找到 "OpenAI API" 或 "External API" 設置
3. 啟用並添加 API 端點

## 方法 3：直接訪問整合服務（測試用）

您也可以直接通過 API 測試 RAG 查詢：

```bash
curl -X POST http://localhost:8009/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.1:8b@hybrid_balanced",
    "messages": [
      {"role": "user", "content": "Tell me about Renaissance art"}
    ]
  }'
```

## 42 種可用組合

### 7 個 LLM 模型
1. 🦙 Llama 3.1 8B
2. 🦙 Llama 3.1 70B
3. 🎯 Qwen 2.5 7B
4. 🎯 Qwen 2.5 14B
5. 🔬 Gemma 2 9B
6. 🔬 Gemma 2 27B
7. 🎭 Mistral 7B

### 6 種 RAG 策略
1. 🔍 Vector Only - 純向量語義檢索
2. 🕸️ Graph Only - 知識圖譜檢索
3. ⚖️ Hybrid Balanced - 混合平衡檢索
4. 🚀 Advanced RAG - 多級檢索+重排序
5. 🤖 Agentic RAG - 智能代理推理
6. 🔄 Self RAG - 自我反思迭代

### 組合示例
- `llama3.1:8b@vector_only`
- `llama3.1:8b@graph_only`
- `llama3.1:8b@hybrid_balanced`
- `qwen2.5:7b@advanced_rag`
- `gemma2:9b@agentic_rag`
- ...等 42 種組合

## 故障排除

### 如果看不到模型
1. 檢查整合服務是否運行：
   ```bash
   docker ps | grep integration
   docker logs art-history-openwebui-integration --tail 20
   ```

2. 測試整合服務 API：
   ```bash
   curl http://localhost:8009/v1/models | jq '.data | length'
   # 應該返回 42
   ```

3. 檢查 OpenWebUI 日誌：
   ```bash
   docker logs art-history-openwebui --tail 50
   ```

### 如果連接失敗
- 確認所有容器在同一網絡：
  ```bash
  docker network inspect art-history-network
  ```

- 使用容器內網絡地址而不是 localhost：
  - ✅ 正確：`http://art-history-openwebui-integration:8009/v1`
  - ❌ 錯誤：`http://localhost:8009/v1`

## 比較實驗建議

### 相同 LLM，不同 RAG 策略
```
llama3.1:8b@vector_only
llama3.1:8b@graph_only
llama3.1:8b@hybrid_balanced
```
比較不同檢索策略對回答質量的影響

### 相同 RAG，不同 LLM
```
llama3.1:8b@hybrid_balanced
qwen2.5:7b@hybrid_balanced
gemma2:9b@hybrid_balanced
```
比較不同模型的生成能力

### 高級策略對比
```
llama3.1:8b@advanced_rag     # 多級檢索
llama3.1:8b@agentic_rag      # 智能代理
llama3.1:8b@self_rag         # 自我反思
```
比較複雜 RAG 策略的效果
