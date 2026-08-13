# 🚀 RL-Agentic RAG 快速開始指南

## 📋 目錄
1. [安裝依賴](#安裝依賴)
2. [準備數據](#準備數據)
3. [訓練模型](#訓練模型)
4. [測試模型](#測試模型)
5. [部署集成](#部署集成)
6. [監控與調優](#監控與調優)

---

## 🔧 安裝依賴

### 1. 安裝 RL 相關包

```bash
cd /mnt/c/Users/ssking1999/Desktop/藝術史資料庫/art-history-database

# 安裝依賴
pip install -r requirements-rl.txt

# 如果使用 GPU (CUDA 11.8)
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

### 2. 驗證安裝

```bash
python -c "import torch; print(f'PyTorch: {torch.__version__}'); print(f'CUDA available: {torch.cuda.is_available()}')"
python -c "import stable_baselines3; print(f'SB3: {stable_baselines3.__version__}')"
```

---

## 📊 準備數據

### 1. 收集查詢日誌

從現有系統導出查詢歷史：

```bash
# 創建數據目錄
mkdir -p data/rl_training

# 從日誌提取查詢（如果有）
# 或使用模擬數據（訓練腳本會自動生成）
```

### 2. 數據格式

`data/training_queries.json`:

```json
[
  {
    "query": "介紹文藝復興時期的藝術特色",
    "context": {
      "user_expertise": 0.5,
      "time_of_day": 14,
      "device_type": 0
    },
    "expected_strategy": "advanced_rag",
    "user_feedback": 0.8
  },
  {
    "query": "達文西和米開朗基羅的比較",
    "context": {
      "user_expertise": 0.7
    },
    "expected_strategy": "graph_rag",
    "user_feedback": 0.9
  }
]
```

---

## 🏃 訓練模型

### 方法 1: 使用訓練腳本（推薦）

```bash
cd src/agents/rl

# 基礎訓練（使用默認配置）
python train_rl_agent.py

# 自定義配置
python train_rl_agent.py \
  --data ../../../data/rl_training/queries.json \
  --episodes 200 \
  --steps 100 \
  --save-dir ../../../models/rl \
  --log-dir ../../../runs/rl_training
```

### 方法 2: 交互式訓練

```python
import asyncio
from rl_agentic_rag import RLAgenticRAG
from train_rl_agent import RLTrainer

# 初始化
agent = RLAgenticRAG()
trainer = RLTrainer(
    agent=agent,
    training_data_path='data/training_queries.json'
)

# 訓練
asyncio.run(trainer.train(
    num_episodes=100,
    max_steps_per_episode=50
))
```

### 訓練輸出示例

```
🚀 開始訓練 RL Agent
📊 訓練配置:
  - Episodes: 100
  - Steps per Episode: 50

============================================================
📊 Episode 1/100
  平均獎勵: 0.6543
  平均損失: 0.003421
  Epsilon: 0.9950
  耗時: 12.34s
  訓練步數: 50

🧪 評估模型 (Episode 5)
  評估平均獎勵: 0.6821

💾 檢查點已保存: models/rl/rl_agent_episode_10.pt

============================================================
🎉 訓練完成！
📄 訓練報告已生成: models/rl/training_report.json
```

---

## 🧪 測試模型

### 1. 單獨測試

```bash
cd src/agents/rl
python rl_agentic_rag.py
```

### 2. 評估腳本

創建 `evaluate_rl_agent.py`:

```python
import asyncio
from rl_agentic_rag import RLAgenticRAG

async def evaluate():
    # 載入訓練好的模型
    agent = RLAgenticRAG()
    agent.load('models/rl/rl_agent_final.pt')
    agent.is_training = False  # 評估模式

    # 測試查詢
    test_queries = [
        "介紹文藝復興時期的藝術特色",
        "達文西和米開朗基羅的比較",
        "什麼是印象派藝術？",
    ]

    results = []
    for query in test_queries:
        result = await agent.query(query, context={})
        print(f"\n查詢: {query}")
        print(f"選擇策略: {result['strategy']}")
        print(f"獎勵: {result['reward']:.4f}")
        results.append(result)

    return results

asyncio.run(evaluate())
```

---

## 🔌 部署集成

### 1. 修改現有 RAG 系統

在 `enhanced_openwebui_rag_function_v6_with_graph_viz.py` 中集成：

```python
# 在文件開頭添加
from src.agents.rl.rl_agentic_rag import RLAgenticRAG

class Tools:
    def __init__(self):
        # ... 現有代碼 ...

        # 初始化 RL Agent
        self.rl_agent = RLAgenticRAG()
        self.rl_agent.load('models/rl/rl_agent_final.pt')
        self.rl_agent.is_training = False  # 推理模式

        # A/B 測試配置
        self.use_rl = True
        self.rl_ratio = 0.5  # 50% 流量使用 RL

    async def query_with_rl(self, query: str, context: Dict):
        """使用 RL Agent 選擇策略"""

        # A/B 測試
        import random
        if not self.use_rl or random.random() > self.rl_ratio:
            # 使用原始邏輯
            return await self.original_query(query, context)

        # 使用 RL Agent
        rl_result = await self.rl_agent.query(query, context)
        strategy = rl_result['strategy']

        # 執行選定的策略
        return await self.execute_strategy(strategy, query, context)
```

### 2. 創建 RL 服務器

創建 `src/agents/rl/rl_server.py`:

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from rl_agentic_rag import RLAgenticRAG
import uvicorn

app = FastAPI(title="RL-Agentic RAG Server")

# 初始化 Agent
agent = RLAgenticRAG()
agent.load('models/rl/rl_agent_final.pt')
agent.is_training = False

class QueryRequest(BaseModel):
    query: str
    context: dict = {}

class QueryResponse(BaseModel):
    query: str
    strategy: str
    action: int
    reward: float
    processing_time: float

@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """處理查詢請求"""
    try:
        result = await agent.query(request.query, request.context)
        return QueryResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats")
async def get_stats():
    """獲取統計信息"""
    return agent.get_stats()

@app.get("/health")
async def health():
    """健康檢查"""
    return {"status": "healthy", "model_loaded": True}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8011)
```

運行服務器：

```bash
cd src/agents/rl
python rl_server.py
```

### 3. Docker 部署

創建 `Dockerfile.rl-agent`:

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# 安裝依賴
COPY requirements-rl.txt .
RUN pip install --no-cache-dir -r requirements-rl.txt

# 複製代碼
COPY src/agents/rl/ ./agents/rl/
COPY models/ ./models/

# 環境變量
ENV RL_MODEL_PATH=/app/models/rl/rl_agent_final.pt
ENV PYTHONPATH=/app

# 啟動服務
CMD ["python", "agents/rl/rl_server.py"]
```

添加到 `docker-compose.yml`:

```yaml
services:
  rl-agent:
    build:
      context: .
      dockerfile: Dockerfile.rl-agent
    ports:
      - "8011:8011"
    volumes:
      - ./models:/app/models
      - ./logs:/app/logs
    environment:
      - RL_MODEL_PATH=/app/models/rl/rl_agent_final.pt
    networks:
      - art-history-network
```

啟動：

```bash
docker-compose up -d rl-agent
```

---

## 📈 監控與調優

### 1. TensorBoard 監控

```bash
# 啟動 TensorBoard
tensorboard --logdir=runs/rl_training --port=6006

# 訪問
# http://localhost:6006
```

查看指標：
- `Reward/episode`: 每回合平均獎勵
- `Loss/episode`: 訓練損失
- `Epsilon/episode`: 探索率變化
- `ActionCount/*`: 各策略使用頻率

### 2. 性能對比

創建 `compare_performance.py`:

```python
import asyncio
import time
from rl_agentic_rag import RLAgenticRAG

async def compare():
    """對比 RL Agent 和原始 Agentic RAG"""

    # 載入 RL Agent
    rl_agent = RLAgenticRAG()
    rl_agent.load('models/rl/rl_agent_final.pt')
    rl_agent.is_training = False

    # 測試查詢
    test_queries = [...]  # 你的測試查詢

    rl_results = []
    original_results = []

    for query in test_queries:
        # RL Agent
        start = time.time()
        rl_result = await rl_agent.query(query, {})
        rl_time = time.time() - start

        # 原始 Agentic RAG
        start = time.time()
        original_result = await original_agentic_query(query)
        original_time = time.time() - start

        rl_results.append({
            'query': query,
            'strategy': rl_result['strategy'],
            'reward': rl_result['reward'],
            'time': rl_time
        })

        original_results.append({
            'query': query,
            'strategy': original_result['strategy'],
            'reward': original_result['reward'],
            'time': original_time
        })

    # 統計分析
    print("RL Agent vs Original Agentic RAG")
    print("=" * 60)
    print(f"RL 平均獎勵: {sum(r['reward'] for r in rl_results) / len(rl_results):.4f}")
    print(f"原始平均獎勵: {sum(r['reward'] for r in original_results) / len(original_results):.4f}")
    print(f"RL 平均時間: {sum(r['time'] for r in rl_results) / len(rl_results):.4f}s")
    print(f"原始平均時間: {sum(r['time'] for r in original_results) / len(original_results):.4f}s")

asyncio.run(compare())
```

### 3. 超參數調優

修改 `src/agents/rl/rl_config.yaml`:

```yaml
# 調整學習率
learning:
  learning_rate: 0.0001  # 試試 0.001, 0.00001

# 調整探索策略
exploration:
  epsilon_decay: 0.995   # 試試 0.99, 0.999

# 調整網絡架構
network:
  hidden_dims: [512, 256, 128]  # 試試 [256, 128], [1024, 512, 256]
```

### 4. 在線學習（持續訓練）

```python
# 在生產環境中啟用在線學習
agent = RLAgenticRAG()
agent.load('models/rl/rl_agent_final.pt')
agent.is_training = True  # 啟用訓練模式
agent.epsilon = 0.1  # 降低探索率

# 定期保存模型
async def periodic_save():
    while True:
        await asyncio.sleep(3600)  # 每小時
        agent.save('models/rl/rl_agent_online.pt')
```

---

## 🔍 故障排除

### 問題 1: 訓練損失不下降

**解決方案**:
- 降低學習率：`learning_rate: 0.00001`
- 增加預熱步數：`warmup_steps: 2000`
- 檢查獎勵函數設計

### 問題 2: Agent 總是選擇同一策略

**解決方案**:
- 增加探索率：`epsilon_end: 0.1`
- 調整獎勵多樣性權重：`diversity: 0.2`
- 使用優先級經驗回放

### 問題 3: GPU 內存不足

**解決方案**:
- 減小批次大小：`batch_size: 32`
- 減小網絡規模：`hidden_dims: [256, 128]`
- 使用梯度累積

### 問題 4: 訓練速度慢

**解決方案**:
- 使用 GPU 訓練
- 減少 episode 步數
- 並行執行查詢（批處理）

---

## 📚 進階主題

### 1. 多智能體強化學習

將不同的 RAG 策略視為協作智能體

### 2. 元學習 (Meta-Learning)

讓 Agent 學習如何快速適應新領域

### 3. 離線強化學習

使用歷史數據進行訓練，無需在線交互

### 4. 分布式訓練

使用 Ray RLlib 進行大規模分布式訓練

---

## ✅ 檢查清單

- [ ] 安裝所有依賴包
- [ ] 準備訓練數據
- [ ] 配置 `rl_config.yaml`
- [ ] 運行基礎訓練
- [ ] 驗證 TensorBoard 監控
- [ ] 評估模型性能
- [ ] 對比原系統性能
- [ ] 部署 RL 服務器
- [ ] 集成到 OpenWebUI
- [ ] 啟動 A/B 測試
- [ ] 監控生產性能
- [ ] 持續優化改進

---

## 📞 支援

如有問題，請參考：
- 完整方案：`RL_AGENTIC_RAG_實施方案.md`
- 代碼實現：`src/agents/rl/rl_agentic_rag.py`
- 訓練腳本：`src/agents/rl/train_rl_agent.py`

---

**最後更新**: 2026-01-11
**版本**: v1.0
**狀態**: ✅ 可用
