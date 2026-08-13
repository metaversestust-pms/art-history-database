# Open WebUI 網站架設說明

## 概述

已成功將 Open WebUI 通過 Nginx 反向代理架設為網站，現在可以透過 HTTP 訪問並提供給他人使用。

## 訪問地址

### 本地訪問
- **首頁**: http://localhost/
- **Open WebUI (AI 聊天)**: http://localhost/chat/
- **Open WebUI 直接訪問**: http://localhost:8080/
- **健康檢查**: http://localhost/health

### 網路訪問（區域網路）
如果您在同一區域網路中，其他人可以通過您的 IP 地址訪問：
- 查看您的 IP: `ipconfig`（Windows）或 `ip addr`（Linux）
- 訪問地址: `http://您的IP地址/chat/`

例如：`http://192.168.1.100/chat/`

## 架構說明

```
用戶瀏覽器
    ↓
Nginx (Port 80) ← 反向代理
    ↓
Open WebUI (Port 8080) ← AI 聊天界面
    ↓
Ollama (Port 11434) ← LLM 服務
```

## 服務狀態檢查

### 檢查所有服務狀態
```bash
docker ps | grep -E "nginx|openwebui|ollama"
```

### 檢查 Nginx 日誌
```bash
docker logs art-database-nginx
```

### 檢查 Open WebUI 日誌
```bash
docker logs art-history-openwebui
```

## 配置文件位置

- **Nginx 配置**: `context/deployment/nginx-simple.conf`
- **首頁**: `public/index.html`
- **Docker Compose (主系統)**: `docker-compose.yml`
- **Docker Compose (Open WebUI)**: `docker-compose.openwebui.yml`

## 啟動和停止服務

### 啟動所有服務
```bash
cd /mnt/c/Users/ssking1999/Desktop/藝術史資料庫/art-history-database

# 啟動 Nginx
docker-compose up -d nginx

# 啟動 Open WebUI
docker-compose -f docker-compose.openwebui.yml up -d openwebui
```

### 停止服務
```bash
# 停止 Nginx
docker-compose stop nginx

# 停止 Open WebUI
docker-compose -f docker-compose.openwebui.yml stop openwebui
```

### 重新加載 Nginx 配置（無需停機）
```bash
docker exec art-database-nginx nginx -s reload
```

## 網路配置

- Open WebUI 容器連接到兩個網路:
  - `art-history-network` (與 Ollama 通信)
  - `art-history-database_art-network` (與 Nginx 通信)

## 對外開放設置

### 方案 1: 區域網路訪問（已完成）
當前配置已支持區域網路訪問。同一網路中的用戶可以通過您的內網 IP 訪問。

### 方案 2: 公網訪問（需要額外設置）

#### 選項 A: 端口轉發
如果您有固定 IP 或 DDNS：
1. 在路由器設置端口轉發: 外部 80 → 內部 80
2. 設置防火牆規則允許 80 端口
3. 通過公網 IP 訪問

#### 選項 B: 使用穿透服務（推薦用於測試）

**使用 ngrok:**
```bash
# 安裝 ngrok
# 從 https://ngrok.com/ 下載並註冊

# 啟動穿透
ngrok http 80

# ngrok 會提供一個公網地址，例如:
# https://abc123.ngrok.io
```

**使用 Cloudflare Tunnel:**
```bash
# 安裝 cloudflared
# 從 https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/

# 設置隧道
cloudflared tunnel --url http://localhost:80
```

## SSL/HTTPS 設置（可選）

如果需要啟用 HTTPS，我們已準備好 SSL 證書目錄和配置：

### 使用自簽證書（測試用）
已生成的自簽證書位於 `ssl/` 目錄。

### 使用 Let's Encrypt（生產環境推薦）
```bash
# 安裝 certbot
sudo apt-get install certbot python3-certbot-nginx

# 獲取證書（需要域名）
certbot certonly --standalone -d your-domain.com

# 將證書複製到 ssl 目錄
cp /etc/letsencrypt/live/your-domain.com/fullchain.pem ssl/cert.pem
cp /etc/letsencrypt/live/your-domain.com/privkey.pem ssl/key.pem

# 使用完整的 Nginx 配置（包含 HTTPS）
# 修改 docker-compose.yml 中的 nginx 配置文件路徑
# 從 nginx-simple.conf 改為 nginx.conf
```

### 啟用 HTTPS 配置
1. 更新 `docker-compose.yml`:
```yaml
  nginx:
    image: nginx:alpine
    container_name: art-database-nginx
    ports:
      - "80:80"
      - "443:443"  # 添加 HTTPS 端口
    volumes:
      - ./context/deployment/nginx.conf:/etc/nginx/nginx.conf:ro  # 使用完整配置
      - ./ssl:/etc/nginx/ssl:ro
      - ./public:/usr/share/nginx/html:ro
      - nginx_logs:/var/log/nginx
    networks:
      - art-network
    restart: unless-stopped
```

2. 重啟 Nginx:
```bash
docker-compose up -d nginx
```

## 安全建議

### 1. 啟用身份驗證
Open WebUI 支持用戶註冊和登入。在 `docker-compose.openwebui.yml` 中:
```yaml
environment:
  - WEBUI_AUTH=true  # 啟用認證
  - ENABLE_SIGNUP=false  # 禁用公開註冊（可選）
```

### 2. 限制訪問來源
在 Nginx 配置中添加 IP 白名單:
```nginx
location /chat/ {
    # 只允許特定 IP 訪問
    allow 192.168.1.0/24;  # 允許區域網路
    deny all;

    # ... 其他配置
}
```

### 3. 設置防火牆
```bash
# Ubuntu/Debian
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# 限制只允許特定 IP
sudo ufw allow from 192.168.1.0/24 to any port 80
```

### 4. 定期更新
```bash
# 更新 Docker 映像
docker-compose pull
docker-compose up -d
```

## 故障排除

### 問題 1: 無法訪問 /chat/
**檢查**:
```bash
# 確認 Open WebUI 正在運行
docker ps | grep openwebui

# 檢查網路連接
docker exec art-database-nginx ping art-history-openwebui

# 查看 Nginx 錯誤日誌
docker logs art-database-nginx
```

### 問題 2: 502 Bad Gateway
**原因**: Nginx 無法連接到 Open WebUI

**解決**:
```bash
# 重啟 Open WebUI
docker-compose -f docker-compose.openwebui.yml restart openwebui

# 檢查兩個容器是否在同一網路
docker network inspect art-history-database_art-network
```

### 問題 3: Nginx 無法啟動
**檢查配置**:
```bash
docker exec art-database-nginx nginx -t
```

### 問題 4: 頁面加載緩慢
**優化建議**:
1. 檢查 Ollama 模型是否已加載
2. 增加 Nginx 超時時間
3. 檢查系統資源使用情況

## 效能監控

### 查看資源使用
```bash
docker stats art-database-nginx art-history-openwebui art-history-ollama
```

### Nginx 訪問統計
```bash
# 查看訪問日誌
docker exec art-database-nginx tail -f /var/log/nginx/access.log

# 統計訪問量
docker exec art-database-nginx cat /var/log/nginx/access.log | wc -l
```

## 備份和恢復

### 備份 Open WebUI 數據
```bash
# 數據位置
docker volume ls | grep openwebui

# 備份
docker run --rm -v art-history-database_openwebui_data:/data -v $(pwd):/backup ubuntu tar czf /backup/openwebui-backup.tar.gz /data
```

### 恢復數據
```bash
docker run --rm -v art-history-database_openwebui_data:/data -v $(pwd):/backup ubuntu tar xzf /backup/openwebui-backup.tar.gz -C /
```

## 進階配置

### 自訂域名
1. 購買域名並設置 DNS 指向您的 IP
2. 更新 Nginx 配置中的 `server_name`:
```nginx
server {
    server_name your-domain.com;
    # ... 其他配置
}
```

### 負載均衡（多個 Open WebUI 實例）
```nginx
upstream open_webui {
    server art-history-openwebui-1:8080;
    server art-history-openwebui-2:8080;
    server art-history-openwebui-3:8080;
}
```

### 添加更多服務
在 `nginx-simple.conf` 中添加新的 location:
```nginx
location /api/ {
    set $api http://your-api-service:port;
    proxy_pass $api/;
    # ... proxy 設置
}
```

## 聯絡支援

如有問題或需要協助，請：
1. 查看 Nginx 和 Open WebUI 日誌
2. 檢查 Docker 容器狀態
3. 參考 Open WebUI 官方文檔: https://docs.openwebui.com/

## 更新記錄

- **2025-11-08**: 初始設置完成
  - 配置 Nginx 反向代理
  - 連接 Open WebUI 和 Nginx 網路
  - 創建首頁界面
  - 啟用 HTTP 訪問
