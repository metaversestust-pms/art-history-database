# 📝 如何更新 OpenWebUI Function 為 v4.1

您的 OpenWebUI 運行在 **http://localhost:8080**，但是我們更新的代碼需要手動上傳到 OpenWebUI 界面。

## 🎯 快速更新步驟

### 方法 1：網頁界面更新（推薦，最簡單）

1. **打開 OpenWebUI**
   ```
   http://localhost:8080
   ```

2. **登入後，點擊左側菜單**
   - 找到 "Workspace" 或"工作區"
   - 點擊 "Functions" 或"功能"

3. **找到現有的藝術史 Function**
   - 應該會看到 "藝術史 RAG+LLM 完整智能組合系統 v4.0"
   - 點擊它進入編輯模式

4. **複製新代碼**
   - 打開文件：`enhanced_openwebui_rag_function_v4.py`
   - 全選並複製所有內容（Ctrl+A, Ctrl+C）

5. **貼上並保存**
   - 在 OpenWebUI Function 編輯器中，刪除舊代碼
   - 貼上新代碼（Ctrl+V）
   - 點擊 "Save" 或"保存"按鈕

6. **驗證更新**
   - 標題應該顯示: "藝術史 RAG+LLM 完整智能組合系統 v4.1"
   - 描述應該提到: "整合Neo4j+ChromaDB雙資料庫"

7. **測試**
   - 回到聊天界面
   - 選擇任一模型（例如: Llama 3.1 8B + Vector RAG）
   - 現在應該會看到策略名稱中包含資料庫信息
   - 例如: "🔍 Vector RAG (ChromaDB優先)"

---

## 🔍 如何驗證更新成功

更新後，您應該能在以下地方看到變化：

### 1. 策略名稱顯示資料庫
**更新前**:
- 🔍 Vector RAG

**更新後**:
- 🔍 Vector RAG (ChromaDB優先) 🆕

### 2. 執行信息顯示詳細來源
**更新前**:
```
📊 執行信息
- 🤖 LLM模型: llama3.1:8b
- 🔍 RAG策略: vector_only
- 🌐 服務器: 標準 (port 8008)
```

**更新後**:
```
📊 執行信息
- 🤖 LLM模型: llama3.1:8b
- 🔍 RAG策略: vector_only
- 🌐 服務器: 多資料庫 (port 8010)
- 💾 主要資料庫: CHROMADB
- 📊 資料源分布: chromadb: 3個
```

### 3. 參考資料顯示完整來源
**更新前**:
```
📚 參考資料
1. 作品內容... (相關度: 0.85, 方法: vector)
```

**更新後**:
```
📚 參考資料

[1] 作品內容...
   📊 來源: CHROMADB > Met Museum API
   🎯 相關度: 0.85 | 檢索方法: vector

[2] 藝術家資訊...
   📊 來源: NEO4J > Internal Knowledge Base
   🎯 相關度: 0.82 | 檢索方法: fulltext
```

---

## ❓ 常見問題

### Q1: 我找不到 Functions 選項在哪裡？

**A**: 依序點擊：
1. 左側菜單欄
2. 找到齒輪圖示（設置）或 "Workspace"
3. 應該會看到 "Functions" 或 "Tools" 選項

### Q2: 我更新了但是沒有看到變化？

**A**: 請嘗試：
1. 重新整理頁面（F5）
2. 清除瀏覽器快取（Ctrl+Shift+Delete）
3. 重新選擇模型組合

### Q3: 多資料庫服務器顯示不可用？

**A**: 檢查服務器是否運行：
```bash
curl http://localhost:8010/health
```

如果沒有回應，啟動服務器：
```bash
node multi-database-rag-server.js > multi-database-rag-server.log 2>&1 &
```

### Q4: 我想要回到舊版本怎麼辦？

**A**: OpenWebUI 通常會保存 Function 的歷史版本，您可以：
1. 在 Function 編輯頁面找到"版本歷史"
2. 選擇之前的版本恢復

---

## 📋 更新檢查清單

使用這個清單確保更新成功：

- [ ] 已登入 OpenWebUI (http://localhost:8080)
- [ ] 已找到 Functions 管理頁面
- [ ] 已找到現有的藝術史 Function
- [ ] 已複製 `enhanced_openwebui_rag_function_v4.py` 的全部內容
- [ ] 已在 OpenWebUI 中貼上新代碼
- [ ] 已保存更新
- [ ] 版本號已更新為 v4.1
- [ ] 描述中提到"多資料庫整合"
- [ ] 測試查詢後可以看到資料庫標註
- [ ] 參考資料中顯示完整來源追蹤

---

## 🎉 更新完成後

恭喜！更新完成後，您的系統現在：

✅ **5 個 RAG 策略改用 ChromaDB 優先**
- Vector RAG、Advanced RAG、Agentic RAG、Self RAG、Naive RAG

✅ **策略名稱清楚顯示使用的資料庫**
- 例如："🔍 Vector RAG (ChromaDB優先)"

✅ **每個回答都包含完整來源追蹤**
- 顯示資料庫來源（Neo4j/ChromaDB）
- 顯示原始來源（Met Museum API/Internal Knowledge Base）
- 顯示檢索方法（vector/fulltext/graph）

✅ **資料來源分布統計**
- 顯示使用了多少個 Neo4j 結果
- 顯示使用了多少個 ChromaDB 結果

---

**文件位置**: `enhanced_openwebui_rag_function_v4.py`
**更新日期**: 2025-10-19
**版本**: v4.1.0
