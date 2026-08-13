# 🐳 RL-Agentic RAG Docker 部署指南

## 📦 系統組成

### Docker 服務配置
- **服務名稱**: `rl-agent`
- **容器名稱**: `art-database-rl-agent`
- **端口**: `8011:8011`
- **網絡**: `art-network`

### 核心文件
```
art-history-database/
├── Dockerfile.rl-agent        # RL Agent Docker 鏡像定義
├── docker-compose.yml          # Docker Compose 配置（已集成 RL Agent）
├── src/agents/rl/
│   ├── rl_server.py           # FastAPI 服務器
│   ├── rl_simple_test.py      # 簡化版 RL Agent（NumPy）
│   ├── rl_agentic_rag.py      # 完整版 RL Agent（PyTorch）
│   └── rl_config.yaml         # RL 配置文件
└── .dockerignore              # Docker 忽略文件
```

## 🚀 快速開始

### 1. 構建 Docker 鏡像

```bash
# 切換到項目目錄
cd /mnt/c/Users/ssking1999/Desktop/藝術史資料庫/art-history-database

# 構建 RL Agent 鏡像
docker build -f Dockerfile.rl-agent -t art-database-rl-agent:latest .
```

### 2. 啟動服務

#### 方式 A: 單獨啟動 RL Agent
```bash
docker-compose up rl-agent
```

#### 方式 B: 啟動所有服務
```bash
docker-compose up -d
```

#### 方式 C: 僅啟動 RL Agent（後台運行）
```bash
docker-compose up -d rl-agent
```

### 3. 驗證服務

```bash
# 檢查容器狀態
docker ps | grep rl-agent

# 查看日誌
docker-compose logs -f rl-agent

# 測試健康檢查
curl http://localhost:8011/health
```

**預期輸出**:
```json
{
  "status": "healthy",
  "model_loaded": true,
  "model_version": "simplified",
  "training_mode": false
}
```

## 🔧 API 端點

### 1. 健康檢查
```bash
GET http://localhost:8011/health
```

### 2. 執行查詢
```bash
POST http://localhost:8011/query
Content-Type: application/json

{
  "query": "介紹文藝復興時期的藝術特色",
  "context": {
    "user_expertise": 0.5,
    "time_of_day": 14,
    "device_type": 0
  },
  "training": false
}
```

**響應示例**:
```json
{
  "query": "介紹文藝復興時期的藝術特色",
  "strategy": "advanced_rag",
  "action": 3,
  "confidence": 0.8543,
  "reward": 0.8123,
  "processing_time": 0.142,
  "epsilon": 0.0,
  "model_version": "simplified"
}
```

### 3. 獲取統計信息
```bash
GET http://localhost:8011/stats
```

**響應示例**:
```json
{
  "total_queries": 150,
  "training_steps": 0,
  "epsilon": 0.0,
  "average_reward": 0.8654,
  "action_distribution": {
    "vector_rag": 35,
    "graph_rag": 28,
    "hybrid_rag": 22,
    "advanced_rag": 18,
    "agentic_rag": 12,
    "self_rag": 10,
    "adaptive_rag": 8,
    "multimodal_rag": 5,
    "dynamic_weight_0.3": 6,
    "dynamic_weight_0.7": 6
  },
  "model_version": "simplified",
  "training_mode": false
}
```

### 4. 提交用戶反饋
```bash
POST http://localhost:8011/feedback
Content-Type: application/json

{
  "query": "介紹文藝復興時期的藝術特色",
  "strategy": "advanced_rag",
  "user_satisfaction": 0.9,
  "actual_processing_time": 2.5
}
```

### 5. 保存模型（僅完整版）
```bash
POST http://localhost:8011/save_model
```

## 🔄 集成到現有系統

### 方式 1: HTTP API 調用

在您的 RAG Function 中調用 RL Agent API：

```python
import httpx

async def get_strategy_from_rl(query: str, context: dict):
    """從 RL Agent 獲取推薦策略"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://rl-agent:8011/query",
            json={
                "query": query,
                "context": context,
                "training": False
            },
            timeout=5.0
        )
        result = response.json()
        return result['strategy']

# 使用示例
async def enhanced_query(query: str):
    # 獲取 RL 推薦的策略
    strategy = await get_strategy_from_rl(query, {
        "user_expertise": 0.5,
        "time_of_day": 14
    })

    # 根據推薦策略執行查詢
    if strategy == "vector_rag":
        result = await vector_rag_query(query)
    elif strategy == "graph_rag":
        result = await graph_rag_query(query)
    # ... 其他策略

    return result
```

### 方式 2: Docker 網絡內部通信

在 `docker-compose.yml` 中，RL Agent 已經加入 `art-network`，可以直接通過服務名稱訪問：

```python
# RL Agent URL 在 Docker 網絡內
RL_AGENT_URL = "http://rl-agent:8011"

# 在容器內調用
response = requests.post(
    f"{RL_AGENT_URL}/query",
    json={"query": query, "context": context}
)
```

## 🎯 環境變量配置

在 `docker-compose.yml` 中可以配置以下環境變量：

```yaml
environment:
  # 模型路徑
  - RL_MODEL_PATH=/app/models/rl/rl_agent_final.pt

  # 配置文件路徑
  - RL_CONFIG_PATH=/app/agents/rl/rl_config.yaml

  # 訓練模式（false=推理模式，true=訓練模式）
  - RL_TRAINING_MODE=false

  # 服務器配置
  - RL_SERVER_HOST=0.0.0.0
  - RL_SERVER_PORT=8011
  - RL_SERVER_WORKERS=1
```

## 📊 監控與日誌

### 查看實時日誌
```bash
# 實時查看日誌
docker-compose logs -f rl-agent

# 查看最近100行日誌
docker-compose logs --tail=100 rl-agent
```

### 進入容器調試
```bash
# 進入容器
docker exec -it art-database-rl-agent /bin/bash

# 檢查 Python 環境
python --version
pip list | grep torch

# 測試 RL Agent
python agents/rl/rl_simple_test.py
```

### 檢查資源使用
```bash
# 查看容器資源使用
docker stats art-database-rl-agent
```

## 🔧 故障排除

### 問題 1: 容器無法啟動

**檢查**:
```bash
docker-compose logs rl-agent
```

**可能原因**:
- 端口 8011 被占用
- 依賴文件缺失
- Python 包安裝失敗

**解決方案**:
```bash
# 檢查端口
sudo lsof -i :8011

# 重新構建
docker-compose build --no-cache rl-agent

# 重新啟動
docker-compose up -d rl-agent
```

### 問題 2: API 響應 503 Service Unavailable

**原因**: Agent 未成功初始化

**檢查**:
```bash
docker-compose logs rl-agent | grep "初始化"
```

**解決方案**:
- 確認代碼文件正確複製到容器
- 檢查 Python 導入錯誤

### 問題 3: 健康檢查失敗

**檢查**:
```bash
docker exec art-database-rl-agent curl -f http://localhost:8011/health
```

**解決方案**:
```bash
# 重啟容器
docker-compose restart rl-agent
```

## 🎮 高級配置

### 啟用訓練模式

修改 `docker-compose.yml`:
```yaml
environment:
  - RL_TRAINING_MODE=true  # 啟用訓練
  - RL_MODEL_PATH=/app/models/rl/rl_agent_online.pt
```

重啟服務:
```bash
docker-compose restart rl-agent
```

### 使用完整版本（PyTorch）

確保 `requirements-rl.txt` 包含完整依賴，並且確認 `rl_server.py` 可以導入 `rl_agentic_rag`模組。

### 掛載自定義模型

```yaml
volumes:
  - ./my_models:/app/models
```

然後設置:
```yaml
environment:
  - RL_MODEL_PATH=/app/models/my_custom_model.pt
```

## 📈 性能優化

### 增加 Worker 數量
```yaml
environment:
  - RL_SERVER_WORKERS=4  # 增加到 4 個 worker
```

### GPU 支持

修改 `Dockerfile.rl-agent`:
```dockerfile
# 取消註解 GPU 安裝
RUN pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

修改 `docker-compose.yml`:
```yaml
rl-agent:
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: 1
            capabilities: [gpu]
```

## 📝 API 文檔

啟動服務後，訪問自動生成的 API 文檔：

- **Swagger UI**: http://localhost:8011/docs
- **ReDoc**: http://localhost:8011/redoc

## 🎯 測試示例

### cURL 測試
```bash
# 健康檢查
curl http://localhost:8011/health

# 執行查詢
curl -X POST http://localhost:8011/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "介紹文藝復興時期的藝術特色",
    "context": {"user_expertise": 0.5}
  }'

# 獲取統計
curl http://localhost:8011/stats
```

### Python 測試
```python
import requests

# 查詢
response = requests.post(
    "http://localhost:8011/query",
    json={
        "query": "達文西和米開朗基羅的比較",
        "context": {"user_expertise": 0.7}
    }
)

result = response.json()
print(f"推薦策略: {result['strategy']}")
print(f"獎勵分數: {result['reward']:.4f}")
print(f"處理時間: {result['processing_time']:.2f}s")
```

## 🔄 更新與維護

### 更新代碼
```bash
# 停止服務
docker-compose stop rl-agent

# 重新構建
docker-compose build rl-agent

# 啟動服務
docker-compose up -d rl-agent
```

### 備份模型
```bash
# 從容器複製模型
docker cp art-database-rl-agent:/app/models/rl/rl_agent_final.pt ./backup/

# 恢復模型
docker cp ./backup/rl_agent_final.pt art-database-rl-agent:/app/models/rl/
```

## 📞 支援資源

- **完整實施方案**: `RL_AGENTIC_RAG_實施方案.md`
- **快速開始**: `RL_QUICK_START.md`
- **總結文檔**: `RL_AGENTIC_RAG_總結.md`
- **代碼實現**: `src/agents/rl/rl_agentic_rag.py`

---

**版本**: v1.0
**最後更新**: 2026-01-11
**狀態**: ✅ 可用
