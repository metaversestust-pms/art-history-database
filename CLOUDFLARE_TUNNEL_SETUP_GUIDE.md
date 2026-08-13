# Cloudflare Tunnel 設置指南

## 📋 當前狀態

✅ **已完成:**
- cloudflared 已下載到 `~/cloudflared-linux-amd64`
- Nginx 和 Open WebUI 運行正常
- 本地訪問測試通過

🔲 **待完成:**
- 安裝 cloudflared
- 登入 Cloudflare
- 創建和配置 Tunnel
- 設置 DNS
- 測試公網訪問

---

## 🚀 設置步驟（請按順序執行）

### 步驟 1: 安裝 cloudflared

在終端執行：

```bash
sudo mv ~/cloudflared-linux-amd64 /usr/local/bin/cloudflared
```

驗證安裝：

```bash
cloudflared version
```

應該看到版本信息，例如：`cloudflared version 2024.x.x`

---

### 步驟 2: 準備 Cloudflare 帳號和域名

#### 2.1 註冊 Cloudflare 帳號

1. 訪問：https://dash.cloudflare.com/sign-up
2. 使用 Email 或 Google 帳號註冊（**免費**）
3. 驗證 Email

#### 2.2 準備域名

**選項 A: 使用免費域名服務（最簡單）**

我推薦使用 **DuckDNS**（最簡單）：

1. 訪問：https://www.duckdns.org/
2. 使用 Google/GitHub 登入
3. 創建一個子域名，例如：`art-history.duckdns.org`
4. **重要**: DuckDNS 不需要添加到 Cloudflare
5. 記下您的域名

**選項 B: 使用 Freenom 免費域名**

1. 訪問：https://www.freenom.com/
2. 搜索可用的免費域名（.tk, .ml, .ga, .cf, .gq）
3. 註冊域名（免費，最多 12 個月）
4. 登入 Cloudflare，點擊 "Add a Site"
5. 輸入您的域名
6. 選擇 Free 方案
7. 按指示更改域名的 Name Servers 到 Cloudflare

**選項 C: 使用現有域名**

如果您已有域名：
1. 在 Cloudflare 添加域名
2. 更改域名的 DNS 到 Cloudflare
3. 等待 DNS 生效（可能需要幾分鐘）

---

### 步驟 3: 登入 Cloudflare（授權）

在終端執行：

```bash
cloudflared tunnel login
```

**會發生什麼：**
1. 終端會顯示一個 URL
2. 自動打開瀏覽器（如果沒有，請手動複製 URL 到瀏覽器）
3. 選擇您要使用的域名
4. 點擊 "Authorize"
5. 看到成功訊息

**如果使用 DuckDNS:**
- DuckDNS 不會出現在 Cloudflare 的域名列表中
- 您需要在 Cloudflare 創建一個臨時域名用於授權
- 或者使用下面的替代方案

**授權成功後：**
終端會顯示：
```
You have successfully logged in.
A certificate has been saved to: /home/YOUR_USER/.cloudflared/cert.pem
```

---

### 步驟 4: 創建 Tunnel

執行以下命令（將 `art-history` 替換為您想要的 tunnel 名稱）：

```bash
cloudflared tunnel create art-history
```

**輸出示例：**
```
Tunnel credentials written to /home/YOUR_USER/.cloudflared/TUNNEL_ID.json
Created tunnel art-history with id TUNNEL_ID
```

**重要：記下您的 Tunnel ID**（一串類似 `abc123-def456-ghi789` 的字符串）

查看您的 tunnels：

```bash
cloudflared tunnel list
```

---

### 步驟 5: 創建配置文件

創建配置文件：

```bash
mkdir -p ~/.cloudflared
nano ~/.cloudflared/config.yml
```

**使用以下模板，並替換相應的值：**

```yaml
# 替換 YOUR_TUNNEL_ID 為您在步驟 4 獲得的 Tunnel ID
tunnel: YOUR_TUNNEL_ID

# 替換 YOUR_USERNAME 為您的 Linux 用戶名
credentials-file: /home/YOUR_USERNAME/.cloudflared/YOUR_TUNNEL_ID.json

ingress:
  # AI 聊天服務 - 替換 chat.your-domain.com 為您的實際域名
  - hostname: chat.your-domain.com
    service: http://localhost:80
    originRequest:
      noTLSVerify: true
      connectTimeout: 30s
      httpHostHeader: chat.your-domain.com

  # 主網站（可選）- 替換 your-domain.com 為您的實際域名
  - hostname: your-domain.com
    service: http://localhost:80
    originRequest:
      noTLSVerify: true
      httpHostHeader: your-domain.com

  # 捕獲所有其他請求
  - service: http_status:404
```

**配置說明：**

- `tunnel`: 您的 Tunnel ID
- `credentials-file`: credentials 文件的完整路徑
- `hostname`: 您的域名（可以是子域名）
- `service`: 本地服務地址（Port 80）

**保存文件：**
- 按 `Ctrl + O` 保存
- 按 `Enter` 確認
- 按 `Ctrl + X` 退出

**驗證配置：**

```bash
cloudflared tunnel ingress validate
```

應該看到：`Configuration valid`

---

### 步驟 6: 設置 DNS 記錄

**方式 A: 使用命令行（推薦 - 適用於 Cloudflare 管理的域名）**

為您的每個 hostname 創建 DNS 記錄：

```bash
# 替換 art-history 為您的 tunnel 名稱
# 替換域名為您的實際域名

# 為聊天服務創建 DNS
cloudflared tunnel route dns art-history chat.your-domain.com

# 為主域名創建 DNS（可選）
cloudflared tunnel route dns art-history your-domain.com
```

**方式 B: 手動設置（適用於 DuckDNS 等）**

1. 登入您的 DNS 提供商（如 DuckDNS）
2. 獲取您本機的公網 IP（訪問 https://whatismyip.com/）
3. 設置 A 記錄指向您的 IP
4. **注意**: DuckDNS 會自動更新，無需手動設置

**方式 C: 使用 Cloudflare Dashboard**

1. 登入 Cloudflare Dashboard
2. 選擇您的域名
3. 進入 DNS 設置
4. 添加 CNAME 記錄：
   - Name: `chat`（或您的子域名）
   - Target: `YOUR_TUNNEL_ID.cfargotunnel.com`
   - Proxy status: Proxied（橙色雲）

---

### 步驟 7: 測試 Tunnel（前台運行）

在正式安裝為服務前，先測試：

```bash
cloudflared tunnel run art-history
```

**您應該看到：**
```
2024-XX-XX INF Starting tunnel tunnelID=YOUR_ID
2024-XX-XX INF Connection registered connIndex=0
2024-XX-XX INF Registered tunnel connection
```

**保持終端開啟，進行測試：**

1. 打開瀏覽器
2. 訪問：`https://chat.your-domain.com/chat/`
3. 應該能看到 Open WebUI 介面

**如果成功：** ✅ 繼續下一步
**如果失敗：** ❌ 查看下方「故障排除」

測試完成後，按 `Ctrl + C` 停止。

---

### 步驟 8: 安裝為系統服務（背景運行）

如果測試成功，安裝為系統服務以便自動啟動：

```bash
# 安裝服務
sudo cloudflared service install

# 啟動服務
sudo systemctl start cloudflared

# 設置開機自啟
sudo systemctl enable cloudflared

# 檢查狀態
sudo systemctl status cloudflared
```

**應該看到：**
```
● cloudflared.service - cloudflared
   Loaded: loaded
   Active: active (running)
```

---

### 步驟 9: 驗證公網訪問

從**另一台設備**或**手機**（使用行動網路，不要用 WiFi）測試：

訪問：`https://chat.your-domain.com/chat/`

**如果成功：** 🎉 恭喜！您的 Open WebUI 已可公網訪問！

---

## 🔒 步驟 10: 啟用安全認證（重要！）

在開放公網訪問後，**必須**啟用身份驗證：

### 10.1 修改配置

```bash
cd /mnt/c/Users/ssking1999/Desktop/藝術史資料庫/art-history-database
nano docker-compose.openwebui.yml
```

找到並修改：

```yaml
environment:
  - WEBUI_AUTH=true         # 改為 true
  - ENABLE_SIGNUP=false     # 改為 false（防止公開註冊）
  - DEFAULT_USER_ROLE=user
```

### 10.2 重啟服務

```bash
docker-compose -f docker-compose.openwebui.yml up -d openwebui
```

### 10.3 創建管理員帳號

首次訪問 `https://chat.your-domain.com/chat/` 時：
1. 會看到註冊頁面
2. 註冊的第一個用戶自動成為管理員
3. 之後其他人無法註冊（因為設置了 `ENABLE_SIGNUP=false`）

---

## 🔧 常用管理命令

### 查看 Tunnel 狀態

```bash
# 查看所有 tunnels
cloudflared tunnel list

# 查看服務狀態
sudo systemctl status cloudflared

# 查看日誌
sudo journalctl -u cloudflared -f
```

### 重啟 Tunnel

```bash
sudo systemctl restart cloudflared
```

### 停止 Tunnel

```bash
sudo systemctl stop cloudflared
```

### 刪除 Tunnel

```bash
# 停止服務
sudo systemctl stop cloudflared

# 刪除 tunnel
cloudflared tunnel delete art-history
```

---

## ❓ 故障排除

### 問題 1: 無法登入 Cloudflare

**症狀：** `cloudflared tunnel login` 失敗

**解決：**
```bash
# 檢查網路連接
ping cloudflare.com

# 手動打開授權 URL
# 複製終端顯示的 URL 到瀏覽器
```

---

### 問題 2: DNS 記錄創建失敗

**症狀：** `cloudflared tunnel route dns` 報錯

**解決：**
1. 確認域名已添加到 Cloudflare
2. 確認域名 DNS 已切換到 Cloudflare
3. 使用 Cloudflare Dashboard 手動添加 DNS 記錄

---

### 問題 3: Tunnel 運行但無法訪問

**檢查清單：**

```bash
# 1. 確認本地服務運行
curl http://localhost/health

# 2. 確認 tunnel 運行
sudo systemctl status cloudflared

# 3. 檢查 DNS 是否生效（可能需要幾分鐘）
nslookup chat.your-domain.com

# 4. 查看 tunnel 日誌
sudo journalctl -u cloudflared -f
```

---

### 問題 4: 502 Bad Gateway

**原因：** Tunnel 無法連接到本地服務

**解決：**
```bash
# 檢查 Nginx 是否運行
docker ps | grep nginx

# 檢查本地訪問
curl http://localhost/chat/

# 查看 Nginx 日誌
docker logs art-database-nginx

# 重啟 Nginx
docker-compose restart nginx
```

---

### 問題 5: 403 Forbidden

**原因：** Cloudflare 安全設置阻擋

**解決：**
1. 登入 Cloudflare Dashboard
2. 進入 Security > WAF
3. 檢查是否有規則阻擋
4. 添加例外規則

---

## 📊 配置範例

### 完整的 config.yml 範例

```yaml
tunnel: abc123-def456-ghi789-012345
credentials-file: /home/ssking1999/.cloudflared/abc123-def456-ghi789-012345.json

# 連接設置
warp-routing:
  enabled: false

# 入口規則
ingress:
  # AI 聊天服務
  - hostname: chat.example.com
    service: http://localhost:80
    originRequest:
      noTLSVerify: true
      connectTimeout: 30s
      tlsTimeout: 10s
      keepAliveTimeout: 90s
      httpHostHeader: chat.example.com

  # 主網站
  - hostname: example.com
    service: http://localhost:80
    originRequest:
      noTLSVerify: true
      httpHostHeader: example.com

  # 監控面板（可選）
  - hostname: monitor.example.com
    service: http://localhost:3001
    originRequest:
      noTLSVerify: true

  # 默認處理
  - service: http_status:404
```

---

## 🎓 進階配置

### 1. 添加訪問控制

在 Cloudflare Dashboard:

1. Zero Trust > Access > Applications
2. 添加新應用
3. 設置訪問規則（如 Email 白名單）

### 2. 設置 WAF 規則

1. Security > WAF
2. 創建自定義規則
3. 限制訪問來源/頻率

### 3. 啟用 Analytics

1. Analytics > Traffic
2. 查看訪問統計
3. 監控流量

---

## ✅ 最終檢查清單

設置完成後確認：

- [ ] cloudflared 已安裝並運行
- [ ] Tunnel 已創建並配置
- [ ] DNS 記錄已設置
- [ ] 可通過公網域名訪問
- [ ] 已啟用身份驗證
- [ ] 已創建管理員帳號
- [ ] 服務設置為開機自啟
- [ ] 已測試從外網訪問

---

## 🎉 完成！

您的訪問地址：
- **AI 聊天**: `https://chat.your-domain.com/chat/`
- **主頁**: `https://your-domain.com/`

分享給其他人即可使用！

---

## 📞 需要幫助？

如遇問題：

1. 查看日誌：`sudo journalctl -u cloudflared -f`
2. 檢查本地服務：`docker ps`
3. 測試本地訪問：`curl http://localhost/chat/`
4. 參考官方文檔：https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/

---

**下一步：開始步驟 1，安裝 cloudflared！** 🚀
