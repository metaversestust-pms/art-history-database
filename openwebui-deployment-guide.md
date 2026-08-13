# OpenWebUI 藝術史資料庫部署指南

## 🎯 系統架構概覽

```
OpenWebUI (前端) → Ollama (LLM) → RAG系統 → CUDA ML服務 → 向量資料庫
     ↓                  ↓           ↓          ↓              ↓
   Port 3001        Port 11434   Port 3000   Port 8080    Port 8000
```

## 🚀 第一階段：基礎環境部署

### Step 1: 安裝 Ollama
```bash
# 下載並安裝 Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# 啟動 Ollama 服務
ollama serve

# 下載需要的模型
ollama pull llama3.1:8b
ollama pull bge-m3:latest
ollama pull nomic-embed-text
```

### Step 2: 部署 ChromaDB
```bash
# 啟動 ChromaDB 向量資料庫
docker run -d \
  --name chromadb \
  -p 8000:8000 \
  -v chromadb_data:/chroma/chroma \
  --restart unless-stopped \
  chromadb/chroma:latest
```

### Step 3: 驗證 CUDA ML 服務
```bash
# 檢查服務狀態
curl http://localhost:8080/health

# 測試分類API
curl -X POST http://localhost:8080/classify/artwork \
  -H "Content-Type: application/json" \
  -d '{"image_url": "test_image.jpg"}'
```

## 🌐 第二階段：OpenWebUI 配置

### Step 4: 部署 OpenWebUI
```bash
# 創建 OpenWebUI 配置目錄
mkdir -p ./openwebui-config

# 部署 OpenWebUI 容器
docker run -d \
  --name open-webui \
  -p 3001:8080 \
  -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
  -e WEBUI_SECRET_KEY="your-secret-key-here" \
  -e ENABLE_RAG_WEB_SEARCH=true \
  -e ENABLE_RAG_DOCUMENT=true \
  -e CHROMA_DB_URL=http://host.docker.internal:8000 \
  -e CUDA_ML_SERVICE_URL=http://host.docker.internal:8080 \
  --add-host=host.docker.internal:host-gateway \
  -v open-webui:/app/backend/data \
  -v ./openwebui-config:/app/backend/config \
  --restart always \
  ghcr.io/open-webui/open-webui:main
```

### Step 5: 自定義配置文件
```yaml
# openwebui-config/config.yaml
ui:
  title: "藝術史資料庫 AI 助手"
  description: "專業的藝術史研究與學習平台"
  theme: "dark"
  brand_color: "#8B4513"

models:
  default: "llama3.1:8b"
  available:
    - name: "llama3.1:8b"
      display_name: "藝術史專家 (大型)"
      description: "最適合複雜藝術史問題分析"
    - name: "llama3:8b"
      display_name: "通用助手 (標準)"
      description: "一般藝術問題諮詢"

rag:
  enabled: true
  default_collection: "art_history_knowledge"
  embedding_model: "bge-m3"
  top_k: 5
  enable_web_search: false

  collections:
    - name: "artwork_descriptions"
      display_name: "藝術品描述"
      description: "包含各種藝術品的詳細描述和分析"

    - name: "artist_biographies"
      display_name: "藝術家傳記"
      description: "藝術家的生平、作品和影響力"

    - name: "historical_periods"
      display_name: "藝術史時期"
      description: "各個藝術史時期的特徵和代表作"

custom_functions:
  - name: "analyze_artwork"
    display_name: "藝術品分析"
    description: "使用 AI 分析上傳的藝術品圖像"
    endpoint: "http://host.docker.internal:8080/classify/artwork"

  - name: "similarity_search"
    display_name: "相似作品搜索"
    description: "找到風格相似的藝術品"
    endpoint: "http://host.docker.internal:8080/similarity/search"
```

## 🔧 第三階段：RAG 集成配置

### Step 6: 連接向量資料庫
```python
# rag_integration.py - RAG 集成腳本
import chromadb
from sentence_transformers import SentenceTransformer

class ArtHistoryRAG:
    def __init__(self):
        self.chroma_client = chromadb.HttpClient(host="localhost", port=8000)
        self.embedding_model = SentenceTransformer('BAAI/bge-m3')

        # 創建藝術史知識庫集合
        self.artwork_collection = self.chroma_client.get_or_create_collection(
            name="artwork_descriptions",
            embedding_function=self.embedding_model
        )

        self.artist_collection = self.chroma_client.get_or_create_collection(
            name="artist_biographies",
            embedding_function=self.embedding_model
        )

    def add_documents(self, texts, metadata, collection_name):
        """添加文檔到指定集合"""
        collection = getattr(self, f"{collection_name}_collection")
        collection.add(
            documents=texts,
            metadatas=metadata,
            ids=[f"doc_{i}" for i in range(len(texts))]
        )

    def search(self, query, collection_name, n_results=5):
        """搜索相關文檔"""
        collection = getattr(self, f"{collection_name}_collection")
        results = collection.query(
            query_texts=[query],
            n_results=n_results
        )
        return results

# 使用示例
rag = ArtHistoryRAG()

# 添加藝術品描述
artwork_texts = [
    "《蒙娜麗莎》是達文西最著名的肖像畫作品，創作於1503-1519年間...",
    "《星夜》是梵高的代表作，展現了後印象派的典型風格...",
    "《大衛像》是米開朗基羅的雕塑傑作，高5.17米..."
]

artwork_metadata = [
    {"artist": "達文西", "period": "文藝復興", "year": 1503, "style": "寫實主義"},
    {"artist": "梵高", "period": "後印象派", "year": 1889, "style": "表現主義"},
    {"artist": "米開朗基羅", "period": "文藝復興", "year": 1504, "style": "古典主義"}
]

rag.add_documents(artwork_texts, artwork_metadata, "artwork")
```

### Step 7: 自定義提示詞模板
```python
# 藝術史專家提示詞模板
ART_EXPERT_PROMPT = """
你是一位資深的藝術史學者，專精於：
- 中國傳統藝術（書畫、陶瓷、雕塑）
- 西方古典到現代藝術史
- 藝術品分析與鑑賞
- 藝術史背景與文化脈絡

請根據以下知識庫內容回答用戶問題：

{context}

用戶問題：{question}

請提供：
1. 專業而準確的解答
2. 相關的歷史背景
3. 如有需要，提及相關藝術家或作品
4. 使用易懂但專業的語言
"""

# 多模態分析提示詞
MULTIMODAL_ANALYSIS_PROMPT = """
基於圖像分析結果和文本描述，請提供綜合分析：

圖像特徵：{image_features}
相關文獻：{text_context}
用戶查詢：{query}

請分析：
1. 作品的藝術風格和技法
2. 可能的創作時期和文化背景
3. 與其他相似作品的比較
4. 藝術史價值和影響
"""
```

## 🎨 第四階段：自定義界面優化

### Step 8: 自定義 CSS 樣式
```css
/* custom-art-theme.css */
:root {
  --primary-color: #8B4513;
  --secondary-color: #D2691E;
  --accent-color: #DAA520;
  --background-color: #1C1C1C;
  --text-color: #F5F5DC;
}

.art-history-theme {
  background: linear-gradient(135deg, #2C1810 0%, #1C1C1C 100%);
  font-family: 'Crimson Text', serif;
}

.artwork-card {
  border: 2px solid var(--accent-color);
  border-radius: 8px;
  background: rgba(139, 69, 19, 0.1);
  padding: 1rem;
  margin: 0.5rem;
}

.artist-badge {
  background-color: var(--primary-color);
  color: var(--text-color);
  border-radius: 20px;
  padding: 0.3rem 0.8rem;
  font-size: 0.9rem;
}
```

### Step 9: JavaScript 增強功能
```javascript
// art-history-enhancements.js

// 圖像上傳和分析功能
class ArtworkAnalyzer {
    constructor() {
        this.mlServiceUrl = 'http://localhost:8080';
    }

    async analyzeImage(imageFile) {
        const formData = new FormData();
        formData.append('image', imageFile);

        try {
            const response = await fetch(`${this.mlServiceUrl}/classify/artwork`, {
                method: 'POST',
                body: formData
            });

            const result = await response.json();
            return this.formatAnalysisResult(result);
        } catch (error) {
            console.error('圖像分析失敗:', error);
            return null;
        }
    }

    formatAnalysisResult(result) {
        return {
            style: result.predicted_style,
            period: result.predicted_period,
            confidence: result.confidence,
            similarWorks: result.similar_artworks || []
        };
    }
}

// 智能搜索建議
class SmartSearch {
    constructor() {
        this.suggestions = [
            "達文西的繪畫技法特點",
            "中國山水畫的演變歷程",
            "印象派與後印象派的區別",
            "文藝復興時期的雕塑特色"
        ];
    }

    getSuggestions(query) {
        return this.suggestions.filter(s =>
            s.includes(query) || query.length < 2
        );
    }
}

// 初始化增強功能
document.addEventListener('DOMContentLoaded', function() {
    const analyzer = new ArtworkAnalyzer();
    const smartSearch = new SmartSearch();

    // 添加圖像拖拽上傳
    const chatInput = document.querySelector('.chat-input');
    chatInput.addEventListener('drop', handleImageDrop);

    // 添加搜索建議
    const searchInput = document.querySelector('.search-input');
    searchInput.addEventListener('input', showSearchSuggestions);
});
```

## 📊 第五階段：性能監控和優化

### Step 10: 監控設置
```bash
# 啟動性能監控
docker run -d \
  --name prometheus \
  -p 9090:9090 \
  -v ./prometheus.yml:/etc/prometheus/prometheus.yml \
  prom/prometheus

# Grafana 儀表板
docker run -d \
  --name grafana \
  -p 3000:3000 \
  -e GF_SECURITY_ADMIN_PASSWORD=admin \
  grafana/grafana
```

## 🔧 第六階段：部署腳本

### Step 11: 一鍵部署腳本
```bash
#!/bin/bash
# deploy-art-history-system.sh

echo "🎨 開始部署藝術史資料庫系統..."

# 檢查必要服務
echo "📋 檢查必要服務..."
docker --version || { echo "需要安裝 Docker"; exit 1; }

# 啟動核心服務
echo "🚀 啟動核心服務..."
docker-compose -f docker-compose.optimized.yml up -d

# 等待服務準備就緒
echo "⏳ 等待服務初始化..."
sleep 30

# 檢查 CUDA ML 服務
echo "🔍 檢查 CUDA ML 服務..."
curl -f http://localhost:8080/health || { echo "CUDA ML 服務啟動失敗"; exit 1; }

# 啟動 Ollama
echo "🦙 啟動 Ollama..."
ollama serve &
sleep 10

# 下載模型
echo "📥 下載 AI 模型..."
ollama pull llama3.1:8b
ollama pull bge-m3:latest

# 啟動 ChromaDB
echo "🗄️  啟動向量資料庫..."
docker run -d \
  --name chromadb \
  -p 8000:8000 \
  -v chromadb_data:/chroma/chroma \
  chromadb/chroma:latest

# 部署 OpenWebUI
echo "🌐 部署 OpenWebUI..."
docker run -d \
  --name art-history-webui \
  -p 3001:8080 \
  -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
  -e CHROMA_DB_URL=http://host.docker.internal:8000 \
  --add-host=host.docker.internal:host-gateway \
  -v open-webui:/app/backend/data \
  ghcr.io/open-webui/open-webui:main

# 等待服務完全啟動
sleep 20

echo "✅ 部署完成！"
echo "🌐 OpenWebUI: http://localhost:3001"
echo "📊 系統監控: http://localhost:3000"
echo "🔧 向量資料庫: http://localhost:8000"
echo "🤖 CUDA ML 服務: http://localhost:8080"
```

## 📚 使用指南

### 基本功能
1. **文本問答**: 直接輸入藝術史相關問題
2. **圖像分析**: 上傳藝術品圖片進行AI分析
3. **知識庫搜索**: 在特定主題中搜索相關資料
4. **多語言支持**: 支持中文、英文等多語言查詢

### 進階功能
1. **自定義RAG**: 上傳專業文獻建立個人知識庫
2. **批量分析**: 同時處理多個藝術品圖像
3. **時序分析**: 追蹤藝術風格的歷史演變
4. **比較分析**: 對比不同藝術家或時期的作品

### 故障排除
- 如果服務無法啟動，檢查端口佔用
- 模型下載失敗時，確認網絡連接
- CUDA 服務問題時，檢查 GPU 驅動
- 向量搜索慢時，考慮增加索引優化

## 🔄 維護和更新
```bash
# 更新系統
./update-system.sh

# 備份資料
./backup-system.sh

# 監控日誌
docker logs -f art-history-webui
```

---
**📝 注意**: 首次部署需要下載大約 8GB 的模型文件，請確保有足夠的磁盘空間和網絡帶寬。