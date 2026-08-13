# RAG 檢索策略優化指南

## 📋 目錄
1. [當前系統分析](#當前系統分析)
2. [LangChain RAG 檢索策略](#langchain-rag-檢索策略)
3. [Neo4j 檢索優化建議](#neo4j-檢索優化建議)
4. [實施優化方案](#實施優化方案)
5. [性能評估指標](#性能評估指標)

---

## 🔍 當前系統分析

### 現有架構
基於代碼分析，您的系統當前實現了：

1. **RAG 策略**
   - ✅ Vector Only (純向量檢索)
   - ✅ Graph Only (純圖譜檢索)
   - ✅ Hybrid Balanced (混合檢索)
   - ✅ Advanced RAG (多級檢索)
   - ✅ Self-RAG (自我反思)
   - ✅ Agentic RAG (智能代理)
   - ✅ Naive RAG (簡單檢索)

2. **Neo4j 圖譜檢索**
   ```python
   # 當前實現 (knowledge_graph_rag.py:222-239)
   MATCH (a:Artist)
   WHERE a.name CONTAINS $query OR a.biography CONTAINS $query
   OPTIONAL MATCH (a)-[r1:CREATED_BY]-(w:Artwork)
   OPTIONAL MATCH (a)-[r2:BELONGS_TO_MOVEMENT]-(m:Movement)
   RETURN a, collect(DISTINCT w) as artworks, collect(DISTINCT m) as movements
   LIMIT 10
   ```

### ⚠️ 潛在問題

1. **Neo4j 檢索不夠精確**
   - 使用簡單的 `CONTAINS` 字符串匹配，沒有語義相似度
   - 缺少向量化搜索（Neo4j 支持向量索引）
   - 沒有利用 Neo4j 的全文索引功能
   - 查詢結果排序僅依賴圖結構，未考慮語義相關性

2. **缺少重排序機制**
   - 檢索結果沒有經過 Re-ranker 模型精排
   - 無法利用交叉編碼器提升精確度

3. **查詢處理簡單**
   - 沒有查詢擴展和改寫
   - 缺少多角度查詢生成
   - 未處理中英文混合查詢

---

## 🦜 LangChain RAG 檢索策略

### 1. 多查詢檢索器 (MultiQueryRetriever)

**適用場景**: 從不同角度重新表述查詢，提高召回率

**實現方式**:
```python
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain_openai import ChatOpenAI

# 初始化
llm = ChatOpenAI(temperature=0)
retriever_from_llm = MultiQueryRetriever.from_llm(
    retriever=base_retriever,
    llm=llm
)

# 使用
docs = retriever_from_llm.get_relevant_documents(
    "達文西的藝術風格是什麼？"
)
```

**工作原理**:
1. LLM 生成多個相似查詢（如："達文西的繪畫特色"、"Leonardo da Vinci 藝術手法"）
2. 對每個查詢執行檢索
3. 合併並去重結果

**優勢**:
- 提高召回率
- 處理查詢表述的歧義
- 自動進行查詢擴展

---

### 2. 上下文壓縮檢索器 (ContextualCompressionRetriever)

**適用場景**: 提取檢索文檔中最相關的部分，減少噪音

**實現方式**:
```python
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import LLMChainExtractor

# 初始化壓縮器
compressor = LLMChainExtractor.from_llm(llm)

# 創建壓縮檢索器
compression_retriever = ContextualCompressionRetriever(
    base_compressor=compressor,
    base_retriever=base_retriever
)

# 使用
compressed_docs = compression_retriever.get_relevant_documents(
    "印象派的主要特徵"
)
```

**工作原理**:
1. 基礎檢索器獲取相關文檔
2. LLM 提取每個文檔中與查詢最相關的部分
3. 返回壓縮後的高質量片段

**優勢**:
- 減少無關信息
- 提高上下文質量
- 降低 token 消耗

---

### 3. 集成檢索器 (EnsembleRetriever)

**適用場景**: 結合多個檢索器的優勢（如 BM25 + 向量檢索）

**實現方式**:
```python
from langchain.retrievers import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever

# 創建多個檢索器
bm25_retriever = BM25Retriever.from_documents(documents)
vector_retriever = vectorstore.as_retriever(search_kwargs={"k": 5})

# 組合檢索器
ensemble_retriever = EnsembleRetriever(
    retrievers=[bm25_retriever, vector_retriever],
    weights=[0.4, 0.6]  # BM25 40%, 向量 60%
)

# 使用
docs = ensemble_retriever.get_relevant_documents(
    "巴洛克時期的雕塑作品"
)
```

**優勢**:
- 結合傳統檢索和語義檢索
- 提高檢索穩定性
- 適合多語言查詢

---

### 4. 父文檔檢索器 (ParentDocumentRetriever)

**適用場景**: 檢索小塊文檔，但返回完整上下文

**實現方式**:
```python
from langchain.retrievers import ParentDocumentRetriever
from langchain.storage import InMemoryStore
from langchain_text_splitters import RecursiveCharacterTextSplitter

# 創建存儲
parent_store = InMemoryStore()

# 創建分割器
child_splitter = RecursiveCharacterTextSplitter(chunk_size=400)
parent_splitter = RecursiveCharacterTextSplitter(chunk_size=2000)

# 創建檢索器
retriever = ParentDocumentRetriever(
    vectorstore=vectorstore,
    docstore=parent_store,
    child_splitter=child_splitter,
    parent_splitter=parent_splitter,
)

# 添加文檔
retriever.add_documents(documents)
```

**優勢**:
- 精確檢索（小塊）+ 完整上下文（大塊）
- 平衡精確度和信息完整性

---

### 5. 自查詢檢索器 (SelfQueryRetriever)

**適用場景**: 從自然語言查詢中提取結構化過濾條件

**實現方式**:
```python
from langchain.retrievers.self_query.base import SelfQueryRetriever
from langchain.chains.query_constructor.base import AttributeInfo

# 定義元數據屬性
metadata_field_info = [
    AttributeInfo(
        name="period",
        description="藝術時期（如 Renaissance, Baroque）",
        type="string",
    ),
    AttributeInfo(
        name="artist",
        description="藝術家名稱",
        type="string",
    ),
    AttributeInfo(
        name="year",
        description="創作年份",
        type="integer",
    ),
]

# 創建檢索器
retriever = SelfQueryRetriever.from_llm(
    llm,
    vectorstore,
    document_content_description="藝術史作品和資料",
    metadata_field_info=metadata_field_info,
)

# 使用
docs = retriever.get_relevant_documents(
    "1500年到1600年間文藝復興時期的繪畫作品"
)
```

**工作原理**:
1. LLM 解析查詢，提取語義部分和過濾條件
2. 語義部分用於向量檢索
3. 過濾條件用於元數據篩選

**優勢**:
- 結合語義搜索和精確過濾
- 處理複雜查詢
- 自動提取結構化條件

---

### 6. 時間權重檢索器 (TimeWeightedVectorStoreRetriever)

**適用場景**: 考慮文檔新鮮度的檢索

**實現方式**:
```python
from langchain.retrievers import TimeWeightedVectorStoreRetriever

retriever = TimeWeightedVectorStoreRetriever(
    vectorstore=vectorstore,
    decay_rate=0.01,  # 衰減率
    k=5
)

# 使用
docs = retriever.get_relevant_documents(
    "最新的藝術史研究發現"
)
```

**優勢**:
- 平衡相關性和新鮮度
- 適合動態更新的知識庫

---

## 🔧 Neo4j 檢索優化建議

### 1. 添加向量索引支持

**問題**: 當前只使用字符串匹配，無法捕捉語義相似度

**解決方案**: 利用 Neo4j Vector Index

```python
# 創建向量索引
CREATE VECTOR INDEX artist_name_embeddings IF NOT EXISTS
FOR (a:Artist) ON (a.name_embedding)
OPTIONS {indexConfig: {
 `vector.dimensions`: 1536,
 `vector.similarity_function`: 'cosine'
}}

# 查詢時使用向量相似度
def search_artists_by_embedding(query_embedding, top_k=5):
    cypher = """
    CALL db.index.vector.queryNodes('artist_name_embeddings', $top_k, $query_embedding)
    YIELD node, score
    RETURN node.name AS name, node.biography AS bio, score
    ORDER BY score DESC
    """
    return graph.query(cypher, {
        'query_embedding': query_embedding,
        'top_k': top_k
    })
```

**優勢**:
- 語義相似度搜索
- 支持多語言查詢
- 更精確的匹配

---

### 2. 使用全文索引

**問題**: `CONTAINS` 性能差，無法處理複雜文本查詢

**解決方案**: 創建全文索引

```cypher
// 創建全文索引
CREATE FULLTEXT INDEX artist_fulltext IF NOT EXISTS
FOR (a:Artist) ON EACH [a.name, a.biography, a.nationality]

CREATE FULLTEXT INDEX artwork_fulltext IF NOT EXISTS
FOR (w:Artwork) ON EACH [w.title, w.description, w.medium]

// 使用全文搜索
CALL db.index.fulltext.queryNodes('artist_fulltext', '達文西 OR Leonardo')
YIELD node, score
RETURN node.name, score
ORDER BY score DESC
LIMIT 10
```

**優勢**:
- 更快的文本搜索
- 支持模糊匹配
- 自動分詞和評分

---

### 3. 混合檢索策略

**優化後的檢索流程**:

```python
class EnhancedNeo4jRetriever:
    def __init__(self, graph, embedding_model):
        self.graph = graph
        self.embedding_model = embedding_model

    async def hybrid_search(self, query: str, top_k: int = 5):
        """混合檢索：向量 + 全文 + 圖關係"""

        # 1. 生成查詢向量
        query_embedding = self.embedding_model.embed_query(query)

        # 2. 向量搜索
        vector_results = self.vector_search(query_embedding, top_k=10)

        # 3. 全文搜索
        fulltext_results = self.fulltext_search(query, top_k=10)

        # 4. 圖關係擴展
        graph_results = self.graph_expansion(
            vector_results + fulltext_results
        )

        # 5. 重排序
        final_results = self.rerank(
            query,
            graph_results,
            top_k=top_k
        )

        return final_results

    def vector_search(self, embedding, top_k=10):
        """向量相似度搜索"""
        cypher = """
        CALL db.index.vector.queryNodes(
            'artist_name_embeddings',
            $top_k,
            $embedding
        )
        YIELD node, score
        RETURN node, score
        """
        return self.graph.query(cypher, {
            'embedding': embedding,
            'top_k': top_k
        })

    def fulltext_search(self, query, top_k=10):
        """全文搜索"""
        cypher = """
        CALL db.index.fulltext.queryNodes(
            'artist_fulltext',
            $query
        )
        YIELD node, score
        WHERE score > 0.5
        RETURN node, score
        ORDER BY score DESC
        LIMIT $top_k
        """
        return self.graph.query(cypher, {
            'query': query,
            'top_k': top_k
        })

    def graph_expansion(self, initial_results):
        """圖關係擴展"""
        entity_ids = [r['node'].id for r in initial_results]

        cypher = """
        MATCH (n)
        WHERE id(n) IN $entity_ids
        OPTIONAL MATCH (n)-[r]-(related)
        RETURN n, r, related,
               type(r) as rel_type,
               labels(related) as related_labels
        """
        return self.graph.query(cypher, {
            'entity_ids': entity_ids
        })

    def rerank(self, query, results, top_k=5):
        """使用交叉編碼器重排序"""
        from sentence_transformers import CrossEncoder

        model = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')

        # 準備文本對
        pairs = []
        for result in results:
            doc_text = self._format_result(result)
            pairs.append([query, doc_text])

        # 計算相關性分數
        scores = model.predict(pairs)

        # 排序並返回 top_k
        ranked_results = sorted(
            zip(results, scores),
            key=lambda x: x[1],
            reverse=True
        )

        return ranked_results[:top_k]
```

---

### 4. 查詢擴展和改寫

**問題**: 單一查詢表述可能遺漏相關結果

**解決方案**: 使用 LLM 進行查詢擴展

```python
class QueryExpander:
    def __init__(self, llm):
        self.llm = llm

    def expand_query(self, original_query: str) -> List[str]:
        """生成多個查詢變體"""
        prompt = f"""
        作為藝術史專家，請將以下查詢改寫成3個不同角度的表述，
        包括中英文混合：

        原始查詢: {original_query}

        請提供：
        1. 學術正式表述
        2. 通俗表述
        3. 英文表述

        格式: 每行一個查詢
        """

        response = self.llm.invoke(prompt)
        queries = [q.strip() for q in response.content.split('\n') if q.strip()]

        # 添加原始查詢
        queries.insert(0, original_query)

        return queries

    def generate_related_concepts(self, query: str) -> List[str]:
        """生成相關概念"""
        prompt = f"""
        針對查詢 "{query}"，列出5個相關的藝術史概念或關鍵詞。

        格式: 概念1, 概念2, ...
        """

        response = self.llm.invoke(prompt)
        concepts = [c.strip() for c in response.content.split(',')]

        return concepts
```

---

## 🚀 實施優化方案

### 方案 1: 快速優化（1-2天）

**目標**: 提升現有系統精確度

1. **添加 Re-ranker**
   ```python
   from sentence_transformers import CrossEncoder

   class RerankingRetriever:
       def __init__(self, base_retriever):
           self.base_retriever = base_retriever
           self.reranker = CrossEncoder('BAAI/bge-reranker-large')

       def retrieve(self, query, top_k=5):
           # 基礎檢索（多檢索一些）
           initial_docs = self.base_retriever.get_relevant_documents(
               query,
               top_k=top_k * 3
           )

           # 重排序
           pairs = [[query, doc.page_content] for doc in initial_docs]
           scores = self.reranker.predict(pairs)

           # 排序並返回 top_k
           ranked_docs = sorted(
               zip(initial_docs, scores),
               key=lambda x: x[1],
               reverse=True
           )

           return [doc for doc, score in ranked_docs[:top_k]]
   ```

2. **優化 Neo4j Cypher 查詢**
   - 添加全文索引
   - 改進查詢語句
   - 添加結果評分機制

3. **實現查詢擴展**
   - 使用 MultiQueryRetriever
   - 處理中英文混合查詢

---

### 方案 2: 中期優化（1週）

**目標**: 實現混合檢索架構

1. **Neo4j 向量索引**
   ```python
   # 為所有節點添加向量嵌入
   async def add_vector_embeddings():
       # 獲取所有藝術家
       artists = graph.query("MATCH (a:Artist) RETURN a")

       for artist in artists:
           # 生成嵌入
           text = f"{artist['name']} {artist['biography']}"
           embedding = embedding_model.embed_query(text)

           # 更新節點
           graph.query("""
               MATCH (a:Artist {name: $name})
               SET a.name_embedding = $embedding
           """, {
               'name': artist['name'],
               'embedding': embedding
           })
   ```

2. **集成多個檢索器**
   ```python
   from langchain.retrievers import EnsembleRetriever

   # 組合檢索器
   ensemble = EnsembleRetriever(
       retrievers=[
           bm25_retriever,        # 傳統檢索
           vector_retriever,      # 向量檢索
           neo4j_graph_retriever  # 圖檢索
       ],
       weights=[0.2, 0.4, 0.4]
   )
   ```

3. **添加上下文壓縮**
   ```python
   compression_retriever = ContextualCompressionRetriever(
       base_compressor=compressor,
       base_retriever=ensemble
   )
   ```

---

### 方案 3: 長期優化（2-4週）

**目標**: 構建生產級 RAG 系統

1. **實現所有 LangChain 高級檢索器**
   - MultiQueryRetriever
   - SelfQueryRetriever
   - ParentDocumentRetriever
   - TimeWeightedRetriever

2. **添加 LangGraph 工作流**
   ```python
   from langgraph.graph import StateGraph

   # 定義 RAG 工作流
   workflow = StateGraph()
   workflow.add_node("query_analysis", analyze_query)
   workflow.add_node("retrieval", retrieve_documents)
   workflow.add_node("rerank", rerank_documents)
   workflow.add_node("generate", generate_answer)

   # 添加邊
   workflow.add_edge("query_analysis", "retrieval")
   workflow.add_edge("retrieval", "rerank")
   workflow.add_edge("rerank", "generate")
   ```

3. **實現監控和優化**
   - LangSmith 追蹤
   - 性能指標收集
   - A/B 測試框架
   - 自動參數調優

---

## 📊 性能評估指標

### 檢索質量指標

1. **Recall@K**: 前K個結果中相關文檔的比例
2. **Precision@K**: 前K個結果中有用文檔的比例
3. **MRR (Mean Reciprocal Rank)**: 第一個相關結果的排名倒數
4. **NDCG (Normalized Discounted Cumulative Gain)**: 考慮排序質量的綜合指標

### 用戶體驗指標

1. **響應時間**: 查詢到返回結果的時間
2. **答案質量評分**: 用戶對答案的評分
3. **上下文相關性**: 檢索內容與查詢的相關度

### 實現評估框架

```python
class RAGEvaluator:
    def __init__(self, test_queries, ground_truth):
        self.test_queries = test_queries
        self.ground_truth = ground_truth

    def evaluate_retrieval(self, retriever, k=5):
        """評估檢索質量"""
        recall_scores = []
        precision_scores = []
        mrr_scores = []

        for query, relevant_docs in zip(self.test_queries, self.ground_truth):
            # 檢索
            retrieved = retriever.get_relevant_documents(query, k=k)
            retrieved_ids = [doc.metadata.get('id') for doc in retrieved]

            # 計算指標
            relevant_ids = set(relevant_docs)
            retrieved_set = set(retrieved_ids)

            # Recall
            recall = len(relevant_ids & retrieved_set) / len(relevant_ids)
            recall_scores.append(recall)

            # Precision
            precision = len(relevant_ids & retrieved_set) / k
            precision_scores.append(precision)

            # MRR
            for i, doc_id in enumerate(retrieved_ids):
                if doc_id in relevant_ids:
                    mrr_scores.append(1 / (i + 1))
                    break
            else:
                mrr_scores.append(0)

        return {
            'recall@k': np.mean(recall_scores),
            'precision@k': np.mean(precision_scores),
            'mrr': np.mean(mrr_scores)
        }

    def compare_retrievers(self, retrievers: Dict[str, Any]):
        """比較多個檢索器"""
        results = {}

        for name, retriever in retrievers.items():
            print(f"\n評估 {name}...")
            metrics = self.evaluate_retrieval(retriever)
            results[name] = metrics

            print(f"  Recall@5: {metrics['recall@k']:.3f}")
            print(f"  Precision@5: {metrics['precision@k']:.3f}")
            print(f"  MRR: {metrics['mrr']:.3f}")

        return results
```

---

## 🎯 優先級建議

### 🔴 高優先級（立即實施）

1. **添加 Re-ranker** - 快速提升精確度
2. **優化 Neo4j 查詢** - 使用全文索引
3. **實現查詢擴展** - MultiQueryRetriever

### 🟡 中優先級（1-2週內）

1. **Neo4j 向量索引** - 語義搜索
2. **集成多檢索器** - EnsembleRetriever
3. **上下文壓縮** - 提升答案質量

### 🟢 低優先級（長期優化）

1. **LangGraph 工作流** - 更複雜的推理
2. **監控和追蹤** - LangSmith
3. **自動優化** - 參數調優

---

## 📚 參考資源

1. **LangChain 官方文檔**
   - [RAG 教程](https://python.langchain.com/docs/tutorials/rag/)
   - [Retrievers](https://python.langchain.com/docs/concepts/retrievers/)

2. **Neo4j 向量搜索**
   - [Vector Search](https://neo4j.com/docs/cypher-manual/current/indexes-for-vector-search/)
   - [Fulltext Index](https://neo4j.com/docs/cypher-manual/current/indexes-for-full-text-search/)

3. **Re-ranking 模型**
   - [BGE Reranker](https://huggingface.co/BAAI/bge-reranker-large)
   - [Cross-Encoder](https://www.sbert.net/examples/applications/cross-encoder/README.html)

4. **評估指標**
   - [RAGAS](https://github.com/explodinggradients/ragas) - RAG 評估框架
   - [LangSmith](https://docs.smith.langchain.com/) - 追蹤和評估

---

## 🛠️ 下一步行動

1. **立即實施**: 添加 Re-ranker 到現有系統
2. **測試評估**: 使用評估框架比較優化前後效果
3. **逐步優化**: 按優先級實施其他優化方案
4. **持續監控**: 收集用戶反饋和性能數據

需要我提供具體某個優化方案的詳細實現代碼嗎？
