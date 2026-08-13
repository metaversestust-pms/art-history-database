# Cloudflare Tunnel 快速參考

## 📋 設置流程概覽

```
1. 安裝 cloudflared (5分鐘)
   ↓
2. 準備 Cloudflare 帳號和域名 (5-10分鐘)
   ↓
3. 登入並授權 (2分鐘)
   ↓
4. 創建 Tunnel (2分鐘)
   ↓
5. 配置 config.yml (5分鐘)
   ↓
6. 設置 DNS (2分鐘)
   ↓
7. 測試運行 (3分鐘)
   ↓
8. 安裝為服務 (2分鐘)
   ↓
9. 啟用安全認證 (3分鐘)
   ↓
✅ 完成！
```

**總計時間：約 30 分鐘**

---

## 🚀 快速命令

### 步驟 1: 安裝
```bash
sudo mv ~/cloudflared-linux-amd64 /usr/local/bin/cloudflared
cloudflared version
```

### 步驟 2: 登入
```bash
cloudflared tunnel login
# 會打開瀏覽器，授權後回到終端
```

### 步驟 3: 創建 Tunnel
```bash
cloudflared tunnel create art-history
cloudflared tunnel list  # 查看並記下 Tunnel ID
```

### 步驟 4: 配置文件
```bash
mkdir -p ~/.cloudflared
nano ~/.cloudflared/config.yml
```

**模板（替換標記的值）：**
```yaml
tunnel: YOUR_TUNNEL_ID
credentials-file: /home/YOUR_USERNAME/.cloudflared/YOUR_TUNNEL_ID.json

ingress:
  - hostname: chat.your-domain.com
    service: http://localhost:80
    originRequest:
      noTLSVerify: true
  - hostname: your-domain.com
    service: http://localhost:80
  - service: http_status:404
```

**驗證：**
```bash
cloudflared tunnel ingress validate
```

### 步驟 5: 設置 DNS
```bash
cloudflared tunnel route dns art-history chat.your-domain.com
cloudflared tunnel route dns art-history your-domain.com
```

### 步驟 6: 測試
```bash
cloudflared tunnel run art-history
# 保持運行，訪問 https://chat.your-domain.com/chat/
# 測試成功後按 Ctrl+C 停止
```

### 步驟 7: 安裝為服務
```bash
sudo cloudflared service install
sudo systemctl start cloudflared
sudo systemctl enable cloudflared
sudo systemctl status cloudflared
```

### 步驟 8: 啟用認證
```bash
cd /mnt/c/Users/ssking1999/Desktop/藝術史資料庫/art-history-database
nano docker-compose.openwebui.yml
# 改：WEBUI_AUTH=true 和 ENABLE_SIGNUP=false
docker-compose -f docker-compose.openwebui.yml up -d openwebui
```

---

## 🔧 常用管理命令

```bash
# 查看狀態
sudo systemctl status cloudflared

# 查看日誌
sudo journalctl -u cloudflared -f

# 重啟服務
sudo systemctl restart cloudflared

# 停止服務
sudo systemctl stop cloudflared

# 列出所有 tunnels
cloudflared tunnel list

# 測試配置
cloudflared tunnel ingress validate
```

---

## 🆓 免費域名選項

### 選項 1: DuckDNS（最簡單）
1. 訪問：https://www.duckdns.org/
2. 用 Google 登入
3. 創建子域名：`art-history.duckdns.org`
4. **注意**: 需要定期更新 IP（DuckDNS 提供腳本）

### 選項 2: Freenom
1. 訪問：https://www.freenom.com/
2. 搜索域名（.tk, .ml, .ga, .cf, .gq）
3. 註冊免費域名（12個月）
4. 添加到 Cloudflare

### 選項 3: No-IP
1. 訪問：https://www.noip.com/
2. 註冊免費帳號
3. 創建 hostname

---

## ⚠️ 重要提醒

### 安全設置
- ✅ **必須**啟用 `WEBUI_AUTH=true`
- ✅ **必須**設置 `ENABLE_SIGNUP=false`
- ✅ 首次訪問立即創建管理員帳號
- ✅ 定期更新 Docker 映像

### DNS 生效時間
- Cloudflare DNS 通常 1-5 分鐘生效
- 某些地區可能需要 10-30 分鐘
- 可用 `nslookup your-domain.com` 檢查

### 防火牆
- Cloudflare Tunnel **不需要**開放任何端口
- 所有流量通過加密隧道
- 無需配置路由器端口轉發

---

## 📊 配置變量對照表

| 需要替換的變量 | 說明 | 範例 |
|--------------|------|------|
| `YOUR_TUNNEL_ID` | tunnel create 時獲得的 ID | `abc123-def456-ghi789` |
| `YOUR_USERNAME` | Linux 用戶名 | `ssking1999` |
| `your-domain.com` | 您的域名 | `example.com` 或 `art.duckdns.org` |
| `chat.your-domain.com` | 聊天服務子域名 | `chat.example.com` |

---

## 🎯 檢查清單

### 安裝前
- [ ] 已註冊 Cloudflare 帳號
- [ ] 已準備域名
- [ ] 本地服務運行正常（`curl http://localhost/health`）

### 安裝中
- [ ] cloudflared 安裝成功（`cloudflared version`）
- [ ] 已登入授權（`.cloudflared/cert.pem` 存在）
- [ ] Tunnel 已創建（`cloudflared tunnel list`）
- [ ] config.yml 已配置並驗證通過
- [ ] DNS 記錄已創建

### 安裝後
- [ ] 測試運行成功
- [ ] 服務已安裝並啟動
- [ ] 可從外網訪問
- [ ] 已啟用身份驗證
- [ ] 已創建管理員帳號

---

## 🐛 快速故障排除

### 無法訪問？
```bash
# 1. 檢查本地
curl http://localhost/health

# 2. 檢查 tunnel
sudo systemctl status cloudflared

# 3. 檢查 DNS
nslookup chat.your-domain.com

# 4. 查看日誌
sudo journalctl -u cloudflared -f
```

### 502 錯誤？
```bash
# 檢查 Nginx
docker ps | grep nginx

# 重啟 Nginx
docker-compose restart nginx
```

### 403 錯誤？
- 檢查 Cloudflare WAF 規則
- 暫時關閉 WAF 測試

---

## 📱 訪問地址

設置完成後，您的服務可通過以下地址訪問：

- **AI 聊天**: `https://chat.your-domain.com/chat/`
- **主頁**: `https://your-domain.com/`
- **健康檢查**: `https://your-domain.com/health`

分享給任何人都可以訪問！

---

## 📚 詳細文檔

需要更多細節？查看：
- **完整指南**: `CLOUDFLARE_TUNNEL_SETUP_GUIDE.md`
- **公網訪問**: `PUBLIC_ACCESS_GUIDE.md`
- **Nginx 配置**: `NGINX_SETUP.md`

---

**準備好了嗎？從步驟 1 開始！** 🚀
