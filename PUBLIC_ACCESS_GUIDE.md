# Open WebUI 公網訪問設置指南

## 問題說明

目前系統只能在區域網路內訪問。如果要讓不同網路、不同地區的人訪問，需要將服務暴露到公網。

## 方案比較

| 方案 | 難度 | 成本 | 安全性 | 穩定性 | 適用場景 |
|------|------|------|--------|--------|----------|
| **Cloudflare Tunnel** | ⭐ 簡單 | 免費 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | **最推薦** |
| ngrok | ⭐ 簡單 | 免費/付費 | ⭐⭐⭐ | ⭐⭐⭐ | 快速測試 |
| 端口轉發 | ⭐⭐⭐ 中等 | 免費 | ⭐⭐ | ⭐⭐⭐ | 有固定 IP |
| VPS 部署 | ⭐⭐⭐⭐ 複雜 | 付費 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 生產環境 |

---

## 🌟 方案 1: Cloudflare Tunnel（強烈推薦）

**優點:**
- ✅ 完全免費
- ✅ 自動 HTTPS 加密
- ✅ 不需要公網 IP
- ✅ 不需要端口轉發
- ✅ DDoS 防護
- ✅ 可綁定自定義域名
- ✅ 穩定可靠

**缺點:**
- ❌ 需要註冊 Cloudflare 帳號
- ❌ 需要擁有域名（可使用免費域名服務）

### 步驟 1: 註冊 Cloudflare 並添加域名

#### 選項 A: 已有域名
1. 訪問 [Cloudflare](https://dash.cloudflare.com/sign-up)
2. 註冊帳號並添加您的域名
3. 按指示更改域名的 DNS 伺服器到 Cloudflare

#### 選項 B: 使用免費域名
推薦的免費域名服務：
- [Freenom](https://www.freenom.com/) - 提供 .tk, .ml, .ga, .cf, .gq 免費域名
- [No-IP](https://www.noip.com/) - 提供免費動態 DNS
- [DuckDNS](https://www.duckdns.org/) - 簡單的免費域名服務

### 步驟 2: 安裝 Cloudflared

```bash
# 下載 cloudflared（Windows WSL2 環境）
cd ~
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64
chmod +x cloudflared-linux-amd64
sudo mv cloudflared-linux-amd64 /usr/local/bin/cloudflared

# 驗證安裝
cloudflared version
```

### 步驟 3: 登入 Cloudflare

```bash
cloudflared tunnel login
```

這會打開瀏覽器，選擇您要使用的域名並授權。

### 步驟 4: 創建 Tunnel

```bash
# 創建一個新的 tunnel（命名為 art-history）
cloudflared tunnel create art-history

# 記下顯示的 Tunnel ID，例如: abc123-def456-ghi789
```

### 步驟 5: 配置 Tunnel

創建配置文件：

```bash
mkdir -p ~/.cloudflared
nano ~/.cloudflared/config.yml
```

填入以下內容（**替換成您的資訊**）：

```yaml
tunnel: YOUR_TUNNEL_ID  # 替換為您的 Tunnel ID
credentials-file: /home/YOUR_USERNAME/.cloudflared/YOUR_TUNNEL_ID.json  # 替換路徑

ingress:
  # Open WebUI - AI 聊天
  - hostname: chat.your-domain.com  # 替換為您的域名
    service: http://localhost:80
    originRequest:
      noTLSVerify: true

  # 首頁（可選）
  - hostname: your-domain.com  # 替換為您的域名
    service: http://localhost:80

  # 捕獲所有其他請求
  - service: http_status:404
```

### 步驟 6: 設置 DNS 記錄

```bash
# 為您的域名創建 DNS 記錄
cloudflared tunnel route dns art-history chat.your-domain.com
cloudflared tunnel route dns art-history your-domain.com
```

### 步驟 7: 運行 Tunnel

#### 測試運行
```bash
cloudflared tunnel run art-history
```

訪問 `https://chat.your-domain.com/chat/` 測試是否正常。

#### 背景運行
如果測試成功，可以設置為服務：

```bash
# 安裝為系統服務
sudo cloudflared service install

# 啟動服務
sudo systemctl start cloudflared
sudo systemctl enable cloudflared

# 檢查狀態
sudo systemctl status cloudflared
```

### 完整設置腳本

創建一個自動化腳本：

```bash
#!/bin/bash
# cloudflare-tunnel-setup.sh

echo "=== Cloudflare Tunnel 設置腳本 ==="

# 檢查是否已安裝 cloudflared
if ! command -v cloudflared &> /dev/null; then
    echo "安裝 cloudflared..."
    wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64
    chmod +x cloudflared-linux-amd64
    sudo mv cloudflared-linux-amd64 /usr/local/bin/cloudflared
fi

echo "請訪問瀏覽器進行授權..."
cloudflared tunnel login

read -p "輸入 Tunnel 名稱（例如: art-history）: " TUNNEL_NAME
cloudflared tunnel create $TUNNEL_NAME

read -p "輸入您的域名（例如: your-domain.com）: " DOMAIN

# 獲取 Tunnel ID
TUNNEL_ID=$(cloudflared tunnel list | grep $TUNNEL_NAME | awk '{print $1}')
echo "Tunnel ID: $TUNNEL_ID"

# 創建配置文件
cat > ~/.cloudflared/config.yml <<EOF
tunnel: $TUNNEL_ID
credentials-file: /home/$USER/.cloudflared/$TUNNEL_ID.json

ingress:
  - hostname: chat.$DOMAIN
    service: http://localhost:80
  - hostname: $DOMAIN
    service: http://localhost:80
  - service: http_status:404
EOF

echo "設置 DNS 記錄..."
cloudflared tunnel route dns $TUNNEL_NAME chat.$DOMAIN
cloudflared tunnel route dns $TUNNEL_NAME $DOMAIN

echo ""
echo "=== 設置完成! ==="
echo "請運行以下命令啟動 tunnel:"
echo "  cloudflared tunnel run $TUNNEL_NAME"
echo ""
echo "訪問地址:"
echo "  https://chat.$DOMAIN/chat/"
echo "  https://$DOMAIN/"
```

---

## 🚀 方案 2: ngrok（快速測試用）

**優點:**
- ✅ 設置極其簡單（5分鐘內完成）
- ✅ 自動 HTTPS
- ✅ 不需要域名
- ✅ 適合臨時分享

**缺點:**
- ❌ 免費版 URL 會變動
- ❌ 免費版有連線數限制
- ❌ 不適合長期使用

### 步驟 1: 安裝 ngrok

```bash
# 下載並安裝
curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null
echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | sudo tee /etc/apt/sources.list.d/ngrok.list
sudo apt update && sudo apt install ngrok
```

### 步驟 2: 註冊並配置

1. 訪問 [ngrok.com](https://ngrok.com/) 註冊免費帳號
2. 獲取 authtoken
3. 配置 authtoken:

```bash
ngrok config add-authtoken YOUR_AUTH_TOKEN
```

### 步驟 3: 啟動 Tunnel

```bash
# 基本用法
ngrok http 80

# 自訂域名（付費版功能）
ngrok http 80 --domain=your-domain.ngrok.io
```

輸出會顯示公網 URL，例如：
```
Forwarding  https://abc123.ngrok.io -> http://localhost:80
```

分享 `https://abc123.ngrok.io/chat/` 給其他人即可訪問。

### 步驟 4: 背景運行（可選）

創建配置文件 `~/.ngrok.yml`:

```yaml
version: "2"
authtoken: YOUR_AUTH_TOKEN
tunnels:
  art-history:
    proto: http
    addr: 80
    bind_tls: true
```

運行：
```bash
ngrok start art-history
```

---

## 🏠 方案 3: 端口轉發（需要固定 IP）

**前置條件:**
- 有固定公網 IP 或動態 DNS
- 可以訪問路由器管理界面
- 對網路配置有一定了解

### 步驟 1: 確認您的網路類型

```bash
# 查看本機內網 IP
ipconfig  # Windows
ip addr   # Linux

# 訪問 https://www.whatismyip.com/ 查看公網 IP
```

如果公網 IP 和您查到的外網 IP 相同，表示您有公網 IP。

### 步驟 2: 設置端口轉發

1. 登入路由器管理界面（通常是 192.168.1.1 或 192.168.0.1）
2. 找到「端口轉發」或「虛擬服務器」設置
3. 添加新規則：
   - **外部端口**: 80（HTTP）和 443（HTTPS）
   - **內部 IP**: 您的電腦 IP（例如 192.168.1.100）
   - **內部端口**: 80 和 443
   - **協議**: TCP

### 步驟 3: 設置動態 DNS（如果沒有固定 IP）

使用 No-IP 或 DuckDNS：

```bash
# DuckDNS 範例
# 1. 在 https://www.duckdns.org/ 註冊並創建域名
# 2. 安裝更新腳本

mkdir -p ~/duckdns
cd ~/duckdns
nano duck.sh
```

填入：
```bash
#!/bin/bash
echo url="https://www.duckdns.org/update?domains=YOUR_DOMAIN&token=YOUR_TOKEN&ip=" | curl -k -o ~/duckdns/duck.log -K -
```

設置定時更新：
```bash
chmod +x duck.sh
crontab -e
# 添加: */5 * * * * ~/duckdns/duck.sh >/dev/null 2>&1
```

### 步驟 4: 配置防火牆

```bash
# Windows Defender 防火牆
# 控制台 -> 系統及安全性 -> Windows Defender 防火牆 -> 進階設定
# 新增輸入規則: 允許 TCP 80, 443

# Linux (如果有)
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
```

---

## ☁️ 方案 4: VPS 雲端部署（生產環境）

**適用於:** 需要高穩定性、專業運營的場景

### 推薦的 VPS 提供商

| 提供商 | 最低價格 | 特點 |
|--------|----------|------|
| [DigitalOcean](https://www.digitalocean.com/) | $4/月 | 簡單易用，文檔豐富 |
| [Linode](https://www.linode.com/) | $5/月 | 效能好，支援好 |
| [Vultr](https://www.vultr.com/) | $2.5/月 | 便宜，機房多 |
| [AWS Lightsail](https://aws.amazon.com/lightsail/) | $3.5/月 | AWS 生態系統 |

### 基本步驟

1. **購買 VPS** - 選擇 Ubuntu 22.04 LTS
2. **安裝 Docker** 和 Docker Compose
3. **上傳代碼** - 使用 git clone 或 scp
4. **配置防火牆** - 開放 80, 443 端口
5. **設置域名** - 將域名 A 記錄指向 VPS IP
6. **啟用 SSL** - 使用 Let's Encrypt
7. **運行服務** - docker-compose up -d

詳細部署腳本：

```bash
# VPS 初始化腳本
#!/bin/bash

# 更新系統
sudo apt update && sudo apt upgrade -y

# 安裝 Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 安裝 Docker Compose
sudo apt install docker-compose -y

# 克隆代碼（或上傳）
git clone YOUR_REPO_URL
cd YOUR_PROJECT

# 安裝 certbot
sudo apt install certbot python3-certbot-nginx -y

# 獲取 SSL 證書
sudo certbot certonly --standalone -d your-domain.com -d chat.your-domain.com

# 啟動服務
docker-compose up -d

# 設置自動更新 SSL
echo "0 0 1 * * certbot renew --quiet" | sudo crontab -
```

---

## 🔒 安全加固建議

無論使用哪種方案，都應該：

### 1. 啟用 HTTPS

如果使用 Cloudflare Tunnel，自動啟用。

其他方案使用 Let's Encrypt：
```bash
sudo certbot --nginx -d your-domain.com
```

### 2. 啟用身份驗證

編輯 `docker-compose.openwebui.yml`:

```yaml
environment:
  - WEBUI_AUTH=true  # 必須登入
  - ENABLE_SIGNUP=false  # 關閉註冊
  - DEFAULT_USER_ROLE=user
```

創建管理員帳號：
```bash
docker exec -it art-history-openwebui python manage.py createsuperuser
```

### 3. IP 白名單（可選）

在 Nginx 配置中限制訪問：

```nginx
location /chat/ {
    # 只允許特定國家/IP
    allow 1.2.3.4;  # 允許特定 IP
    deny all;

    # ... 其他配置
}
```

### 4. 速率限制

防止濫用：

```nginx
http {
    limit_req_zone $binary_remote_addr zone=chatzone:10m rate=10r/s;

    server {
        location /chat/ {
            limit_req zone=chatzone burst=20;
            # ...
        }
    }
}
```

### 5. 設置 Cloudflare WAF（使用 Cloudflare Tunnel 時）

在 Cloudflare 控制台：
- Security > WAF > Managed Rules - 啟用
- Security > DDoS - 確保啟用
- Security > Rate Limiting - 設置規則

---

## 📊 方案選擇建議

### 選擇 Cloudflare Tunnel，如果：
- ✅ 想要免費且穩定的解決方案
- ✅ 願意註冊 Cloudflare 並設置域名
- ✅ 需要長期使用
- ✅ 重視安全性

### 選擇 ngrok，如果：
- ✅ 只是臨時測試或演示
- ✅ 不想購買域名
- ✅ 需要快速設置（5分鐘）

### 選擇端口轉發，如果：
- ✅ 有固定公網 IP
- ✅ 熟悉網路配置
- ✅ 不想依賴第三方服務

### 選擇 VPS 部署，如果：
- ✅ 是生產環境
- ✅ 需要高可用性
- ✅ 預算充足
- ✅ 需要完全控制

---

## 🎯 快速開始：推薦流程

### 最簡單方案（ngrok - 5分鐘）

```bash
# 1. 安裝 ngrok
curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null
echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | sudo tee /etc/apt/sources.list.d/ngrok.list
sudo apt update && sudo apt install ngrok

# 2. 註冊並配置（在 ngrok.com 獲取 token）
ngrok config add-authtoken YOUR_TOKEN

# 3. 啟動
ngrok http 80

# 4. 分享顯示的 https 地址
```

### 最佳方案（Cloudflare Tunnel - 30分鐘）

```bash
# 1. 安裝 cloudflared
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64
chmod +x cloudflared-linux-amd64
sudo mv cloudflared-linux-amd64 /usr/local/bin/cloudflared

# 2. 登入授權
cloudflared tunnel login

# 3. 創建 tunnel
cloudflared tunnel create art-history

# 4. 配置（見上文詳細步驟）

# 5. 啟動
cloudflared tunnel run art-history
```

---

## 📞 需要協助？

如果在設置過程中遇到問題，請提供：
1. 選擇的方案
2. 具體錯誤訊息
3. 系統環境資訊

我可以協助您進行詳細的設置和故障排除。
