# 藝術史資料庫 API 完整文檔

## 📋 目錄

- [簡介](#簡介)
- [快速開始](#快速開始)
- [認證](#認證)
- [API端點](#api端點)
- [資料格式](#資料格式)
- [錯誤處理](#錯誤處理)
- [使用範例](#使用範例)
- [SDK支援](#sdk支援)

---

## 🎯 簡介

藝術史資料庫提供完整的RESTful API，支援多種RAG策略和資料格式，專為藝術史研究和AI應用設計。

### 基本資訊

- **API基礎URL**: `http://localhost:8008/api/v1`
- **版本**: v1.0
- **協議**: HTTP/HTTPS
- **資料格式**: JSON
- **字符編碼**: UTF-8

### API特性

✅ 7種RAG策略支援
✅ 35種LLM+RAG組合
✅ 多語言資料支援
✅ 高品質資料來源
✅ 即時品質監控

---

## 🚀 快速開始

### 安裝與部署

```bash
# 1. 克隆專案
git clone <repository-url>
cd 藝術史資料庫

# 2. 設置環境變數
cp art-history-database/.env.example art-history-database/.env
# 編輯 .env 文件，填入API密鑰

# 3. 啟動所有服務
docker-compose -f art-history-database/docker-compose.complete.yml up -d

# 4. 驗證服務狀態
curl http://localhost:8008/health
```

### 第一個API請求

```bash
curl -X POST http://localhost:8008/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "介紹文藝復興時期的藝術特點",
    "strategy": "hybrid_balanced",
    "top_k": 5
  }'
```

---

## 🔐 認證

目前API使用簡單的密鑰認證（未來將支援OAuth2）。

### 請求頭

```http
Authorization: Bearer YOUR_API_KEY
Content-Type: application/json
```

### 獲取API密鑰

```bash
# 開發環境：使用預設密鑰（僅用於測試）
export API_KEY="dev_test_key_123"

# 生產環境：聯繫管理員獲取正式密鑰
```

---

## 📡 API端點

### 1. 健康檢查

**端點**: `GET /health`

**描述**: 檢查API服務狀態

**請求範例**:
```bash
curl http://localhost:8008/health
```

**響應範例**:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2025-10-16T10:30:00Z",
  "services": {
    "neo4j": "connected",
    "postgres": "connected",
    "redis": "connected",
    "elasticsearch": "connected"
  }
}
```

---

### 2. RAG查詢

**端點**: `POST /api/v1/query`

**描述**: 使用RAG策略進行智能查詢

**請求參數**:

| 參數 | 類型 | 必需 | 說明 |
|-----|------|-----|------|
| query | string | ✅ | 查詢問題 |
| strategy | string | ✅ | RAG策略名稱 |
| top_k | integer | ❌ | 返回結果數量（默認5） |
| include_sources | boolean | ❌ | 是否包含來源（默認true） |
| language | string | ❌ | 結果語言（默認zh-TW） |

**支援的RAG策略**:

- `hybrid_balanced` - 平衡混合策略（推薦）
- `advanced_rag` - Advanced RAG多級檢索
- `vector_only` - 純向量檢索
- `graph_only` - 知識圖譜檢索
- `agentic_rag` - 智能代理推理
- `self_rag` - 自我反思策略
- `naive_rag` - 簡單快速檢索

**請求範例**:
```bash
curl -X POST http://localhost:8008/api/v1/query \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "query": "達文西的蒙娜麗莎有什麼藝術特色？",
    "strategy": "advanced_rag",
    "top_k": 5,
    "include_sources": true,
    "language": "zh-TW"
  }'
```

**響應範例**:
```json
{
  "status": "success",
  "query": "達文西的蒙娜麗莎有什麼藝術特色？",
  "answer": "達文西的《蒙娜麗莎》是文藝復興時期最具代表性的肖像畫作品...",
  "strategy_used": "advanced_rag",
  "confidence_score": 0.95,
  "processing_time": 1.234,
  "sources": [
    {
      "title": "Mona Lisa - Leonardo da Vinci",
      "source": "Metropolitan Museum",
      "score": 0.98,
      "url": "https://www.metmuseum.org/art/collection/..."
    }
  ],
  "metadata": {
    "total_documents_searched": 1500,
    "relevant_documents": 15,
    "timestamp": "2025-10-16T10:30:00Z"
  }
}
```

---

### 3. 批次查詢

**端點**: `POST /api/v1/batch-query`

**描述**: 批次處理多個查詢

**請求參數**:

```json
{
  "queries": [
    {
      "id": "q1",
      "query": "文藝復興時期的代表作品",
      "strategy": "hybrid_balanced"
    },
    {
      "id": "q2",
      "query": "巴洛克藝術的特點",
      "strategy": "graph_only"
    }
  ],
  "max_concurrent": 5
}
```

**響應範例**:
```json
{
  "status": "success",
  "total_queries": 2,
  "completed": 2,
  "failed": 0,
  "results": [
    {
      "id": "q1",
      "status": "success",
      "answer": "...",
      "processing_time": 1.2
    },
    {
      "id": "q2",
      "status": "success",
      "answer": "...",
      "processing_time": 0.8
    }
  ]
}
```

---

### 4. 藝術品搜索

**端點**: `GET /api/v1/artworks`

**描述**: 搜索藝術品資料

**查詢參數**:

| 參數 | 類型 | 說明 | 範例 |
|-----|------|------|------|
| q | string | 搜索關鍵詞 | "Mona Lisa" |
| artist | string | 藝術家名稱 | "Leonardo da Vinci" |
| period | string | 藝術時期 | "Renaissance" |
| medium | string | 創作媒材 | "Oil painting" |
| source | string | 資料來源 | "met_museum" |
| limit | integer | 結果數量 | 20 |
| offset | integer | 偏移量 | 0 |

**請求範例**:
```bash
curl "http://localhost:8008/api/v1/artworks?q=Starry%20Night&artist=Van%20Gogh&limit=10"
```

**響應範例**:
```json
{
  "status": "success",
  "total": 1,
  "limit": 10,
  "offset": 0,
  "artworks": [
    {
      "id": "artwork_001",
      "title": "The Starry Night",
      "artist": "Vincent van Gogh",
      "date": "1889",
      "medium": "Oil on canvas",
      "dimensions": "73.7 cm × 92.1 cm",
      "location": "Museum of Modern Art, New York",
      "description": "...",
      "image_url": "https://...",
      "source": "met_museum",
      "quality_score": 98.5
    }
  ]
}
```

---

### 5. 藝術家資訊

**端點**: `GET /api/v1/artists/{artist_id}`

**描述**: 獲取藝術家詳細資訊

**路徑參數**:
- `artist_id` - 藝術家ID

**請求範例**:
```bash
curl http://localhost:8008/api/v1/artists/leonardo-da-vinci
```

**響應範例**:
```json
{
  "status": "success",
  "artist": {
    "id": "leonardo-da-vinci",
    "name": "Leonardo da Vinci",
    "full_name": "Leonardo di ser Piero da Vinci",
    "birth_year": 1452,
    "death_year": 1519,
    "nationality": "Italian",
    "biography": "...",
    "notable_works": [
      {
        "id": "mona-lisa",
        "title": "Mona Lisa",
        "year": 1503
      },
      {
        "id": "last-supper",
        "title": "The Last Supper",
        "year": 1498
      }
    ],
    "art_movements": ["Renaissance"],
    "sources": ["met_museum", "harvard_art_museums"]
  }
}
```

---

### 6. 資料品質報告

**端點**: `GET /api/v1/quality/report`

**描述**: 獲取資料品質監控報告

**查詢參數**:
- `source` - 資料來源ID（可選）
- `period` - 時間範圍（可選，如 "7d", "30d"）

**請求範例**:
```bash
curl "http://localhost:8008/api/v1/quality/report?source=harvard_art_museums&period=7d"
```

**響應範例**:
```json
{
  "status": "success",
  "report": {
    "source_id": "harvard_art_museums",
    "source_name": "Harvard Art Museums",
    "overall_score": 95.5,
    "total_records": 1500,
    "quality_scores": {
      "completeness": 96.2,
      "accuracy": 98.5,
      "consistency": 94.8,
      "timeliness": 92.0,
      "validity": 97.3,
      "uniqueness": 99.1
    },
    "trend": "improving",
    "alerts": [
      {
        "level": "info",
        "metric": "timeliness",
        "message": "部分記錄超過30天未更新",
        "affected_records": 25
      }
    ],
    "last_updated": "2025-10-16T10:30:00Z"
  }
}
```

---

### 7. 統計分析

**端點**: `GET /api/v1/statistics`

**描述**: 獲取資料庫統計資訊

**請求範例**:
```bash
curl http://localhost:8008/api/v1/statistics
```

**響應範例**:
```json
{
  "status": "success",
  "statistics": {
    "total_artworks": 15234,
    "total_artists": 3421,
    "total_museums": 156,
    "data_sources": [
      {
        "source_id": "harvard_art_museums",
        "record_count": 5000,
        "quality_score": 95.5
      },
      {
        "source_id": "met_museum",
        "record_count": 7234,
        "quality_score": 93.2
      },
      {
        "source_id": "europeana",
        "record_count": 3000,
        "quality_score": 96.8
      }
    ],
    "period_distribution": {
      "Renaissance": 3245,
      "Baroque": 2134,
      "Modern": 4567,
      "Contemporary": 5288
    },
    "language_distribution": {
      "en": 12000,
      "zh-TW": 1500,
      "fr": 800,
      "de": 934
    }
  }
}
```

---

## 📊 資料格式

### 藝術品資料結構

```json
{
  "id": "unique_artwork_id",
  "title": "作品標題",
  "artist": "藝術家名稱",
  "date": "創作年代",
  "period": "藝術時期",
  "medium": "創作媒材",
  "dimensions": "尺寸",
  "description": "作品描述",
  "provenance": ["來源記錄"],
  "current_location": "當前位置",
  "image_url": "圖片URL",
  "source": "資料來源",
  "quality_score": 95.5,
  "metadata": {
    "created_at": "2025-10-16T10:30:00Z",
    "updated_at": "2025-10-16T10:30:00Z"
  }
}
```

### 藝術家資料結構

```json
{
  "id": "unique_artist_id",
  "name": "藝術家名稱",
  "full_name": "完整名稱",
  "birth_year": 1452,
  "death_year": 1519,
  "nationality": "國籍",
  "biography": "生平簡介",
  "notable_works": ["代表作品列表"],
  "art_movements": ["藝術運動"],
  "influences": ["影響因素"],
  "sources": ["資料來源"]
}
```

---

## ⚠️ 錯誤處理

### HTTP狀態碼

| 狀態碼 | 說明 |
|--------|------|
| 200 | 成功 |
| 201 | 創建成功 |
| 400 | 請求錯誤 |
| 401 | 未授權 |
| 403 | 禁止訪問 |
| 404 | 資源未找到 |
| 429 | 請求過於頻繁 |
| 500 | 服務器錯誤 |
| 503 | 服務不可用 |

### 錯誤響應格式

```json
{
  "status": "error",
  "error": {
    "code": "INVALID_PARAMETER",
    "message": "Invalid RAG strategy specified",
    "details": {
      "parameter": "strategy",
      "provided": "invalid_strategy",
      "valid_options": ["hybrid_balanced", "advanced_rag", "..."]
    }
  },
  "timestamp": "2025-10-16T10:30:00Z"
}
```

### 常見錯誤代碼

- `INVALID_PARAMETER` - 參數錯誤
- `MISSING_REQUIRED_FIELD` - 缺少必需欄位
- `AUTHENTICATION_FAILED` - 認證失敗
- `RATE_LIMIT_EXCEEDED` - 超過速率限制
- `RESOURCE_NOT_FOUND` - 資源未找到
- `SERVICE_UNAVAILABLE` - 服務不可用
- `INTERNAL_ERROR` - 內部錯誤

---

## 💡 使用範例

### Python SDK

```python
import requests

class ArtHistoryAPI:
    def __init__(self, base_url="http://localhost:8008", api_key=None):
        self.base_url = base_url
        self.api_key = api_key
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}" if api_key else ""
        }

    def query(self, question, strategy="hybrid_balanced", top_k=5):
        """執行RAG查詢"""
        response = requests.post(
            f"{self.base_url}/api/v1/query",
            json={
                "query": question,
                "strategy": strategy,
                "top_k": top_k
            },
            headers=self.headers
        )
        return response.json()

    def search_artworks(self, query, limit=10):
        """搜索藝術品"""
        response = requests.get(
            f"{self.base_url}/api/v1/artworks",
            params={"q": query, "limit": limit},
            headers=self.headers
        )
        return response.json()

# 使用範例
api = ArtHistoryAPI(api_key="YOUR_API_KEY")

# RAG查詢
result = api.query("介紹文藝復興的藝術特點", strategy="advanced_rag")
print(result["answer"])

# 搜索藝術品
artworks = api.search_artworks("Mona Lisa")
for artwork in artworks["artworks"]:
    print(f"{artwork['title']} by {artwork['artist']}")
```

### JavaScript SDK

```javascript
class ArtHistoryAPI {
  constructor(baseUrl = 'http://localhost:8008', apiKey = null) {
    this.baseUrl = baseUrl;
    this.apiKey = apiKey;
  }

  async query(question, strategy = 'hybrid_balanced', topK = 5) {
    const response = await fetch(`${this.baseUrl}/api/v1/query`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.apiKey}`
      },
      body: JSON.stringify({
        query: question,
        strategy: strategy,
        top_k: topK
      })
    });
    return await response.json();
  }

  async searchArtworks(query, limit = 10) {
    const params = new URLSearchParams({ q: query, limit: limit });
    const response = await fetch(
      `${this.baseUrl}/api/v1/artworks?${params}`,
      {
        headers: {
          'Authorization': `Bearer ${this.apiKey}`
        }
      }
    );
    return await response.json();
  }
}

// 使用範例
const api = new ArtHistoryAPI('http://localhost:8008', 'YOUR_API_KEY');

// RAG查詢
const result = await api.query('介紹文藝復興的藝術特點', 'advanced_rag');
console.log(result.answer);

// 搜索藝術品
const artworks = await api.searchArtworks('Mona Lisa');
artworks.artworks.forEach(artwork => {
  console.log(`${artwork.title} by ${artwork.artist}`);
});
```

---

## 📚 SDK支援

### 官方SDK

- **Python SDK**: `pip install art-history-sdk`
- **JavaScript SDK**: `npm install art-history-sdk`
- **TypeScript SDK**: 包含在JavaScript SDK中

### 社群SDK

- **Java SDK**: [GitHub連結]
- **Go SDK**: [GitHub連結]
- **Ruby SDK**: [GitHub連結]

---

## 🔗 相關資源

- **API遊樂場**: http://localhost:8008/playground
- **互動式文檔**: http://localhost:8008/docs
- **OpenAPI規範**: http://localhost:8008/openapi.json
- **品質儀表板**: http://localhost:8888/quality_dashboard.html
- **Grafana監控**: http://localhost:3001

---

## 📞 支援與回饋

- **問題回報**: [GitHub Issues]
- **功能請求**: [GitHub Discussions]
- **郵件支援**: support@arthistory-db.com
- **文檔改進**: 歡迎提交PR

---

## 📄 授權

本API文檔遵循 MIT 授權條款。

---

**版本**: 1.0.0
**最後更新**: 2025-10-16
**維護團隊**: Art History Database Team
