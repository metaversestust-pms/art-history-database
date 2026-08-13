#!/usr/bin/env node
/**
 * Ollama RAG Proxy Server with Neo4j Graph Visualization
 * 將 RAG+LLM 策略包裝成 Ollama 模型接口 + 自動添加知識圖譜
 *
 * 🆕 新增功能:
 * - 自動從用戶問題和 RAG 結果中提取實體
 * - 查詢 Neo4j 獲取關係圖譜
 * - 生成 Mermaid 圖表並添加到回答中
 * - 只對 graph_rag, hybrid_rag, advanced_rag, agentic_rag 啟用圖譜
 */

const express = require('express');
const axios = require('axios');

const app = express();
app.use(express.json());

class OllamaRAGProxy {
    constructor() {
        // Ollama API
        this.ollamaUrl = 'http://localhost:11434';

        // 多資料庫 RAG 服務器
        this.ragServerUrl = 'http://localhost:8010';

        // 🆕 Neo4j 配置
        this.neo4jUrl = 'http://localhost:7474';
        this.neo4jAuth = Buffer.from('neo4j:arthistory123').toString('base64');

        // RAG 策略映射
        this.ragStrategies = {
            'vector_rag': { strategy: 'vector_only', db: 'ChromaDB優先', showGraph: false },
            'graph_rag': { strategy: 'graph_only', db: 'Neo4j', showGraph: true },
            'hybrid_rag': { strategy: 'hybrid_balanced', db: 'Neo4j+ChromaDB', showGraph: true },
            'enhanced_rag': { strategy: 'enhanced_rag', db: 'Neo4j+ChromaDB', showGraph: true },
            'advanced_rag': { strategy: 'advanced_rag', db: 'ChromaDB優先', showGraph: true },
            'agentic_rag': { strategy: 'agentic_rag', db: 'ChromaDB優先', showGraph: true },
            'self_rag': { strategy: 'self_rag', db: 'ChromaDB優先', showGraph: false },
            'naive_rag': { strategy: 'naive_rag', db: 'ChromaDB', showGraph: false }
        };

        console.log('🚀 Ollama RAG Proxy (with Graph Viz) 初始化完成');
        console.log(`📊 支援策略: ${Object.keys(this.ragStrategies).join(', ')}`);
        console.log(`🕸️ 圖譜視覺化: ${Object.entries(this.ragStrategies).filter(([k,v]) => v.showGraph).map(([k]) => k).join(', ')}`);
    }

    // ============ 原有方法 ============

    parseModelName(modelName) {
        /**
         * 解析模型名稱，提取基礎模型和 RAG 策略
         */
        // 支持兩種格式:
        // 1. llama3.1-vector_rag (舊格式,來自 proxy)
        // 2. llama31-vector-rag (新格式,來自 create_full_rag_models.sh)

        const parts = modelName.split('-');

        if (parts.length < 2) {
            return null;
        }

        const baseName = parts[0];
        const ragName = parts.slice(1).join('-').replace(/_/g, '-');  // 統一為 -

        // 映射到完整模型名稱
        const baseModelMap = {
            'llama3.1': 'llama3.1:8b',
            'llama31': 'llama3.1:8b',
            'llama3': 'llama3.1:8b',
            'qwen3': 'qwen3:4b',
            'qwen3-8b': 'qwen3:8b',
            'qwen2.5': 'qwen2.5:7b',
            'qwen': 'qwen2.5:7b',
            'deepseek': 'deepseek-r1:8b',
            'gemma3': 'gemma3:4b',
            'gemma2': 'gemma2:2b',
            'gemma': 'gemma2:2b'
        };

        const baseModel = baseModelMap[baseName] || `${baseName}:latest`;

        // 嘗試匹配 RAG 策略 (支持 - 和 _)
        const normalizedRagName = ragName.replace(/-/g, '_');

        if (!this.ragStrategies[normalizedRagName]) {
            return null;
        }

        return {
            base: baseModel,
            rag: normalizedRagName,
            strategy: this.ragStrategies[normalizedRagName].strategy,
            db: this.ragStrategies[normalizedRagName].db,
            showGraph: this.ragStrategies[normalizedRagName].showGraph
        };
    }

    async queryRAG(query, strategy, topK = 5) {
        /**
         * 查詢 RAG 服務器
         */
        try {
            const response = await axios.post(
                `${this.ragServerUrl}/query`,
                {
                    query: query,
                    strategy: strategy,
                    top_k: topK
                },
                { timeout: 30000 }
            );

            return response.data;
        } catch (error) {
            console.error(`❌ RAG 查詢失敗: ${error.message}`);
            return null;
        }
    }

    async generateWithLLM(baseModel, prompt, stream = false) {
        /**
         * 使用基礎 LLM 生成回答
         */
        try {
            const response = await axios.post(
                `${this.ollamaUrl}/api/generate`,
                {
                    model: baseModel,
                    prompt: prompt,
                    stream: stream
                },
                { timeout: 60000 }
            );

            return response.data;
        } catch (error) {
            console.error(`❌ LLM 生成失敗: ${error.message}`);
            return null;
        }
    }

    buildRAGPrompt(userQuery, ragResults) {
        /**
         * 構建包含 RAG 上下文的提示詞
         */
        let prompt = `基於以下檢索到的藝術史資料，回答用戶的問題。\n\n`;

        // 添加檢索上下文
        if (ragResults && ragResults.context) {
            prompt += `【參考資料】\n${ragResults.context}\n\n`;
        }

        // 添加用戶問題
        prompt += `【用戶問題】\n${userQuery}\n\n`;

        // 添加指導
        prompt += `【回答要求】\n`;
        prompt += `1. 基於上述參考資料回答問題\n`;
        prompt += `2. 引用具體的藝術家、作品名稱\n`;
        prompt += `3. 保持專業和準確\n`;
        prompt += `4. 如果資料不足以回答，請誠實說明\n\n`;
        prompt += `【回答】\n`;

        return prompt;
    }

    // ============ 🆕 圖譜相關方法 ============

    extractEntitiesFromText(text) {
        /**
         * 從文本中提取實體名稱
         */
        const entities = new Set();

        // 提取常見藝術家名稱 (中文和英文)
        const artistPatterns = [
            /(達文西|米開朗基羅|拉斐爾|提香|卡拉瓦喬|杜勒)/gi,
            /(Leonardo da Vinci|Michelangelo|Raphael|Titian|Caravaggio|Dürer)/gi,
            /(莫內|梵谷|畢卡索|塞尚|雷諾瓦|高更)/gi,
            /(Monet|Van Gogh|Picasso|Cézanne|Renoir|Gauguin)/gi,
        ];

        artistPatterns.forEach(pattern => {
            const matches = text.match(pattern) || [];
            matches.forEach(m => entities.add(m));
        });

        // 提取作品名稱 (帶引號或書名號)
        const artworkPattern = /[《「『]([^》」』]+)[》」』]|"([^"]+)"|'([^']+)'/g;
        let match;
        while ((match = artworkPattern.exec(text)) !== null) {
            const name = match[1] || match[2] || match[3];
            if (name && name.length > 2) {
                entities.add(name);
            }
        }

        // 提取大寫開頭的專有名詞 (英文)
        const properNounPattern = /\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b/g;
        while ((match = properNounPattern.exec(text)) !== null) {
            const name = match[1];
            if (name.length > 3 && !['The', 'And', 'For', 'With'].includes(name)) {
                entities.add(name);
            }
        }

        return Array.from(entities).slice(0, 10);  // 限制數量
    }

    async queryNeo4jGraph(entityNames, maxDepth = 2) {
        /**
         * 查詢 Neo4j 獲取實體關係圖譜
         */
        if (!entityNames || entityNames.length === 0) {
            return { nodes: [], edges: [] };
        }

        const cypherQuery = `
            MATCH (source)
            WHERE source.name IN $entity_names
               OR source.title IN $entity_names
            OPTIONAL MATCH path = (source)-[r*1..2]-(related)
            WITH source, relationships(path) as rels
            UNWIND rels as rel
            WITH DISTINCT source, rel, startNode(rel) as start, endNode(rel) as end
            RETURN
                collect(DISTINCT {
                    id: id(source),
                    label: labels(source)[0],
                    name: coalesce(source.name, source.title, '未知')
                }) as source_nodes,
                collect(DISTINCT {
                    id: id(start),
                    label: labels(start)[0],
                    name: coalesce(start.name, start.title, '未知')
                }) +
                collect(DISTINCT {
                    id: id(end),
                    label: labels(end)[0],
                    name: coalesce(end.name, end.title, '未知')
                }) as all_nodes,
                collect(DISTINCT {
                    source: id(start),
                    target: id(end),
                    relationship: type(rel)
                }) as edges
        `;

        try {
            const response = await axios.post(
                `${this.neo4jUrl}/db/neo4j/tx/commit`,
                {
                    statements: [{
                        statement: cypherQuery,
                        parameters: { entity_names: entityNames }
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

            if (response.status === 200 && response.data.results && response.data.results[0].data.length > 0) {
                const data = response.data.results[0].data[0].row;

                // 合併並去重節點
                const nodesDict = {};
                [data[0], data[1]].forEach(nodeList => {
                    nodeList.forEach(node => {
                        const nodeId = node.id;
                        if (nodeId && !nodesDict[nodeId]) {
                            nodesDict[nodeId] = node;
                        }
                    });
                });

                return {
                    nodes: Object.values(nodesDict).slice(0, 15),  // 限制節點數
                    edges: data[2].slice(0, 30),  // 限制關係數
                    entity_count: Object.keys(nodesDict).length,
                    relationship_count: data[2].length
                };
            }

            return { nodes: [], edges: [] };

        } catch (error) {
            console.error(`❌ Neo4j 查詢失敗: ${error.message}`);
            return { nodes: [], edges: [], error: error.message };
        }
    }

    formatMermaidGraph(graphData) {
        /**
         * 生成 Mermaid 圖表
         */
        if (!graphData || !graphData.nodes || graphData.nodes.length === 0) {
            return '';
        }

        const lines = ['```mermaid', 'graph TD'];

        // 節點定義
        const nodeMap = {};
        graphData.nodes.forEach((node, i) => {
            const nodeId = `N${i}`;
            const label = node.label || 'Entity';
            const name = (node.name || '未知').substring(0, 20);

            let style;
            if (label === 'Artist') {
                style = `${nodeId}[👨‍🎨 ${name}]`;
            } else if (label === 'Artwork') {
                style = `${nodeId}[🖼️ ${name}]`;
            } else if (label === 'Style') {
                style = `${nodeId}{🎨 ${name}}`;
            } else if (label === 'Period') {
                style = `${nodeId}{📅 ${name}}`;
            } else if (label === 'Museum') {
                style = `${nodeId}[🏛️ ${name}]`;
            } else {
                style = `${nodeId}[${name}]`;
            }

            lines.push(`    ${style}`);
            nodeMap[node.id] = nodeId;
        });

        // 邊定義
        const relTranslations = {
            'CREATED': '創作',
            'INFLUENCED': '影響',
            'BELONGS_TO': '屬於',
            'EXHIBITED_AT': '展出於',
            'STUDIED_UNDER': '師從',
            'CONTEMPORARY_OF': '同時代',
            'LOCATED_IN': '位於',
            'PART_OF': '屬於時期'
        };

        graphData.edges.forEach(edge => {
            const source = nodeMap[edge.source];
            const target = nodeMap[edge.target];
            const relType = edge.relationship || 'related';

            if (source && target) {
                const relLabel = relTranslations[relType] || relType;
                lines.push(`    ${source} -->|${relLabel}| ${target}`);
            }
        });

        lines.push('```');

        // 添加圖例
        const legend = `\n\n### 📊 知識圖譜關係圖\n\n` +
            `> **找到 ${graphData.entity_count || 0} 個實體, ${graphData.relationship_count || 0} 個關係**\n\n` +
            `> 💡 **圖例**: 👨‍🎨 藝術家 | 🖼️ 作品 | 🎨 風格 | 📅 時期 | 🏛️ 博物館\n\n`;

        return legend + lines.join('\n');
    }

    async formatResponse(llmResponse, ragResults, modelInfo, userQuery) {
        /**
         * 🆕 增強版: 格式化最終回答,包含來源信息和圖譜
         */
        let answer = llmResponse.response || '無法生成回答';

        // 🆕 如果啟用圖譜,添加知識圖譜
        if (modelInfo.showGraph) {
            console.log(`   🕸️ 生成知識圖譜...`);

            // 從用戶問題和 RAG 結果中提取實體
            let entities = this.extractEntitiesFromText(userQuery);

            // 如果從問題中提取的實體不夠,嘗試從 RAG 結果中提取
            if (entities.length === 0 && ragResults && ragResults.context) {
                entities = this.extractEntitiesFromText(ragResults.context);
            }

            console.log(`      提取的實體: ${entities.join(', ')}`);

            if (entities.length > 0) {
                // 查詢圖譜
                const graphData = await this.queryNeo4jGraph(entities, 2);

                if (graphData.nodes && graphData.nodes.length > 0) {
                    const mermaidGraph = this.formatMermaidGraph(graphData);
                    answer += `\n\n---\n${mermaidGraph}`;
                    console.log(`      ✅ 圖譜已添加 (${graphData.nodes.length} 個節點)`);
                } else {
                    console.log(`      ⚠️ 未找到圖譜數據`);
                }
            } else {
                console.log(`      ⚠️ 未提取到實體`);
            }
        }

        // 添加來源信息
        answer += `\n\n---\n\n`;
        answer += `📊 **檢索信息**\n`;
        answer += `- 🔍 RAG 策略: ${modelInfo.rag}\n`;
        answer += `- 💾 資料庫: ${modelInfo.db}\n`;
        answer += `- 🤖 LLM 模型: ${modelInfo.base}\n`;
        answer += `- 🕸️ 圖譜視覺化: ${modelInfo.showGraph ? '✅ 啟用' : '❌ 未啟用'}\n`;

        if (ragResults && ragResults.sources) {
            answer += `- 📚 檢索來源: ${ragResults.sources.length} 個\n\n`;

            // 添加詳細來源
            answer += `**參考資料來源:**\n`;
            ragResults.sources.slice(0, 3).forEach((source, i) => {
                answer += `${i + 1}. 📊 ${source.database.toUpperCase()} > ${source.source}\n`;
                answer += `   🎯 相關度: ${source.score} | 方法: ${source.method}\n`;
            });
        }

        return answer;
    }
}

// 創建代理實例
const proxy = new OllamaRAGProxy();

// API 路由

/**
 * Ollama API: /api/generate
 */
app.post('/api/generate', async (req, res) => {
    try {
        const { model, prompt, stream = false } = req.body;

        console.log(`\n📥 收到請求: ${model}`);
        console.log(`📝 問題: ${prompt.substring(0, 100)}...`);

        const modelInfo = proxy.parseModelName(model);

        if (!modelInfo) {
            console.log(`   → 轉發到 Ollama (非 RAG 模型)`);
            const ollamaResponse = await axios.post(
                `${proxy.ollamaUrl}/api/generate`,
                req.body
            );
            return res.json(ollamaResponse.data);
        }

        console.log(`   → RAG 策略: ${modelInfo.strategy}`);
        console.log(`   → 基礎模型: ${modelInfo.base}`);
        console.log(`   → 圖譜視覺化: ${modelInfo.showGraph ? '✅ 啟用' : '❌ 未啟用'}`);

        // RAG 檢索
        console.log(`   🔍 執行 RAG 檢索...`);
        const ragResults = await proxy.queryRAG(prompt, modelInfo.strategy);

        if (!ragResults) {
            return res.status(500).json({ error: 'RAG 服務不可用' });
        }

        console.log(`   ✅ 檢索到 ${ragResults.sources?.length || 0} 個結果`);

        // 構建提示詞
        const ragPrompt = proxy.buildRAGPrompt(prompt, ragResults);

        // LLM 生成
        console.log(`   🤖 使用 ${modelInfo.base} 生成回答...`);
        const llmResponse = await proxy.generateWithLLM(modelInfo.base, ragPrompt, stream);

        if (!llmResponse) {
            return res.status(500).json({ error: 'LLM 生成失敗' });
        }

        // 🆕 格式化回答 (包含圖譜)
        const formattedAnswer = await proxy.formatResponse(llmResponse, ragResults, modelInfo, prompt);

        console.log(`   ✅ 生成完成\n`);

        res.json({
            model: model,
            created_at: new Date().toISOString(),
            response: formattedAnswer,
            done: true,
            context: llmResponse.context,
            total_duration: llmResponse.total_duration,
            load_duration: llmResponse.load_duration,
            prompt_eval_count: llmResponse.prompt_eval_count,
            eval_count: llmResponse.eval_count
        });

    } catch (error) {
        console.error(`❌ 錯誤: ${error.message}`);
        res.status(500).json({ error: error.message });
    }
});

/**
 * Ollama API: /api/chat
 * OpenWebUI 主要使用這個端點
 */
app.post('/api/chat', async (req, res) => {
    try {
        const { model, messages, stream = false } = req.body;

        const lastMessage = messages[messages.length - 1];
        const prompt = lastMessage.content;

        console.log(`\n📥 收到聊天請求: ${model}`);
        console.log(`📝 問題: ${prompt.substring(0, 100)}...`);

        const modelInfo = proxy.parseModelName(model);

        if (!modelInfo) {
            console.log(`   → 轉發到 Ollama (非 RAG 模型)`);
            const ollamaResponse = await axios.post(
                `${proxy.ollamaUrl}/api/chat`,
                req.body
            );
            return res.json(ollamaResponse.data);
        }

        console.log(`   → RAG 策略: ${modelInfo.strategy}`);
        console.log(`   → 基礎模型: ${modelInfo.base}`);
        console.log(`   → 圖譜視覺化: ${modelInfo.showGraph ? '✅ 啟用' : '❌ 未啟用'}`);

        // RAG 檢索
        console.log(`   🔍 執行 RAG 檢索...`);
        const ragResults = await proxy.queryRAG(prompt, modelInfo.strategy);

        if (!ragResults) {
            return res.status(500).json({ error: 'RAG 服務不可用' });
        }

        console.log(`   ✅ 檢索到 ${ragResults.sources?.length || 0} 個結果`);

        // 構建 RAG 提示詞
        const ragPrompt = proxy.buildRAGPrompt(prompt, ragResults);

        // LLM 生成 (chat 格式)
        console.log(`   🤖 使用 ${modelInfo.base} 生成回答...`);

        const chatMessages = [
            ...messages.slice(0, -1),
            { role: 'user', content: ragPrompt }
        ];

        const llmResponse = await axios.post(
            `${proxy.ollamaUrl}/api/chat`,
            {
                model: modelInfo.base,
                messages: chatMessages,
                stream: stream
            },
            { timeout: 60000 }
        );

        // 提取LLM回答
        const llmAnswer = llmResponse.data.message?.content || llmResponse.data.response || '無法生成回答';

        // 🆕 構造包含圖譜的完整回答
        const llmResponseForFormat = { response: llmAnswer };
        const formattedAnswer = await proxy.formatResponse(llmResponseForFormat, ragResults, modelInfo, prompt);

        console.log(`   ✅ 生成完成\n`);

        res.json({
            model: model,
            created_at: new Date().toISOString(),
            message: {
                role: 'assistant',
                content: formattedAnswer
            },
            done: true,
            total_duration: llmResponse.data.total_duration,
            load_duration: llmResponse.data.load_duration,
            prompt_eval_count: llmResponse.data.prompt_eval_count,
            eval_count: llmResponse.data.eval_count
        });

    } catch (error) {
        console.error(`❌ 錯誤: ${error.message}`);
        res.status(500).json({ error: error.message });
    }
});

/**
 * Ollama API: /api/tags
 */
app.get('/api/tags', async (req, res) => {
    try {
        const ollamaResponse = await axios.get(`${proxy.ollamaUrl}/api/tags`);
        const models = ollamaResponse.data.models || [];

        // 可選: 添加虛擬 RAG 模型到列表
        // (如果您想在 OpenWebUI 中直接看到 RAG 模型選項)

        res.json({ models });

    } catch (error) {
        console.error(`❌ 錯誤: ${error.message}`);
        res.status(500).json({ error: error.message });
    }
});

/**
 * 其他 Ollama API 端點
 */
app.get('/api/ps', async (req, res) => {
    try {
        const ollamaResponse = await axios.get(`${proxy.ollamaUrl}/api/ps`);
        res.json(ollamaResponse.data);
    } catch (error) {
        res.json({ models: [] });
    }
});

app.get('/api/version', async (req, res) => {
    try {
        const ollamaResponse = await axios.get(`${proxy.ollamaUrl}/api/version`);
        res.json(ollamaResponse.data);
    } catch (error) {
        res.json({ version: '0.1.0' });
    }
});

/**
 * 健康檢查
 */
app.get('/health', (req, res) => {
    res.json({
        status: 'ok',
        service: 'ollama-rag-proxy-with-graph',
        version: '2.0.0',
        features: ['RAG', 'Graph Visualization'],
        rag_server: proxy.ragServerUrl,
        ollama_server: proxy.ollamaUrl,
        neo4j_server: proxy.neo4jUrl,
        strategies: Object.keys(proxy.ragStrategies),
        graph_enabled_strategies: Object.entries(proxy.ragStrategies)
            .filter(([k,v]) => v.showGraph)
            .map(([k]) => k)
    });
});

// 啟動服務器
const PORT = process.env.PROXY_PORT || 11435;
app.listen(PORT, () => {
    console.log('\n' + '='.repeat(70));
    console.log(`🚀 Ollama RAG Proxy Server (with Graph Viz) 啟動成功！`);
    console.log(`📡 監聽端口: ${PORT}`);
    console.log(`🔗 健康檢查: http://localhost:${PORT}/health`);
    console.log('='.repeat(70) + '\n');

    console.log('💡 使用方法:');
    console.log(`   1. 在 OpenWebUI 設置中將 Ollama 連接改為:`);
    console.log(`      http://localhost:${PORT}`);
    console.log(`   2. 選擇您創建的 RAG 模型 (例如: llama31-graph-rag)`);
    console.log(`   3. 開始提問,圖譜會自動顯示！`);
    console.log('');
    console.log('🕸️ 圖譜啟用策略: graph-rag, hybrid-rag, advanced-rag, agentic-rag');
    console.log('');
});

module.exports = { OllamaRAGProxy, app };
