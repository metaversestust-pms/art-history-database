# WSL2 環境下的 OpenWebUI + Ollama RAG Proxy 配置

**環境**: Windows Subsystem for Linux 2 (WSL2)
**問題**: Docker 容器無法解析 `host.docker.internal`
**解決方案**: 使用 WSL2 的實際 IP 地址

---

## 🔍 問題說明

在 WSL2 環境下，Docker Desktop 的 `host.docker.internal` 功能可能無法正常工作，導致 OpenWebUI 容器無法連接到宿主機上運行的 Ollama RAG Proxy。

### 錯誤表現

```bash
# 在容器內測試連接失敗
docker exec art-history-openwebui curl http://host.docker.internal:11435/health
# 返回: Error 或無回應
```

---

## ✅ 解決方案

### 步驟 1: 獲取 WSL2 IP 地址

```bash
ip addr show eth0 | grep "inet " | awk '{print $2}' | cut -d/ -f1
```

**示例輸出**: `172.26.104.197`

### 步驟 2: 使用 WSL2 IP 啟動 OpenWebUI

```bash
# 停止並刪除舊容器
docker stop art-history-openwebui
docker rm art-history-openwebui

# 獲取 WSL2 IP
WSL_IP=$(ip addr show eth0 | grep "inet " | awk '{print $2}' | cut -d/ -f1)

# 使用 WSL IP 啟動 OpenWebUI
docker run -d \
  --name art-history-openwebui \
  --restart always \
  -p 8080:8080 \
  -e OLLAMA_BASE_URL=http://${WSL_IP}:11435 \
  -e WEBUI_AUTH=false \
  -v open-webui:/app/backend/data \
  ghcr.io/open-webui/open-webui:main
```

### 步驟 3: 驗證連接

```bash
# 等待容器啟動
sleep 10

# 測試從容器內訪問 Proxy
WSL_IP=$(ip addr show eth0 | grep "inet " | awk '{print $2}' | cut -d/ -f1)
docker exec art-history-openwebui curl -s http://${WSL_IP}:11435/health

# 應該返回:
# {"status":"ok","service":"ollama-rag-proxy",...}
```

---

## 🔧 自動化腳本

創建一個自動獲取 WSL IP 並啟動 OpenWebUI 的腳本：

```bash
#!/bin/bash
# restart-openwebui-wsl2.sh

echo "🔍 獲取 WSL2 IP 地址..."
WSL_IP=$(ip addr show eth0 | grep "inet " | awk '{print $2}' | cut -d/ -f1)
echo "   WSL2 IP: $WSL_IP"

echo ""
echo "🛑 停止現有 OpenWebUI 容器..."
docker stop art-history-openwebui 2>/dev/null
docker rm art-history-openwebui 2>/dev/null

echo ""
echo "🚀 啟動 OpenWebUI（使用 WSL2 IP）..."
docker run -d \
  --name art-history-openwebui \
  --restart always \
  -p 8080:8080 \
  -e OLLAMA_BASE_URL=http://${WSL_IP}:11435 \
  -e WEBUI_AUTH=false \
  -v open-webui:/app/backend/data \
  ghcr.io/open-webui/open-webui:main

echo ""
echo "⏳ 等待容器啟動..."
sleep 10

echo ""
echo "✅ 驗證連接..."
docker exec art-history-openwebui curl -s http://${WSL_IP}:11435/health > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo "   ✅ OpenWebUI 成功連接到 Ollama RAG Proxy！"
    echo ""
    echo "🎉 配置完成！"
    echo "   訪問: http://localhost:8080"
else
    echo "   ❌ 連接失敗，請檢查 Ollama RAG Proxy 是否運行"
    echo ""
    echo "   檢查命令:"
    echo "   curl http://localhost:11435/health"
fi

echo ""
echo "📊 當前配置:"
echo "   WSL2 IP: $WSL_IP"
echo "   OLLAMA_BASE_URL: http://${WSL_IP}:11435"
echo ""
```

保存為 `restart-openwebui-wsl2.sh` 並執行：

```bash
bash restart-openwebui-wsl2.sh
```

---

## 📝 注意事項

### WSL2 IP 地址會變動

**重要**: WSL2 的 IP 地址在每次 WSL 重啟後可能會改變！

**影響**: 如果 WSL 重啟後，OpenWebUI 可能無法連接到 Ollama RAG Proxy

**解決方案**:

1. **每次 WSL 重啟後重新啟動 OpenWebUI**:
   ```bash
   bash restart-openwebui-wsl2.sh
   ```

2. **或者使用網絡模式 `--network host`** (僅限 Linux Docker):
   ```bash
   # 注意: host 模式在 Windows Docker Desktop 上可能不可用
   docker run -d \
     --name art-history-openwebui \
     --restart always \
     --network host \
     -e OLLAMA_BASE_URL=http://localhost:11435 \
     -e WEBUI_AUTH=false \
     -v open-webui:/app/backend/data \
     ghcr.io/open-webui/open-webui:main
   ```

### 防火牆設置

確保 WSL2 防火牆允許端口 11435 的連接：

```bash
# 檢查端口是否可訪問
netstat -tuln | grep 11435

# 如果需要，添加防火牆規則（Windows 端）
# 在 PowerShell (管理員) 中運行:
# New-NetFirewallRule -DisplayName "Ollama RAG Proxy" -Direction Inbound -Action Allow -Protocol TCP -LocalPort 11435
```

---

## 🧪 完整測試流程

### 1. 檢查所有服務

```bash
echo "檢查 Ollama RAG Proxy..."
curl -s http://localhost:11435/health

echo ""
echo "檢查 Multi-DB RAG Server..."
curl -s http://localhost:8010/health

echo ""
echo "檢查 OpenWebUI..."
curl -s http://localhost:8080 > /dev/null && echo "✅ 運行正常" || echo "❌ 無法訪問"
```

### 2. 測試容器內連接

```bash
WSL_IP=$(ip addr show eth0 | grep "inet " | awk '{print $2}' | cut -d/ -f1)

echo "從容器內測試 Proxy 連接..."
docker exec art-history-openwebui curl -s http://${WSL_IP}:11435/health

echo ""
echo "從容器內獲取模型列表..."
docker exec art-history-openwebui curl -s http://${WSL_IP}:11435/api/tags | grep -o '"name":"[^"]*-vector_rag"' | head -3
```

### 3. 在瀏覽器中測試

1. 訪問: http://localhost:8080
2. 點擊新對話
3. 在模型下拉菜單中查找 RAG 組合模型
4. 選擇 `llama3.1-vector_rag` 並提問

---

## 🔄 常見問題與解決方案

### 問題 1: WSL 重啟後 OpenWebUI 無法連接

**症狀**: 選擇 RAG 模型後沒有回應或錯誤

**原因**: WSL2 IP 地址改變

**解決**:
```bash
# 重新啟動 OpenWebUI
bash restart-openwebui-wsl2.sh
```

### 問題 2: 容器無法解析主機名

**症狀**: `curl: (6) Could not resolve host`

**原因**: DNS 配置問題

**解決**:
```bash
# 使用 IP 地址而非主機名
# 不要使用: host.docker.internal
# 使用: 172.26.x.x (實際 WSL IP)
```

### 問題 3: 端口被佔用

**症狀**: `port is already allocated`

**原因**: 端口 8080 被其他程序使用

**解決**:
```bash
# 查找佔用端口的進程
netstat -tuln | grep 8080

# 或使用不同端口
docker run -d \
  --name art-history-openwebui \
  -p 8081:8080 \  # 使用 8081 而非 8080
  ...
```

---

## 📚 相關資源

- **WSL2 網絡文檔**: https://docs.microsoft.com/en-us/windows/wsl/networking
- **Docker Desktop WSL2 集成**: https://docs.docker.com/desktop/wsl/
- **OpenWebUI 文檔**: https://docs.openwebui.com/

---

## ✅ 總結

在 WSL2 環境下運行 OpenWebUI + Ollama RAG Proxy 的關鍵是：

1. ✅ 使用 WSL2 的實際 IP 地址（而非 `host.docker.internal`）
2. ✅ 在 WSL 重啟後重新配置 OpenWebUI
3. ✅ 使用自動化腳本簡化配置過程

**當前配置**:
- WSL2 IP: `172.26.104.197` (您的實際 IP)
- OLLAMA_BASE_URL: `http://172.26.104.197:11435`
- OpenWebUI: http://localhost:8080

**準備就緒！** 🎉
