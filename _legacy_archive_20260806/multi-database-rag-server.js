#!/usr/bin/env node
/**
 * 多資料庫 RAG 服務器
 * 根據 RAG 策略自動選擇 Neo4j 或 ChromaDB 或兩者
 */

const express = require('express');
const axios = require('axios');
const cors = require('cors');

const app = express();
app.use(cors());
app.use(express.json());

class MultiDatabaseRAGServer {
    constructor() {
        // Neo4j 配置
        this.neo4jUrl = 'http://localhost:7474';
        this.neo4jAuth = Buffer.from('neo4j:arthistory123').toString('base64');

        // ChromaDB 配置
        this.chromaUrl = 'http://localhost:8001';
        this.chromaCollectionId = 'aa7a55a2-924e-41b0-a0f7-9b5c031477a4';

        // Ollama 配置
        this.ollamaUrl = 'http://localhost:11434';
        this.embeddingModel = 'nomic-embed-text';

        // 策略-資料源映射
        this.strategyMapping = {
            'enhanced_rag': ['neo4j', 'chromadb'],
            'vector_only': ['chromadb', 'neo4j'],      // ChromaDB 優先
            'graph_only': ['neo4j'],
            'hybrid_balanced': ['neo4j', 'chromadb'],
            'advanced_rag': ['chromadb', 'neo4j'],     // ChromaDB 優先
            'agentic_rag': ['chromadb', 'neo4j'],      // ChromaDB 優先
            'self_rag': ['chromadb', 'neo4j'],         // ChromaDB 優先
            'naive_rag': ['chromadb']                  // 只用 ChromaDB
        };

        console.log('🚀 多資料庫 RAG 服務器初始化完成');
        console.log(`📊 支援策略: ${Object.keys(this.strategyMapping).join(', ')}`);
    }

    async generateEmbedding(text) {
        /**
         * 使用 Ollama 生成嵌入向量
         */
        try {
            const response = await axios.post(
                `${this.ollamaUrl}/api/embeddings`,
                {
                    model: this.embeddingModel,
                    prompt: text
                },
                { timeout: 30000 }
            );

            return response.data.embedding;
        } catch (error) {
            console.error(`❌ 生成 embedding 失敗: ${error.message}`);
            return null;
        }
    }

    async queryChromaDB(query, topK = 5) {
        /**
         * 查詢 ChromaDB
         */
        try {
            // 生成查詢向量
            const queryEmbedding = await this.generateEmbedding(query);
            if (!queryEmbedding) {
                return [];
            }

            // 查詢 ChromaDB
            const response = await axios.post(
                `${this.chromaUrl}/api/v2/tenants/default_tenant/databases/default_database/collections/${this.chromaCollectionId}/query`,
                {
                    query_embeddings: [queryEmbedding],
                    n_results: topK,
                    include: ['metadatas', 'documents', 'distances']
                },
                { timeout: 10000 }
            );

            const { documents, metadatas, distances } = response.data;

            // 格式化結果
            const results = documents[0].map((doc, i) => ({
                content: doc,
                score: (1 / (1 + distances[0][i])).toFixed(3),
                retrieval_method: 'vector',
                source_database: 'chromadb',
                source_collection: 'art_history_collection',
                source_type: 'artwork',
                original_source: metadatas[0][i].collection || 'Met Museum API',
                metadata: metadatas[0][i]
            }));

            console.log(`✅ ChromaDB: 找到 ${results.length} 個結果`);
            return results;

        } catch (error) {
            console.error(`❌ ChromaDB 查詢失敗: ${error.message}`);
            return [];
        }
    }

    async queryNeo4jVector(query, topK = 5) {
        /**
         * Neo4j 向量搜索
         */
        try {
            const queryEmbedding = await this.generateEmbedding(query);
            if (!queryEmbedding) {
                return [];
            }

            // 搜索藝術家
            const cypherQuery = `
                CALL db.index.vector.queryNodes('artist_name_embeddings', $topK, $embedding)
                YIELD node, score
                RETURN node.name as name,
                       node.biography as biography,
                       node.original_source as original_source,
                       'Artist' as type,
                       score
                LIMIT $topK
            `;

            const response = await axios.post(
                `${this.neo4jUrl}/db/neo4j/tx/commit`,
                {
                    statements: [{
                        statement: cypherQuery,
                        parameters: {
                            embedding: queryEmbedding,
                            topK: topK
                        },
                        resultDataContents: ['row']
                    }]
                },
                {
                    headers: {
                        'Authorization': `Basic ${this.neo4jAuth}`,
                        'Content-Type': 'application/json'
                    },
                    timeout: 10000
                }
            );

            if (response.data.errors && response.data.errors.length > 0) {
                console.error('Neo4j 錯誤:', response.data.errors);
                return [];
            }

            const results = response.data.results[0].data.map(item => {
                const [name, biography, original_source, type, score] = item.row;
                return {
                    content: `${name}: ${biography || ''}`.substring(0, 300),
                    score: score.toFixed(3),
                    retrieval_method: 'vector',
                    source_database: 'neo4j',
                    source_collection: 'graph_database',
                    source_type: type,
                    original_source: original_source || 'Internal Knowledge Base',
                    metadata: { name, type }
                };
            });

            console.log(`✅ Neo4j Vector: 找到 ${results.length} 個結果`);
            return results;

        } catch (error) {
            console.error(`❌ Neo4j Vector 查詢失敗: ${error.message}`);
            return [];
        }
    }

    async queryNeo4jFulltext(query, topK = 5) {
        /**
         * Neo4j 全文搜索
         */
        try {
            const cypherQuery = `
                CALL db.index.fulltext.queryNodes('artist_fulltext', $query)
                YIELD node, score
                RETURN node.name as name,
                       node.biography as biography,
                       node.original_source as original_source,
                       'Artist' as type,
                       score
                ORDER BY score DESC
                LIMIT $topK
            `;

            const response = await axios.post(
                `${this.neo4jUrl}/db/neo4j/tx/commit`,
                {
                    statements: [{
                        statement: cypherQuery,
                        parameters: {
                            query: query,
                            topK: topK
                        },
                        resultDataContents: ['row']
                    }]
                },
                {
                    headers: {
                        'Authorization': `Basic ${this.neo4jAuth}`,
                        'Content-Type': 'application/json'
                    },
                    timeout: 10000
                }
            );

            if (response.data.errors && response.data.errors.length > 0) {
                console.error('Neo4j 錯誤:', response.data.errors);
                return [];
            }

            const results = response.data.results[0].data.map(item => {
                const [name, biography, original_source, type, score] = item.row;
                return {
                    content: `${name}: ${biography || ''}`.substring(0, 300),
                    score: score.toFixed(3),
                    retrieval_method: 'fulltext',
                    source_database: 'neo4j',
                    source_collection: 'graph_database',
                    source_type: type,
                    original_source: original_source || 'Internal Knowledge Base',
                    metadata: { name, type }
                };
            });

            console.log(`✅ Neo4j Fulltext: 找到 ${results.length} 個結果`);
            return results;

        } catch (error) {
            console.error(`❌ Neo4j Fulltext 查詢失敗: ${error.message}`);
            return [];
        }
    }

    async routeQuery(query, strategy = 'hybrid_balanced', topK = 5) {
        /**
         * 路由查詢到適當的資料源
         */
        console.log(`\n🔀 路由查詢: "${query}" | 策略: ${strategy}`);

        const sources = this.strategyMapping[strategy] || ['neo4j'];
        console.log(`📊 使用資料源: ${sources.join(', ')}`);

        const allResults = [];

        // 並行查詢
        const tasks = [];

        if (sources.includes('chromadb')) {
            tasks.push(this.queryChromaDB(query, topK));
        }

        if (sources.includes('neo4j')) {
            tasks.push(this.queryNeo4jVector(query, topK));
            tasks.push(this.queryNeo4jFulltext(query, topK));
        }

        const results = await Promise.all(tasks);

        // 合併結果
        results.forEach(r => allResults.push(...r));

        // 去重並排序
        const uniqueResults = this.deduplicate(allResults);
        const sortedResults = uniqueResults
            .sort((a, b) => parseFloat(b.score) - parseFloat(a.score))
            .slice(0, topK);

        // 統計
        const sourceStats = {};
        sortedResults.forEach(r => {
            sourceStats[r.source_database] = (sourceStats[r.source_database] || 0) + 1;
        });

        console.log(`📊 資料源分布: ${JSON.stringify(sourceStats)}`);
        console.log(`✅ 總共返回 ${sortedResults.length} 個結果\n`);

        return sortedResults;
    }

    deduplicate(results) {
        /**
         * 去重結果（基於內容前 50 個字符）
         */
        const seen = new Set();
        const unique = [];

        for (const result of results) {
            const key = result.content.substring(0, 50);
            if (!seen.has(key)) {
                seen.add(key);
                unique.push(result);
            }
        }

        return unique;
    }

    formatResultsForLLM(results) {
        /**
         * 格式化結果供 LLM 使用
         */
        let context = '';
        const sources = [];

        results.forEach((result, i) => {
            // 構建 context
            context += `\n[來源 ${i + 1}] (${result.source_database} > ${result.original_source})\n`;
            context += `${result.content}\n`;

            // 構建 sources
            sources.push({
                rank: i + 1,
                database: result.source_database,
                source: result.original_source,
                method: result.retrieval_method,
                score: result.score,
                content: result.content
            });
        });

        return {
            context,
            sources,
            metadata: {
                total_results: results.length,
                databases_used: [...new Set(results.map(r => r.source_database))],
                source_distribution: results.reduce((acc, r) => {
                    acc[r.source_database] = (acc[r.source_database] || 0) + 1;
                    return acc;
                }, {})
            }
        };
    }
}

// 創建服務器實例
const ragServer = new MultiDatabaseRAGServer();

// API 端點
app.post('/query', async (req, res) => {
    try {
        const { query, strategy = 'hybrid_balanced', top_k = 5 } = req.body;

        if (!query) {
            return res.status(400).json({ error: '缺少 query 參數' });
        }

        console.log(`\n${'='.repeat(60)}`);
        console.log(`收到查詢: ${query}`);
        console.log(`策略: ${strategy}, top_k: ${top_k}`);
        console.log('='.repeat(60));

        // 執行檢索
        const results = await ragServer.routeQuery(query, strategy, top_k);

        // 格式化結果
        const formatted = ragServer.formatResultsForLLM(results);

        res.json({
            success: true,
            query,
            strategy,
            ...formatted
        });

    } catch (error) {
        console.error('❌ 查詢錯誤:', error);
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// 健康檢查
app.get('/health', (req, res) => {
    res.json({
        status: 'ok',
        server: 'multi-database-rag-server',
        version: '1.0',
        strategies: Object.keys(ragServer.strategyMapping)
    });
});

// 啟動服務器
const PORT = process.env.PORT || 8010;
app.listen(PORT, () => {
    console.log('\n' + '='.repeat(60));
    console.log(`🚀 多資料庫 RAG 服務器啟動成功！`);
    console.log(`📡 監聽端口: ${PORT}`);
    console.log(`🔗 健康檢查: http://localhost:${PORT}/health`);
    console.log(`📚 查詢端點: http://localhost:${PORT}/query`);
    console.log('='.repeat(60) + '\n');

    console.log('💡 使用範例:');
    console.log(`   curl -X POST http://localhost:${PORT}/query \\`);
    console.log(`     -H "Content-Type: application/json" \\`);
    console.log(`     -d '{"query": "達文西的作品", "strategy": "vector_only", "top_k": 5}'`);
    console.log('');
});

module.exports = { MultiDatabaseRAGServer, app };
