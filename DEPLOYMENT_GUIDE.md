# 藝術史資料庫部署指南 🚀

## 快速部署指引

### 前置需求

- Docker Desktop 4.0+ 或 Docker Engine 20.10+
- Docker Compose 2.0+
- 最少8GB RAM，推薦16GB+
- 最少50GB可用磁碟空間

---

## 一鍵部署（推薦）

```bash
# 1. 克隆專案
git clone <repository-url>
cd 藝術史資料庫

# 2. 設置環境變數
cp art-history-database/.env.example art-history-database/.env
# 編輯 .env 填入您的API密鑰

# 3. 啟動所有服務
cd art-history-database
docker-compose -f docker-compose.complete.yml up -d

# 4. 檢查服務狀態
docker-compose -f docker-compose.complete.yml ps

# 5. 查看日誌
docker-compose -f docker-compose.complete.yml logs -f
```

---

## 服務訪問端點

啟動後可通過以下端點訪問各項服務：

| 服務 | 端點 | 說明 |
|-----|------|------|
| **Neo4j Browser** | http://localhost:7474 | 圖譜資料庫管理界面 |
| **RAG API** | http://localhost:8008 | RAG查詢API服務 |
| **品質監控** | http://localhost:8888 | 資料品質儀表板 |
| **Grafana** | http://localhost:3001 | 系統監控儀表板 |
| **Prometheus** | http://localhost:9090 | 指標收集服務 |
| **pgAdmin** | http://localhost:5050 | PostgreSQL管理界面 |

### 默認登入憑證

- **Neo4j**: neo4j / arthistory123
- **Grafana**: admin / (查看.env文件)
- **pgAdmin**: admin@arthistory.com / (查看.env文件)

---

## 詳細部署步驟

### 步驟1: 環境準備

```bash
# 檢查Docker版本
docker --version
docker-compose --version

# 確認Docker服務運行
docker ps

# 創建必要的目錄
mkdir -p art-history-database/{logs,data,monitoring}
```

### 步驟2: 配置環境變數

編輯 `art-history-database/.env` 文件：

```bash
# 必需的API密鑰
HARVARD_API_KEY=your_harvard_key_here
EUROPEANA_API_KEY=your_europeana_key_here
OPENAI_API_KEY=your_openai_key_here

# 資料庫密碼（請修改為強密碼）
POSTGRES_PASSWORD=your_strong_password
REDIS_PASSWORD=your_redis_password

# 監控服務密碼
GRAFANA_PASSWORD=your_grafana_password
PGADMIN_PASSWORD=your_pgadmin_password
```

### 步驟3: 啟動核心服務

```bash
# 只啟動核心資料庫服務
docker-compose -f docker-compose.complete.yml up -d neo4j postgres redis elasticsearch

# 等待服務啟動（約30秒）
sleep 30

# 檢查服務健康狀態
docker-compose -f docker-compose.complete.yml ps
```

### 步驟4: 啟動Agent服務

```bash
# 啟動所有Agent
docker-compose -f docker-compose.complete.yml up -d \
  web-crawler-agent \
  data-mapper-agent \
  summarization-agent \
  quality-monitor-agent
```

### 步驟5: 啟動RAG服務

```bash
# 啟動RAG API服務
docker-compose -f docker-compose.complete.yml up -d rag-api-server

# 測試API
curl http://localhost:8008/health
```

### 步驟6: 啟動監控服務

```bash
# 啟動監控堆疊
docker-compose -f docker-compose.complete.yml up -d \
  prometheus \
  grafana \
  pgadmin \
  nginx
```

---

## 驗證部署

### 1. 檢查所有容器狀態

```bash
docker-compose -f docker-compose.complete.yml ps
```

所有服務應該顯示 `Up` 狀態。

### 2. 測試資料庫連接

```bash
# 測試Neo4j
curl http://localhost:7474

# 測試PostgreSQL
docker exec art-postgres pg_isready

# 測試Redis
docker exec art-redis redis-cli ping
```

### 3. 測試API端點

```bash
# 健康檢查
curl http://localhost:8008/health

# RAG查詢測試
curl -X POST http://localhost:8008/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "介紹文藝復興藝術",
    "strategy": "hybrid_balanced",
    "top_k": 5
  }'
```

### 4. 查看品質監控儀表板

在瀏覽器中打開: http://localhost:8888/quality_dashboard.html

---

## 運行測試

```bash
# 進入專案目錄
cd art-history-database

# 運行自動化測試
./run_tests.sh

# 或者使用Docker運行測試
docker-compose -f docker-compose.complete.yml run --rm \
  quality-monitor-agent python test_suite.py
```

---

## 日誌查看

```bash
# 查看所有服務日誌
docker-compose -f docker-compose.complete.yml logs -f

# 查看特定服務日誌
docker-compose -f docker-compose.complete.yml logs -f rag-api-server

# 查看最近100行日誌
docker-compose -f docker-compose.complete.yml logs --tail=100

# 導出日誌到文件
docker-compose -f docker-compose.complete.yml logs > deployment.log
```

---

## 資料備份

### 備份Neo4j

```bash
# 停止Neo4j服務
docker-compose -f docker-compose.complete.yml stop neo4j

# 備份資料
docker run --rm \
  -v art-history-database_neo4j_data:/data \
  -v $(pwd)/backups:/backup \
  alpine tar czf /backup/neo4j-backup-$(date +%Y%m%d).tar.gz -C /data .

# 重啟Neo4j
docker-compose -f docker-compose.complete.yml start neo4j
```

### 備份PostgreSQL

```bash
# 創建備份
docker exec art-postgres pg_dump -U art_user art_history_db > backup-$(date +%Y%m%d).sql

# 或使用pg_dumpall備份所有資料庫
docker exec art-postgres pg_dumpall -U art_user > backup-all-$(date +%Y%m%d).sql
```

---

## 更新與維護

### 更新服務

```bash
# 拉取最新映像
docker-compose -f docker-compose.complete.yml pull

# 重啟服務
docker-compose -f docker-compose.complete.yml up -d
```

### 清理舊資料

```bash
# 清理未使用的Docker資源
docker system prune -a --volumes

# 只清理停止的容器
docker container prune
```

### 查看資源使用

```bash
# 查看容器資源使用
docker stats

# 查看磁碟使用
docker system df
```

---

## 停止服務

```bash
# 停止所有服務
docker-compose -f docker-compose.complete.yml stop

# 停止並刪除容器（保留資料）
docker-compose -f docker-compose.complete.yml down

# 完全清理（包括資料卷）
docker-compose -f docker-compose.complete.yml down -v
```

---

## 故障排除

### 問題1: 服務無法啟動

```bash
# 檢查日誌
docker-compose -f docker-compose.complete.yml logs [service-name]

# 檢查端口佔用
sudo netstat -tulpn | grep LISTEN

# 重啟單個服務
docker-compose -f docker-compose.complete.yml restart [service-name]
```

### 問題2: 記憶體不足

```bash
# 增加Docker記憶體限制
# Docker Desktop: Settings -> Resources -> Memory

# 限制特定服務記憶體
docker-compose -f docker-compose.complete.yml up -d \
  --scale web-crawler-agent=1 \
  --scale data-mapper-agent=1
```

### 問題3: Neo4j連接失敗

```bash
# 檢查Neo4j日誌
docker logs art-neo4j

# 重置Neo4j密碼
docker exec -it art-neo4j cypher-shell -u neo4j -p neo4j
# 然後執行: ALTER USER neo4j SET PASSWORD 'arthistory123';
```

---

## 生產環境建議

### 安全加固

1. **修改默認密碼**: 更改所有默認密碼
2. **啟用HTTPS**: 配置SSL證書
3. **防火牆設置**: 只開放必要端口
4. **定期更新**: 保持所有服務最新

### 性能優化

1. **資源分配**: 根據負載調整容器資源
2. **啟用快取**: 確保Redis正常運行
3. **資料庫調優**: 優化Neo4j和PostgreSQL配置
4. **負載均衡**: 使用Nginx進行負載分配

### 監控告警

1. **設置Grafana告警**: 配置關鍵指標告警
2. **日誌聚合**: 集中收集所有日誌
3. **健康檢查**: 設置定時健康檢查
4. **備份自動化**: 定期自動備份資料

---

## 進階配置

### 自定義Nginx配置

編輯 `art-history-database/nginx/nginx.conf`:

```nginx
upstream rag_api {
    server rag-api-server:8008;
}

server {
    listen 80;
    server_name your-domain.com;

    location /api/ {
        proxy_pass http://rag_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 擴展服務

```bash
# 水平擴展爬蟲Agent
docker-compose -f docker-compose.complete.yml up -d \
  --scale web-crawler-agent=3

# 查看擴展後的容器
docker-compose -f docker-compose.complete.yml ps
```

---

## 支援與聯繫

- 📧 Email: support@arthistory-db.com
- 📚 文檔: [完整文檔連結]
- 🐛 問題報告: [GitHub Issues]
- 💬 討論: [GitHub Discussions]

---

**部署文檔版本**: 1.0.0
**最後更新**: 2025-10-16
**維護團隊**: Art History Database Team
