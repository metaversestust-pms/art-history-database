# 🎨 文藝復興與巴洛克藝術資料庫快速使用指南

## 📚 資料庫現狀

您的藝術史資料庫現已包含：
- ✅ **1,280件** 文藝復興和巴洛克時期藝術作品
- ✅ **完整導入** Neo4j知識圖譜
- ✅ **準備就緒** 可在OpenWebUI中使用

---

## 🚀 快速開始

### 1. 在Neo4j中查詢資料

訪問 Neo4j Browser: **http://localhost:7474**

**常用查詢範例:**

```cypher
// 查看文藝復興時期作品
MATCH (a:Artwork)
WHERE a.period = 'Renaissance'
RETURN a.title, a.dated, a.medium
LIMIT 20

// 查看巴洛克時期作品
MATCH (a:Artwork)
WHERE a.period = 'Baroque'
RETURN a.title, a.dated, a.medium
LIMIT 20

// 查詢Raphael的所有作品
MATCH (p:Artist)-[:CREATED]->(a:Artwork)
WHERE p.name CONTAINS 'Raphael'
RETURN p.name as Artist, a.title as Artwork, a.dated as Date

// 統計各時期作品數量
MATCH (a:Artwork)
WHERE a.period IS NOT NULL
RETURN a.period as Period, count(a) as Count
ORDER BY Count DESC
```

### 2. 在OpenWebUI中提問

訪問 OpenWebUI: **http://localhost:8080**

**範例問題:**
- "請介紹Raphael (拉斐爾)的生平和代表作品"
- "Caravaggio的繪畫風格有什麼特色？"
- "文藝復興和巴洛克時期在藝術風格上有什麼差異？"

---

開始探索您的藝術史資料庫吧！🎨
