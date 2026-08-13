#!/usr/bin/env python3
"""
修復 RAG Manager 中 GraphOnlyRAG 的關鍵詞提取
讓它能正確處理翻譯後的混合語言查詢
"""

import re

def extract_english_keywords(query: str) -> list:
    """
    從混合語言查詢中提取英文關鍵詞

    例如: "Leonardo da Vinci的masterpiece品有哪些"
    -> ["Leonardo", "da", "Vinci", "masterpiece"]
    """
    # 移除標點符號，保留字母和空格
    cleaned = re.sub(r'[^\w\s]', ' ', query)

    # 提取所有英文單詞（至少2個字母）
    english_words = re.findall(r'\b[a-zA-Z]{2,}\b', cleaned)

    # 移除常見停用詞
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                  'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
                  'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
                  'can', 'could', 'should', 'may', 'might', 'must'}

    keywords = [w for w in english_words if w.lower() not in stop_words]

    return keywords

# 需要替換的代碼片段
OLD_CODE = """
            with conn_manager.neo4j_driver.session() as session:
                # 查詢藝術品和藝術家節點
                cypher_query = \"\"\"
                MATCH (a:Artwork)
                WHERE toLower(a.title) CONTAINS toLower($search_text)
                   OR toLower(COALESCE(a.description, '')) CONTAINS toLower($search_text)
                   OR toLower(COALESCE(a.date, '')) CONTAINS toLower($search_text)
                OPTIONAL MATCH (a)-[r]-(related)
                RETURN a as n, collect({rel: type(r), node: related}) as relationships
                LIMIT $limit

                UNION

                MATCH (artist:Artist)
                WHERE toLower(artist.name) CONTAINS toLower($search_text)
                OPTIONAL MATCH (artist)-[r:CREATED]->(artwork:Artwork)
                RETURN artist as n, collect({rel: type(r), node: artwork}) as relationships
                LIMIT $limit
                \"\"\"

                result = session.run(
                    cypher_query,
                    search_text=query,
                    limit=max_results
                )
"""

NEW_CODE = """
            # 從翻譯後的查詢中提取英文關鍵詞
            import re
            keywords = []
            # 提取英文單詞（至少2個字母）
            english_words = re.findall(r'\\b[a-zA-Z]{2,}\\b', query)
            # 移除停用詞
            stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                          'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were'}
            keywords = [w for w in english_words if w.lower() not in stop_words]

            # 如果沒有關鍵詞，使用原始查詢
            search_terms = keywords if keywords else [query]
            logger.info(f"提取的搜索關鍵詞: {search_terms}")

            with conn_manager.neo4j_driver.session() as session:
                all_documents = []

                for term in search_terms:
                    # 查詢藝術品和藝術家節點
                    cypher_query = \"\"\"
                    MATCH (a:Artwork)
                    WHERE toLower(a.title) CONTAINS toLower($search_text)
                       OR toLower(COALESCE(a.description, '')) CONTAINS toLower($search_text)
                       OR toLower(COALESCE(a.date, '')) CONTAINS toLower($search_text)
                    OPTIONAL MATCH (a)-[r]-(related)
                    RETURN a as n, collect({rel: type(r), node: related}) as relationships
                    LIMIT $limit

                    UNION

                    MATCH (artist:Artist)
                    WHERE toLower(artist.name) CONTAINS toLower($search_text)
                    OPTIONAL MATCH (artist)-[r:CREATED]->(artwork:Artwork)
                    RETURN artist as n, collect({rel: type(r), node: artwork}) as relationships
                    LIMIT $limit
                    \"\"\"

                    result = session.run(
                        cypher_query,
                        search_text=term,
                        limit=max_results
                    )

                    # 收集結果
                    for record in result:
                        node = record['n']
                        relationships = record['relationships']
                        content = self._format_graph_node(node, relationships)
                        all_documents.append({
                            'content': content,
                            'metadata': dict(node),
                            'score': 1.0,
                            'source': 'Neo4j Knowledge Graph'
                        })

                # 去重並限制結果數量
                seen_titles = set()
                documents = []
                for doc in all_documents:
                    title = doc['metadata'].get('title') or doc['metadata'].get('name')
                    if title and title not in seen_titles:
                        seen_titles.add(title)
                        documents.append(doc)
                        if len(documents) >= max_results:
                            break

                logger.info(f"圖譜檢索返回 {len(documents)} 個結果")
                return documents
"""

print("GraphOnlyRAG 修復代碼")
print("=" * 60)
print("\n需要在 RAG Manager 容器中修改 unified_rag_manager_v2.py")
print("\n修復說明:")
print("1. 從翻譯後的查詢中提取純英文關鍵詞")
print("2. 對每個關鍵詞分別查詢 Neo4j")
print("3. 去重並合併結果")
print("\n這樣可以處理像 'Leonardo da Vinci的masterpiece品有哪些' 這樣的混合語言查詢")
