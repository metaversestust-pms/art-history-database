# 🎨 藝術史資料庫系統 - Docker Compose 部署指南

## 📋 概述

此優化版 Docker Compose 配置整合了完整的藝術史資料庫系統，包含：

- 🎮 **CUDA/GPU 加速的機器學習服務**
- 📊 **多模態RAG系統 (文字、圖像、音頻)**
- 🔍 **全文搜索與向量搜索**
- 📈 **完整監控與可觀察性**
- 🧪 **ML實驗管理與追蹤**
- 🔄 **自動化健康檢查與恢復**

## 🏗️ 系統架構

### 核心服務層
- **主API服務** (`art-database-api`) - Node.js Express 應用
- **CUDA ML服務** (`cuda-ml-service`) - GPU加速的Python Flask ML API
- **Nginx反向代理** - 負載均衡與路由

### 資料存儲層
- **PostgreSQL** - 關聯式資料庫 (主要數據)
- **Redis** - 快取與會話存儲
- **Elasticsearch** - 全文搜索引擎
- **Neo4j** - 圖資料庫 (知識圖譜)
- **ChromaDB** - 向量資料庫 (嵌入向量)

### AI/ML層
- **PyTorch + CUDA** - GPU加速深度學習
- **Transformers** - NLP模型 (BERT, GPT等)
- **Jupyter Lab** - ML實驗環境
- **MLflow** - 實驗追蹤與模型管理

### 監控層
- **Prometheus** - 指標收集
- **Grafana** - 視覺化面板
- **Node Exporter** - 系統監控

## 🚀 快速部署

### 1. 環境準備

確保已安裝：
```bash
# Docker & Docker Compose
docker --version
docker compose version

# NVIDIA Container Toolkit (用於GPU支援)
nvidia-smi
docker run --rm --gpus all nvidia/cuda:12.0-base nvidia-smi
```

### 2. 配置環境變數

複製並編輯環境變數：
```bash
cp .env.example .env
vi .env
```

關鍵配置項：
```env
# 資料庫
POSTGRES_PASSWORD=your-secure-password
DB_NAME=art_history_db
DB_USER=art_user

# GPU配置
CUDA_DEVICE_ID=0
CUDA_MEMORY_FRACTION=0.8

# 服務密鑰
GRAFANA_PASSWORD=admin123
JUPYTER_TOKEN=art-history-ml-2024
```

### 3. 一鍵部署

```bash
# 賦予執行權限
chmod +x deploy.sh

# 完整部署
./deploy.sh deploy

# 或者使用Docker Compose
docker compose -f docker-compose.optimized.yml up -d
```

## 📊 服務端點

### 主要API
- **主API**: http://localhost:3000/api
- **ML API**: http://localhost:8080
- **API文檔**: http://localhost:3000/api/docs

### 監控面板
- **Grafana**: http://localhost:3001 (admin/password)
- **Prometheus**: http://localhost:9090
- **Jupyter Lab**: http://localhost:8888 (token: jwt-token)

### 資料庫管理
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379
- **Elasticsearch**: http://localhost:9200
- **Neo4j Browser**: http://localhost:7474
- **ChromaDB**: http://localhost:8000

### 實驗管理
- **MLflow**: http://localhost:5000

## 🔧 管理指令

### 部署管理
```bash
# 啟動所有服務
./deploy.sh deploy

# 停止所有服務
./deploy.sh down

# 重啟服務
./deploy.sh restart

# 查看狀態
./deploy.sh status

# 查看日誌
./deploy.sh logs

# 完全清理
./deploy.sh clean
```

### Docker Compose指令
```bash
# 啟動特定服務
docker compose -f docker-compose.optimized.yml up -d postgres redis

# 查看服務狀態
docker compose -f docker-compose.optimized.yml ps

# 查看日誌
docker compose -f docker-compose.optimized.yml logs -f cuda-ml-service

# 進入容器
docker compose -f docker-compose.optimized.yml exec art-database-api bash

# 擴展服務
docker compose -f docker-compose.optimized.yml up -d --scale cuda-ml-service=2
```

## 🎮 GPU加速配置

### CUDA支援檢查
```bash
# 檢查GPU狀態
nvidia-smi

# 檢查Docker GPU支援
docker run --rm --gpus all nvidia/cuda:12.0-base nvidia-smi

# 檢查ML服務GPU使用
docker compose -f docker-compose.optimized.yml exec cuda-ml-service nvidia-smi
```

### GPU資源配置
在 `docker-compose.optimized.yml` 中調整：
```yaml
cuda-ml-service:
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: 1  # GPU數量
            capabilities: [gpu]
```

## 📈 監控與告警

### Grafana面板配置
1. 存取 http://localhost:3001
2. 登入 (admin/密碼)
3. 導入預設Dashboard：
   - 系統資源監控
   - API性能監控
   - ML模型訓練監控
   - GPU使用率監控

### 關鍵監控指標
- **API響應時間** - 平均 < 200ms
- **GPU記憶體使用** - < 80%
- **資料庫連接數** - < 100
- **Redis記憶體使用** - < 2GB
- **磁碟使用率** - < 85%

## 🔒 安全配置

### 網路安全
- 內部服務使用橋接網路隔離
- Prometheus/Jupyter僅內網存取
- Nginx反向代理統一入口

### 資料安全
- PostgreSQL密碼加密
- Redis認證啟用
- 敏感配置使用環境變數

### 容器安全
- 非root用戶執行
- 資源限制設定
- 健康檢查自動恢復

## 🐛 故障排除

### 常見問題

**1. GPU服務啟動失敗**
```bash
# 檢查NVIDIA驅動
nvidia-smi

# 檢查Container Toolkit
docker run --rm --gpus all nvidia/cuda:12.0-base nvidia-smi

# 重建ML服務鏡像
docker compose -f docker-compose.optimized.yml build cuda-ml-service
```

**2. 資料庫連接失敗**
```bash
# 檢查PostgreSQL狀態
docker compose -f docker-compose.optimized.yml exec postgres pg_isready

# 重置資料庫
docker compose -f docker-compose.optimized.yml down postgres
docker volume rm art-history-database_postgres_data
docker compose -f docker-compose.optimized.yml up -d postgres
```

**3. ML模型下載失敗**
```bash
# 檢查網路連接
docker compose -f docker-compose.optimized.yml exec cuda-ml-service curl -I https://huggingface.co

# 手動下載模型
docker compose -f docker-compose.optimized.yml exec cuda-ml-service \
  python -c "from transformers import BertModel; BertModel.from_pretrained('bert-base-multilingual-cased')"
```

### 效能優化

**1. GPU記憶體優化**
```yaml
cuda-ml-service:
  environment:
    - PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:128
    - CUDA_LAUNCH_BLOCKING=0
```

**2. 資料庫效能調整**
```yaml
postgres:
  command: >
    postgres
    -c shared_buffers=256MB
    -c max_connections=200
    -c effective_cache_size=1GB
```

**3. Redis記憶體優化**
```yaml
redis:
  command: >
    redis-server
    --maxmemory 2gb
    --maxmemory-policy allkeys-lru
```

## 📚 進階功能

### 多GPU支援
```yaml
cuda-ml-service:
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: all  # 使用所有GPU
            capabilities: [gpu]
```

### 負載均衡
```bash
# 啟動多個ML服務實例
docker compose -f docker-compose.optimized.yml up -d --scale cuda-ml-service=3
```

### 資料備份
```bash
# 資料庫備份
docker compose -f docker-compose.optimized.yml exec postgres \
  pg_dump -U art_user art_history_db > backup.sql

# 向量資料備份
docker compose -f docker-compose.optimized.yml exec chromadb \
  tar -czf /tmp/chromadb_backup.tar.gz /chroma/chroma
```

## 🤝 支援與維護

### 日誌收集
```bash
# 所有服務日誌
docker compose -f docker-compose.optimized.yml logs > system.log

# 特定服務日誌
docker compose -f docker-compose.optimized.yml logs cuda-ml-service > ml-service.log
```

### 系統更新
```bash
# 更新鏡像
docker compose -f docker-compose.optimized.yml pull

# 重建並重啟
docker compose -f docker-compose.optimized.yml up -d --build
```

### 效能基準測試
```bash
# API負載測試
curl -X POST http://localhost:3000/api/artworks \
  -H "Content-Type: application/json" \
  -d '{"title": "測試藝術品", "artist": "測試藝術家"}'

# ML服務測試
curl -X POST http://localhost:8080/classify/artwork \
  -H "Content-Type: application/json" \
  -d '{"text": "文藝復興時期的肖像畫作品"}'
```

---

**🎨 享受您的藝術史資料庫系統！**

如需技術支援或功能建議，請查看項目文檔或提交Issue。