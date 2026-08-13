# Open WebUI 公網訪問完整指南

## 📚 文檔索引

| 文檔 | 說明 | 適用對象 |
|------|------|----------|
| **QUICK_START_PUBLIC_ACCESS.md** | 快速開始指南 | 想要快速上手 |
| **PUBLIC_ACCESS_GUIDE.md** | 詳細技術文檔 | 需要深入了解 |
| **NGINX_SETUP.md** | Nginx 配置說明 | 已完成基礎設置 |

## 🎯 您現在的狀態

✅ **已完成:**
- Nginx 反向代理配置
- Open WebUI 本地運行
- 區域網路訪問

🔲 **下一步:**
- 選擇公網訪問方案
- 設置安全認證
- 分享給使用者

---

## ⚡ 兩種方案快速對比

### 方案 A: ngrok（推薦新手）

```bash
# 1. 運行自動化腳本
cd /mnt/c/Users/ssking1999/Desktop/藝術史資料庫/art-history-database
bash scripts/setup-ngrok.sh

# 2. 獲得公網地址（例如）
https://abc123.ngrok.io/chat/
```

**時間:** 5 分鐘
**難度:** ⭐ 簡單
**費用:** 免費
**穩定性:** 適合測試

---

### 方案 B: Cloudflare Tunnel（推薦長期使用）

```bash
# 1. 運行自動化腳本
cd /mnt/c/Users/ssking1999/Desktop/藝術史資料庫/art-history-database
bash scripts/setup-cloudflare-tunnel.sh

# 2. 使用自己的域名
https://chat.your-domain.com/chat/
```

**時間:** 30 分鐘
**難度:** ⭐⭐ 中等
**費用:** 免費
**穩定性:** 適合生產環境

---

## 🚦 決策流程圖

```
開始
  ↓
是否只是測試/演示？
  ├─ 是 → 使用 ngrok
  │         ↓
  │       5分鐘完成
  │
  └─ 否 → 是否有域名或願意註冊？
            ├─ 是 → 使用 Cloudflare Tunnel
            │         ↓
            │       30分鐘完成，長期穩定
            │
            └─ 否 → 先用 ngrok 測試
                      ↓
                    後續升級到 Cloudflare
```

---

## 📋 設置前檢查清單

### 系統檢查

```bash
# 1. 確認本地服務運行正常
docker ps | grep -E "nginx|openwebui"

# 應該看到兩個容器都在運行

# 2. 測試本地訪問
curl http://localhost/health
# 應該返回: healthy

curl -I http://localhost/chat/
# 應該返回: HTTP/1.1 200 OK

# 3. 瀏覽器測試
# 訪問 http://localhost/ 應該看到首頁
# 訪問 http://localhost/chat/ 應該看到 Open WebUI 介面
```

如果以上測試都通過，您就可以開始設置公網訪問了！

---

## 🎬 快速開始（選擇一個）

### 選項 1: 使用 ngrok（最快）

```bash
# 一鍵執行
cd /mnt/c/Users/ssking1999/Desktop/藝術史資料庫/art-history-database
bash scripts/setup-ngrok.sh
```

**需要準備:**
1. 訪問 https://ngrok.com 註冊帳號（支援 Google 登入）
2. 複製您的 authtoken
3. 運行腳本時貼上

**完成後:**
- 獲得公網地址: `https://xxx.ngrok.io`
- 分享地址: `https://xxx.ngrok.io/chat/`
- 任何人都可以訪問

---

### 選項 2: 使用 Cloudflare Tunnel（推薦）

```bash
# 一鍵執行
cd /mnt/c/Users/ssking1999/Desktop/藝術史資料庫/art-history-database
bash scripts/setup-cloudflare-tunnel.sh
```

**需要準備:**
1. Cloudflare 帳號（免費註冊: https://dash.cloudflare.com/sign-up）
2. 一個域名（可使用免費域名服務）
   - [Freenom](https://www.freenom.com/) - 免費 .tk/.ml 域名
   - [DuckDNS](https://www.duckdns.org/) - 免費動態 DNS

**完成後:**
- 擁有固定域名: `https://chat.your-domain.com`
- 自動 HTTPS 加密
- 永久穩定訪問

---

## 🔐 安全設置（重要！）

公網訪問前，**必須**啟用身份驗證：

### 步驟 1: 啟用認證

編輯文件:
```bash
nano /mnt/c/Users/ssking1999/Desktop/藝術史資料庫/art-history-database/docker-compose.openwebui.yml
```

找到並修改:
```yaml
environment:
  - WEBUI_AUTH=true         # 改為 true
  - ENABLE_SIGNUP=false     # 改為 false（防止任意註冊）
```

### 步驟 2: 重啟服務

```bash
cd /mnt/c/Users/ssking1999/Desktop/藝術史資料庫/art-history-database
docker-compose -f docker-compose.openwebui.yml up -d openwebui
```

### 步驟 3: 創建管理員帳號

首次訪問 Open WebUI 時註冊的用戶會自動成為管理員。

或者通過環境變數設置:
```yaml
environment:
  - WEBUI_AUTH=true
  - ENABLE_SIGNUP=true
  - DEFAULT_USER_ROLE=pending  # 新用戶需管理員批准
```

---

## 📊 功能對比表

| 功能 | 區域網路訪問 | ngrok | Cloudflare Tunnel |
|------|-------------|-------|-------------------|
| **訪問範圍** | 同網路 | 全球 | 全球 |
| **設置時間** | 已完成 | 5分鐘 | 30分鐘 |
| **費用** | 免費 | 免費 | 免費 |
| **HTTPS** | ❌ | ✅ | ✅ |
| **固定URL** | ✅ | ❌ | ✅ |
| **連線限制** | ❌ | ✅ | ❌ |
| **DDoS防護** | ❌ | ⚠️ | ✅ |
| **適用場景** | 測試 | 演示 | 生產 |

---

## 🛠️ 常用命令

### 查看服務狀態
```bash
# 檢查所有服務
docker ps | grep -E "nginx|openwebui|ollama"

# 檢查 Nginx 日誌
docker logs art-database-nginx -f

# 檢查 Open WebUI 日誌
docker logs art-history-openwebui -f
```

### 重啟服務
```bash
# 重啟 Nginx
docker-compose restart nginx

# 重啟 Open WebUI
docker-compose -f docker-compose.openwebui.yml restart openwebui
```

### 停止服務
```bash
# 停止 ngrok
pkill ngrok

# 停止 Cloudflare Tunnel
sudo systemctl stop cloudflared

# 停止所有服務
docker-compose down
docker-compose -f docker-compose.openwebui.yml down
```

---

## 🎓 學習資源

### 官方文檔
- [Open WebUI 文檔](https://docs.openwebui.com/)
- [ngrok 文檔](https://ngrok.com/docs)
- [Cloudflare Tunnel 文檔](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/)

### 視頻教程
- [ngrok 快速入門](https://www.youtube.com/results?search_query=ngrok+tutorial)
- [Cloudflare Tunnel 教學](https://www.youtube.com/results?search_query=cloudflare+tunnel)

---

## ❓ 疑難排解

### 問題 1: 本地無法訪問
```bash
# 檢查服務狀態
docker ps

# 重啟服務
docker-compose restart nginx
docker-compose -f docker-compose.openwebui.yml restart openwebui
```

### 問題 2: ngrok 連不上
```bash
# 檢查 authtoken 是否正確
ngrok config check

# 重新配置
ngrok config add-authtoken YOUR_TOKEN
```

### 問題 3: Cloudflare Tunnel 無法連接
```bash
# 檢查本地服務
curl http://localhost/health

# 查看 tunnel 狀態
cloudflared tunnel list

# 查看日誌
cloudflared tunnel run your-tunnel-name
```

### 問題 4: 訪問速度慢
- ngrok: 在配置中指定 region (ap 為亞太)
- Cloudflare: 自動選擇最近節點，無需配置

---

## 📈 升級路徑

### 階段 1: 本地測試（已完成）
- ✅ 區域網路訪問
- ✅ 功能驗證

### 階段 2: 公網測試（推薦 ngrok）
- 🔲 快速設置
- 🔲 小範圍分享
- 🔲 收集反饋

### 階段 3: 正式部署（推薦 Cloudflare Tunnel）
- 🔲 固定域名
- 🔲 啟用所有安全功能
- 🔲 設置監控

### 階段 4: 生產優化（可選）
- 🔲 部署到 VPS
- 🔲 設置備份
- 🔲 負載均衡

---

## 💪 進階配置

### 自定義域名
- ngrok 付費版支援
- Cloudflare Tunnel 免費支援

### 多用戶管理
- 在 Open WebUI 後台管理用戶
- 設置用戶角色和權限

### 使用量監控
- 使用 Grafana 查看系統指標
- 訪問 http://localhost:3001

### 數據備份
```bash
# 備份 Open WebUI 數據
docker run --rm -v art-history-database_openwebui_data:/data \
  -v $(pwd):/backup ubuntu \
  tar czf /backup/openwebui-backup-$(date +%Y%m%d).tar.gz /data
```

---

## ✅ 完成檢查清單

### 基礎設置
- [x] Nginx 運行正常
- [x] Open WebUI 運行正常
- [x] 本地訪問成功

### 公網訪問
- [ ] 選擇訪問方案
- [ ] 運行設置腳本
- [ ] 測試公網訪問

### 安全加固
- [ ] 啟用身份驗證
- [ ] 創建管理員帳號
- [ ] 關閉公開註冊
- [ ] 測試登入功能

### 分享使用
- [ ] 記錄訪問地址
- [ ] 分享給使用者
- [ ] 提供使用說明
- [ ] 設置使用監控

---

## 🎉 總結

您現在有三種訪問方式：

1. **本地訪問**: http://localhost/chat/ （本機）
2. **區域網路**: http://您的IP/chat/ （同網路）
3. **公網訪問**:
   - ngrok: https://xxx.ngrok.io/chat/ （臨時）
   - Cloudflare: https://chat.your-domain.com/chat/ （永久）

選擇適合您的方案，運行對應的設置腳本即可！

---

## 📞 獲取幫助

如遇問題：

1. **查看日誌**:
   ```bash
   docker logs art-database-nginx
   docker logs art-history-openwebui
   ```

2. **檢查文檔**:
   - 查看 PUBLIC_ACCESS_GUIDE.md
   - 查看 NGINX_SETUP.md

3. **常見問題**:
   - 參考上方「疑難排解」章節

**開始您的公網部署之旅吧！** 🚀
