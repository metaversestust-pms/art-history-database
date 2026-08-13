# 快速開始：公網訪問設置

## 🎯 目標

讓不同網路、不同地區的人都能訪問您的 Open WebUI。

## 📋 方案選擇

### 方案 1: ngrok（最快 - 5分鐘）⚡

**適合:** 快速測試、臨時分享、演示用途

**執行:**
```bash
cd /mnt/c/Users/ssking1999/Desktop/藝術史資料庫/art-history-database
bash scripts/setup-ngrok.sh
```

**步驟:**
1. 訪問 [ngrok.com](https://ngrok.com) 註冊帳號
2. 複製您的 authtoken
3. 運行上述腳本，按提示輸入 authtoken
4. 獲得公網地址，例如: `https://abc123.ngrok.io`
5. 分享地址: `https://abc123.ngrok.io/chat/`

**優點:** ✅ 超快速設置 ✅ 自動 HTTPS ✅ 免費
**缺點:** ❌ URL 會變動 ❌ 有連線限制

---

### 方案 2: Cloudflare Tunnel（推薦 - 30分鐘）⭐

**適合:** 長期使用、正式服務、需要穩定性

**前置準備:**
- 註冊 [Cloudflare](https://dash.cloudflare.com/sign-up) 帳號
- 準備一個域名（可使用免費域名服務）

**執行:**
```bash
cd /mnt/c/Users/ssking1999/Desktop/藝術史資料庫/art-history-database
bash scripts/setup-cloudflare-tunnel.sh
```

**免費域名服務推薦:**
- [Freenom](https://www.freenom.com/) - .tk, .ml, .ga 等
- [DuckDNS](https://www.duckdns.org/) - 簡單易用

**優點:** ✅ 完全免費 ✅ 穩定可靠 ✅ 自動 HTTPS ✅ DDoS 防護
**缺點:** ❌ 需要域名 ❌ 設置稍複雜

---

## 🚀 最快速方案（2分鐘）

如果您想立即測試，無需安裝任何東西：

### 使用 ngrok 網頁版

```bash
# 1. 運行以下命令
docker run -it -e NGROK_AUTHTOKEN=YOUR_TOKEN ngrok/ngrok http host.docker.internal:80

# 2. 在 ngrok.com 註冊後替換 YOUR_TOKEN
# 3. 查看輸出的公網地址
```

---

## 📊 詳細比較

| 特性 | ngrok | Cloudflare Tunnel |
|------|-------|-------------------|
| 設置時間 | 5 分鐘 | 30 分鐘 |
| 費用 | 免費/付費 | 完全免費 |
| URL 穩定性 | 會變動 | 固定域名 |
| 速度 | 快 | 很快 |
| 安全性 | 好 | 優秀 |
| 連線限制 | 有（免費版） | 無 |
| 適用場景 | 測試/演示 | 長期使用 |

---

## 🔧 手動快速設置（無需腳本）

### ngrok 手動設置

```bash
# 1. 安裝 ngrok
curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null
echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | sudo tee /etc/apt/sources.list.d/ngrok.list
sudo apt update && sudo apt install ngrok

# 2. 配置 authtoken（從 ngrok.com 獲取）
ngrok config add-authtoken YOUR_AUTH_TOKEN

# 3. 啟動
ngrok http 80

# 4. 查看輸出的公網地址
```

### Cloudflare Tunnel 手動設置

```bash
# 1. 安裝 cloudflared
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64
chmod +x cloudflared-linux-amd64
sudo mv cloudflared-linux-amd64 /usr/local/bin/cloudflared

# 2. 登入（會打開瀏覽器）
cloudflared tunnel login

# 3. 創建 tunnel
cloudflared tunnel create my-tunnel

# 4. 配置（創建 ~/.cloudflared/config.yml）
# 詳見 PUBLIC_ACCESS_GUIDE.md

# 5. 設置 DNS
cloudflared tunnel route dns my-tunnel chat.your-domain.com

# 6. 啟動
cloudflared tunnel run my-tunnel
```

---

## 🔒 重要安全建議

在開放公網訪問前，**強烈建議**啟用身份驗證：

### 1. 啟用 Open WebUI 認證

編輯 `docker-compose.openwebui.yml`:

```yaml
environment:
  - WEBUI_AUTH=true        # 開啟認證
  - ENABLE_SIGNUP=false    # 關閉公開註冊
```

重啟服務:
```bash
docker-compose -f docker-compose.openwebui.yml up -d openwebui
```

### 2. 創建管理員帳號

```bash
# 方法 1: 通過網頁（首次訪問）
# 訪問 Open WebUI，第一個註冊的用戶自動成為管理員

# 方法 2: 設置預設管理員（在 docker-compose.openwebui.yml）
environment:
  - WEBUI_AUTH=true
  - ENABLE_SIGNUP=true
  - DEFAULT_USER_ROLE=pending  # 新用戶需要管理員批准
```

### 3. 定期更新

```bash
# 更新 Open WebUI
docker-compose -f docker-compose.openwebui.yml pull
docker-compose -f docker-compose.openwebui.yml up -d
```

---

## ❓ 常見問題

### Q1: ngrok 顯示 "too many connections"
**A:** 免費版有連線數限制。升級到付費版或使用 Cloudflare Tunnel。

### Q2: Cloudflare Tunnel 無法連接
**A:**
- 檢查本地服務是否運行: `curl http://localhost/chat/`
- 查看 tunnel 日誌: `cloudflared tunnel run my-tunnel`
- 等待 DNS 生效（可能需要幾分鐘）

### Q3: 訪問速度慢
**A:**
- ngrok: 選擇合適的 region（ap 為亞太地區）
- Cloudflare: 已自動優化，無需設置

### Q4: URL 被防火牆封鎖
**A:**
- Cloudflare Tunnel 更不容易被封鎖
- 可以嘗試使用自定義域名

### Q5: 如何停止服務
**A:**
```bash
# ngrok: 按 Ctrl+C 或
pkill ngrok

# Cloudflare Tunnel:
sudo systemctl stop cloudflared
```

---

## 📝 下一步

設置完成後：

1. ✅ **測試訪問** - 確保服務正常運行
2. ✅ **啟用認證** - 保護您的服務
3. ✅ **分享地址** - 將地址發送給使用者
4. ✅ **監控使用** - 查看訪問日誌

### 監控命令

```bash
# 查看 Nginx 訪問日誌
docker logs art-database-nginx -f

# 查看 Open WebUI 日誌
docker logs art-history-openwebui -f

# 查看系統資源
docker stats
```

---

## 💡 專業建議

### 測試階段（1-7天）
- 使用 **ngrok**
- 快速驗證功能
- 收集用戶反饋

### 正式使用（長期）
- 切換到 **Cloudflare Tunnel**
- 啟用所有安全功能
- 設置監控和備份

---

## 📞 需要幫助？

1. 查看詳細文檔: `PUBLIC_ACCESS_GUIDE.md`
2. 查看 ngrok 文檔: https://ngrok.com/docs
3. 查看 Cloudflare 文檔: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/

---

## ✅ 檢查清單

設置前：
- [ ] 確認本地服務正常運行
- [ ] 測試本地訪問 http://localhost/chat/
- [ ] 決定使用哪種方案

設置中：
- [ ] 按步驟執行腳本
- [ ] 記錄 authtoken/tunnel ID
- [ ] 保存配置文件

設置後：
- [ ] 測試公網訪問
- [ ] 啟用身份驗證
- [ ] 創建管理員帳號
- [ ] 分享訪問地址
- [ ] 設置監控

---

**開始吧！選擇一個方案並執行對應的腳本。** 🚀
