# 🤖 RL-based Agentic RAG 系統實施方案

## 📋 目錄
1. [系統概述](#系統概述)
2. [技術架構](#技術架構)
3. [實施階段](#實施階段)
4. [核心組件設計](#核心組件設計)
5. [程式碼實現](#程式碼實現)
6. [訓練流程](#訓練流程)
7. [部署與監控](#部署與監控)
8. [評估指標](#評估指標)

---

## 🎯 系統概述

### 目標
在現有藝術史資料庫系統中添加一個**基於強化學習的智能代理 RAG (RL-Agentic RAG)**，使系統能夠：
- 自動學習最優檢索策略
- 根據用戶反饋持續改進
- 動態調整多模態檢索權重
- 個性化查詢優化

### 核心特性
✅ **Deep Q-Network (DQN)** - 策略學習
✅ **Experience Replay** - 經驗回放
✅ **Multi-Armed Bandit** - 探索-利用平衡
✅ **Reward Shaping** - 獎勵函數設計
✅ **Online Learning** - 在線學習
✅ **Policy Gradient** - 策略梯度優化（進階）

---

## 🏗️ 技術架構

### 整體架構圖

```
┌─────────────────────────────────────────────────────────────────┐
│                    用戶查詢接口層                                  │
│  OpenWebUI / API / CLI                                          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│              RL-Agentic RAG 控制層（新增）                        │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌──────────────────┐  ┌────────────────┐ │
│  │  State Encoder  │  │  DQN Agent       │  │  Reward Model  │ │
│  │  (狀態編碼器)    │  │  (策略網絡)       │  │  (獎勵函數)     │ │
│  └─────────────────┘  └──────────────────┘  └────────────────┘ │
│  ┌─────────────────┐  ┌──────────────────┐  ┌────────────────┐ │
│  │Experience Replay│  │  Exploration     │  │  Performance   │ │
│  │  (經驗緩衝池)    │  │  Manager         │  │  Tracker       │ │
│  └─────────────────┘  └──────────────────┘  └────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│              多策略 RAG 執行層（現有）                             │
├─────────────────────────────────────────────────────────────────┤
│  Vector RAG │ Graph RAG │ Hybrid RAG │ Advanced RAG │ Self-RAG │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│              多資料庫層（現有）                                    │
│  Neo4j │ ChromaDB │ PostgreSQL │ Elasticsearch │ MongoDB       │
└─────────────────────────────────────────────────────────────────┘
```

### 技術棧選擇

| 組件 | 技術選擇 | 理由 |
|------|---------|------|
| **RL Framework** | PyTorch + Stable-Baselines3 | 成熟、文檔完善、易於集成 |
| **DQN Implementation** | SB3 DQN / Custom DQN | 靈活配置、預訓練模型 |
| **State Representation** | Sentence-BERT + Metadata | 語義理解 + 結構化特徵 |
| **Replay Buffer** | Redis + Local Cache | 持久化 + 快速訪問 |
| **Training Backend** | Ray RLlib (可選) | 分布式訓練 |
| **Monitoring** | TensorBoard + MLflow | 訓練可視化 + 模型管理 |

---

## 📅 實施階段

### Phase 1: 基礎設施準備 (Week 1-2)

#### 1.1 環境搭建
```bash
# 安裝 RL 相關依賴
pip install stable-baselines3[extra]
pip install tensorboard
pip install mlflow
pip install ray[rllib]  # 可選：分布式訓練
```

#### 1.2 數據收集系統
- 記錄現有查詢日誌
- 收集用戶反饋數據
- 建立標註數據集

#### 1.3 基準性能測試
- 測試現有 10 種 RAG 策略
- 建立性能基準線
- 定義評估指標

---

### Phase 2: RL 核心組件開發 (Week 3-5)

#### 2.1 狀態空間設計
```python
State = {
    'query_embedding': [768-dim vector],      # 查詢語義向量
    'query_length': int,                      # 查詢長度
    'query_complexity': float,                # 複雜度分數
    'domain_keywords': [list],                # 領域關鍵詞
    'user_history': [previous_queries],       # 用戶歷史
    'time_of_day': int,                       # 時段
    'previous_strategy': str,                 # 上一次策略
    'previous_performance': float,            # 上一次性能
}
```

#### 2.2 動作空間設計
```python
Action = {
    0: 'vector_rag',           # 純向量檢索
    1: 'graph_rag',            # 純圖譜檢索
    2: 'hybrid_rag',           # 混合檢索
    3: 'advanced_rag',         # 高級檢索
    4: 'agentic_rag',          # 智能代理（現有）
    5: 'self_rag',             # 自反思檢索
    6: 'adaptive_rag',         # 自適應檢索
    7: 'multimodal_rag',       # 多模態檢索
    8: 'dynamic_weight_0.3',   # 向量權重 0.3
    9: 'dynamic_weight_0.7',   # 向量權重 0.7
}
```

#### 2.3 獎勵函數設計
```python
Reward = (
    0.4 × confidence_score +           # 置信度
    0.3 × (1 - normalized_time) +      # 速度
    0.2 × user_satisfaction +          # 用戶滿意度
    0.1 × diversity_bonus              # 多樣性獎勵
)

# 懲罰項
- timeout_penalty: -10
- error_penalty: -5
- low_relevance_penalty: -2
```

---

### Phase 3: DQN Agent 實現 (Week 6-8)

#### 3.1 Q-Network 架構
```python
Q-Network:
  Input Layer: State (768 + metadata features)
  Hidden Layer 1: 512 neurons + ReLU + Dropout(0.2)
  Hidden Layer 2: 256 neurons + ReLU + Dropout(0.2)
  Hidden Layer 3: 128 neurons + ReLU
  Output Layer: 10 neurons (Q-values for 10 actions)
```

#### 3.2 訓練配置
```yaml
training_config:
  algorithm: DQN
  learning_rate: 0.0001
  gamma: 0.99                    # 折扣因子
  epsilon_start: 1.0             # 初始探索率
  epsilon_end: 0.05              # 最終探索率
  epsilon_decay: 0.995           # 衰減率
  batch_size: 64
  buffer_size: 100000            # 經驗池大小
  target_update_frequency: 1000  # 目標網絡更新頻率
  train_frequency: 4             # 訓練頻率
```

---

### Phase 4: 線上學習與部署 (Week 9-10)

#### 4.1 A/B 測試框架
- 50% 流量使用 RL-Agent
- 50% 流量使用原有 Agentic RAG
- 收集對比數據

#### 4.2 安全機制
- **Fallback 機制**: RL 失敗時回退到原策略
- **性能監控**: 實時監控 RL 決策質量
- **人工干預**: 異常情況下手動切換

---

## 💻 核心組件設計

### 1. State Encoder (狀態編碼器)

```python
class StateEncoder:
    """將查詢轉換為 RL 狀態向量"""

    def __init__(self, embedding_model='BAAI/bge-m3'):
        self.embedding_model = SentenceTransformer(embedding_model)
        self.complexity_analyzer = QueryComplexityAnalyzer()

    def encode(self, query: str, context: Dict) -> np.ndarray:
        # 1. 語義嵌入 (768維)
        query_embedding = self.embedding_model.encode(query)

        # 2. 查詢特徵 (20維)
        features = [
            len(query.split()),                    # 查詢長度
            self.complexity_analyzer.score(query), # 複雜度
            self._count_domain_keywords(query),    # 領域關鍵詞數量
            context.get('user_expertise', 0.5),    # 用戶專業度
            context.get('time_since_last', 0),     # 距上次查詢時間
            # ... 更多特徵
        ]

        # 3. 歷史特徵 (10維)
        history_features = self._encode_history(context.get('history', []))

        # 合併所有特徵
        state = np.concatenate([
            query_embedding,      # 768
            np.array(features),   # 20
            history_features      # 10
        ])  # Total: 798維

        return state
```

### 2. DQN Agent (深度 Q 網絡代理)

```python
class RLAgenticRAG:
    """基於 DQN 的強化學習 RAG 代理"""

    def __init__(self, state_dim=798, action_dim=10):
        # Q-網絡
        self.q_network = QNetwork(state_dim, action_dim)
        self.target_network = QNetwork(state_dim, action_dim)
        self.target_network.load_state_dict(self.q_network.state_dict())

        # 優化器
        self.optimizer = torch.optim.Adam(
            self.q_network.parameters(),
            lr=0.0001
        )

        # 經驗回放
        self.replay_buffer = ReplayBuffer(capacity=100000)

        # 超參數
        self.epsilon = 1.0         # 探索率
        self.epsilon_min = 0.05
        self.epsilon_decay = 0.995
        self.gamma = 0.99          # 折扣因子
        self.batch_size = 64

        # 策略映射
        self.action_to_strategy = {
            0: 'vector_rag',
            1: 'graph_rag',
            2: 'hybrid_rag',
            3: 'advanced_rag',
            4: 'agentic_rag',
            5: 'self_rag',
            6: 'adaptive_rag',
            7: 'multimodal_rag',
            8: 'dynamic_weight_0.3',
            9: 'dynamic_weight_0.7',
        }

    def select_action(self, state: np.ndarray, training=True) -> int:
        """選擇動作（ε-greedy 策略）"""
        if training and np.random.random() < self.epsilon:
            # 探索：隨機選擇
            return np.random.randint(0, len(self.action_to_strategy))
        else:
            # 利用：選擇最優動作
            with torch.no_grad():
                state_tensor = torch.FloatTensor(state).unsqueeze(0)
                q_values = self.q_network(state_tensor)
                return q_values.argmax().item()

    def train_step(self):
        """執行一步訓練"""
        if len(self.replay_buffer) < self.batch_size:
            return None

        # 從經驗池採樣
        batch = self.replay_buffer.sample(self.batch_size)
        states, actions, rewards, next_states, dones = batch

        # 計算當前 Q 值
        current_q = self.q_network(states).gather(1, actions.unsqueeze(1))

        # 計算目標 Q 值（雙 DQN）
        with torch.no_grad():
            next_actions = self.q_network(next_states).argmax(1, keepdim=True)
            next_q = self.target_network(next_states).gather(1, next_actions)
            target_q = rewards + (1 - dones) * self.gamma * next_q.squeeze()

        # 計算損失
        loss = F.mse_loss(current_q.squeeze(), target_q)

        # 反向傳播
        self.optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(self.q_network.parameters(), 1.0)
        self.optimizer.step()

        # 更新探索率
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)

        return loss.item()

    def update_target_network(self):
        """更新目標網絡"""
        self.target_network.load_state_dict(self.q_network.state_dict())

    async def query(self, query_text: str, context: Dict) -> RAGQueryResult:
        """執行查詢（整合到現有系統）"""
        # 1. 編碼狀態
        state = self.state_encoder.encode(query_text, context)

        # 2. 選擇策略
        action = self.select_action(state, training=self.is_training)
        strategy_name = self.action_to_strategy[action]

        # 3. 執行 RAG 查詢（調用現有系統）
        start_time = time.time()
        result = await self.execute_rag_strategy(strategy_name, query_text)
        processing_time = time.time() - start_time

        # 4. 計算獎勵
        reward = self.calculate_reward(result, processing_time, context)

        # 5. 存儲經驗
        next_state = state  # 簡化版本，實際應該是下一個狀態
        done = True         # 單步交互
        self.replay_buffer.push(state, action, reward, next_state, done)

        # 6. 訓練（如果處於訓練模式）
        if self.is_training and len(self.replay_buffer) >= self.batch_size:
            loss = self.train_step()
            if self.training_steps % 1000 == 0:
                self.update_target_network()
            self.training_steps += 1

        # 7. 記錄指標
        self.log_metrics(action, reward, processing_time, result.confidence_score)

        return result
```

### 3. Reward Model (獎勵函數)

```python
class RewardModel:
    """計算獎勵分數"""

    def __init__(self):
        self.weights = {
            'confidence': 0.4,
            'speed': 0.3,
            'satisfaction': 0.2,
            'diversity': 0.1
        }

    def calculate(self,
                  result: RAGQueryResult,
                  processing_time: float,
                  user_feedback: Optional[float] = None,
                  context: Dict = None) -> float:
        """
        計算獎勵分數

        Args:
            result: RAG 查詢結果
            processing_time: 處理時間（秒）
            user_feedback: 用戶反饋分數 (0-1)，可選
            context: 上下文信息

        Returns:
            reward: 獎勵分數
        """

        # 1. 置信度分數 (0-1)
        confidence_score = result.confidence_score

        # 2. 速度分數 (0-1)
        # 將處理時間標準化，越快越好
        max_acceptable_time = 5.0  # 5秒
        speed_score = max(0, 1 - (processing_time / max_acceptable_time))

        # 3. 用戶滿意度分數 (0-1)
        if user_feedback is not None:
            satisfaction_score = user_feedback
        else:
            # 如果沒有明確反饋，使用啟發式估計
            satisfaction_score = self._estimate_satisfaction(result)

        # 4. 多樣性獎勵 (0-1)
        # 鼓勵探索不同的策略組合
        diversity_score = self._calculate_diversity_bonus(
            result.strategy_used,
            context
        )

        # 5. 加權計算總獎勵
        reward = (
            self.weights['confidence'] * confidence_score +
            self.weights['speed'] * speed_score +
            self.weights['satisfaction'] * satisfaction_score +
            self.weights['diversity'] * diversity_score
        )

        # 6. 應用懲罰項
        reward -= self._calculate_penalties(result, processing_time)

        # 7. 標準化到 [-1, 1] 範圍
        reward = np.clip(reward, -1, 1)

        return reward

    def _estimate_satisfaction(self, result: RAGQueryResult) -> float:
        """啟發式估計用戶滿意度"""
        # 基於多個指標估計
        factors = [
            result.confidence_score,              # 置信度
            len(result.sources) / 5.0,           # 來源數量（期望5個）
            1.0 if not result.cache_hit else 0.8, # 新鮮度
        ]
        return np.mean(factors)

    def _calculate_diversity_bonus(self, strategy: str, context: Dict) -> float:
        """計算多樣性獎勵"""
        recent_strategies = context.get('recent_strategies', [])
        if len(recent_strategies) == 0:
            return 0.5

        # 如果策略與最近使用的不同，給予獎勵
        unique_ratio = len(set(recent_strategies)) / len(recent_strategies)
        return unique_ratio

    def _calculate_penalties(self, result: RAGQueryResult, time: float) -> float:
        """計算懲罰項"""
        penalty = 0.0

        # 超時懲罰
        if time > 10.0:
            penalty += 0.5

        # 低置信度懲罰
        if result.confidence_score < 0.5:
            penalty += 0.3

        # 錯誤懲罰
        if result.metadata.get('error', False):
            penalty += 1.0

        return penalty
```

### 4. Experience Replay Buffer (經驗回放緩衝池)

```python
class ReplayBuffer:
    """經驗回放緩衝池"""

    def __init__(self, capacity=100000, redis_client=None):
        self.capacity = capacity
        self.buffer = []
        self.position = 0
        self.redis_client = redis_client  # 可選：持久化到 Redis

    def push(self, state, action, reward, next_state, done):
        """添加經驗"""
        experience = (state, action, reward, next_state, done)

        if len(self.buffer) < self.capacity:
            self.buffer.append(experience)
        else:
            self.buffer[self.position] = experience

        self.position = (self.position + 1) % self.capacity

        # 可選：持久化到 Redis
        if self.redis_client:
            self._persist_to_redis(experience)

    def sample(self, batch_size):
        """隨機採樣批次"""
        indices = np.random.choice(len(self.buffer), batch_size, replace=False)
        batch = [self.buffer[idx] for idx in indices]

        states, actions, rewards, next_states, dones = zip(*batch)

        return (
            torch.FloatTensor(np.array(states)),
            torch.LongTensor(actions),
            torch.FloatTensor(rewards),
            torch.FloatTensor(np.array(next_states)),
            torch.FloatTensor(dones)
        )

    def __len__(self):
        return len(self.buffer)

    def _persist_to_redis(self, experience):
        """持久化經驗到 Redis"""
        if self.redis_client:
            key = f"rl_experience:{time.time()}"
            self.redis_client.lpush(key, json.dumps(experience))
            self.redis_client.expire(key, 86400)  # 24小時過期
```

---

## 🚀 訓練流程

### 訓練腳本

```python
# train_rl_agent.py

import asyncio
from rl_agentic_rag import RLAgenticRAG, StateEncoder, RewardModel

async def train_rl_agent(
    num_episodes=1000,
    max_steps_per_episode=100,
    save_interval=100
):
    """訓練 RL Agent"""

    # 初始化
    agent = RLAgenticRAG()
    agent.is_training = True

    # 載入訓練數據（查詢歷史）
    training_queries = load_training_queries('data/query_logs.json')

    # 訓練循環
    for episode in range(num_episodes):
        episode_rewards = []
        episode_losses = []

        # 隨機選擇查詢
        for step in range(max_steps_per_episode):
            query_data = random.choice(training_queries)
            query_text = query_data['query']
            context = query_data.get('context', {})

            # 執行查詢（包含 RL 決策和訓練）
            result = await agent.query(query_text, context)

            # 記錄指標
            reward = agent.last_reward
            loss = agent.last_loss

            episode_rewards.append(reward)
            if loss is not None:
                episode_losses.append(loss)

        # Episode 統計
        avg_reward = np.mean(episode_rewards)
        avg_loss = np.mean(episode_losses) if episode_losses else 0

        print(f"Episode {episode+1}/{num_episodes}")
        print(f"  Avg Reward: {avg_reward:.4f}")
        print(f"  Avg Loss: {avg_loss:.4f}")
        print(f"  Epsilon: {agent.epsilon:.4f}")

        # 定期保存模型
        if (episode + 1) % save_interval == 0:
            agent.save(f'models/rl_agent_episode_{episode+1}.pt')
            print(f"✅ Model saved at episode {episode+1}")

    print("🎉 Training completed!")
    agent.save('models/rl_agent_final.pt')

# 執行訓練
if __name__ == "__main__":
    asyncio.run(train_rl_agent())
```

---

## 📊 評估指標

### 1. 訓練指標

```python
training_metrics = {
    'episode_reward': [],        # 每個 episode 的總獎勵
    'average_q_value': [],       # 平均 Q 值
    'loss': [],                  # 訓練損失
    'epsilon': [],               # 探索率
    'training_time': []          # 訓練時間
}
```

### 2. 性能指標

```python
performance_metrics = {
    'strategy_accuracy': {},     # 各策略準確率
    'average_response_time': [], # 平均響應時間
    'user_satisfaction': [],     # 用戶滿意度
    'cache_hit_rate': [],        # 緩存命中率
    'diversity_score': []        # 策略多樣性
}
```

### 3. 對比實驗

| 指標 | 原 Agentic RAG | RL-Agentic RAG | 提升 |
|------|---------------|----------------|------|
| 平均準確率 | 85% | ？ | +X% |
| 平均響應時間 | 2.5s | ？ | -X% |
| 用戶滿意度 | 4.2/5 | ？ | +X |
| 策略多樣性 | 0.6 | ？ | +X |

---

## 🔧 部署方案

### Docker 部署

```dockerfile
# Dockerfile.rl-agent

FROM python:3.10-slim

WORKDIR /app

# 安裝依賴
COPY requirements-rl.txt .
RUN pip install -r requirements-rl.txt

# 複製代碼
COPY src/agents/rl/ ./agents/rl/
COPY models/ ./models/

# 環境變量
ENV RL_MODEL_PATH=/app/models/rl_agent_final.pt
ENV RL_TRAINING_MODE=false
ENV RL_EPSILON=0.05

# 啟動服務
CMD ["python", "agents/rl/rl_agent_server.py"]
```

### docker-compose 集成

```yaml
# docker-compose.yml (新增服務)

services:
  # ... 現有服務 ...

  rl-agent:
    build:
      context: .
      dockerfile: Dockerfile.rl-agent
    ports:
      - "8011:8011"
    environment:
      - RL_MODEL_PATH=/app/models/rl_agent_final.pt
      - NEO4J_URI=bolt://neo4j:7687
      - CHROMADB_URL=http://chromadb:8001
    volumes:
      - ./models:/app/models
      - ./logs:/app/logs
    depends_on:
      - neo4j
      - chromadb
    networks:
      - art-history-network
```

---

## 📈 監控與可視化

### TensorBoard 集成

```python
from torch.utils.tensorboard import SummaryWriter

writer = SummaryWriter('runs/rl_training')

# 訓練過程中記錄
writer.add_scalar('Loss/train', loss, global_step)
writer.add_scalar('Reward/episode', episode_reward, episode)
writer.add_scalar('Epsilon', epsilon, global_step)
writer.add_histogram('Q-values', q_values, global_step)
```

### MLflow 實驗追蹤

```python
import mlflow

mlflow.start_run()
mlflow.log_param("learning_rate", 0.0001)
mlflow.log_param("gamma", 0.99)
mlflow.log_metric("avg_reward", avg_reward)
mlflow.log_artifact("model.pt")
mlflow.end_run()
```

---

## 🎯 關鍵成功因素

1. **數據質量**: 需要足夠的查詢歷史和用戶反饋
2. **獎勵函數設計**: 獎勵函數需要反映真實的業務目標
3. **超參數調優**: learning rate, epsilon decay 等需要細緻調整
4. **安全機制**: 確保 RL 決策不會導致系統崩潰
5. **持續學習**: 部署後繼續在線學習和優化

---

## 📚 參考資料

1. **Deep Q-Learning**: Mnih et al., "Human-level control through deep reinforcement learning" (Nature 2015)
2. **Double DQN**: van Hasselt et al., "Deep Reinforcement Learning with Double Q-learning" (AAAI 2016)
3. **Stable-Baselines3**: https://stable-baselines3.readthedocs.io/
4. **RAG with RL**: Recent papers on RL for information retrieval

---

## ✅ 下一步行動

1. ✅ 閱讀完整方案
2. ⬜ 安裝 RL 依賴包
3. ⬜ 準備訓練數據
4. ⬜ 實現 State Encoder
5. ⬜ 實現 DQN Agent
6. ⬜ 實現 Reward Model
7. ⬜ 執行初步訓練
8. ⬜ 評估性能提升
9. ⬜ A/B 測試部署
10. ⬜ 持續優化改進

---

**製作日期**: 2026-01-11
**版本**: v1.0
**作者**: Art History Database Team
**狀態**: 📋 待實施
