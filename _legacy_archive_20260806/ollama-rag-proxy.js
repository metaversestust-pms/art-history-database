#!/usr/bin/env node
/**
 * Ollama RAG Proxy Server
 * 將 RAG+LLM 策略包裝成 Ollama 模型接口
 * 這樣 OpenWebUI 就可以直接使用，不需要 Function
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

        // RAG 策略映射
        this.ragStrategies = {
            'vector_rag': { strategy: 'vector_only', db: 'ChromaDB優先' },
            'graph_rag': { strategy: 'graph_only', db: 'Neo4j' },
            'hybrid_rag': { strategy: 'hybrid_balanced', db: 'Neo4j+ChromaDB' },
            'enhanced_rag': { strategy: 'enhanced_rag', db: 'Neo4j+ChromaDB' },
            'advanced_rag': { strategy: 'advanced_rag', db: 'ChromaDB優先' },
            'agentic_rag': { strategy: 'agentic_rag', db: 'ChromaDB優先' },
            'self_rag': { strategy: 'self_rag', db: 'ChromaDB優先' },
            'naive_rag': { strategy: 'naive_rag', db: 'ChromaDB' }
        };

        console.log('🚀 Ollama RAG Proxy 初始化完成');
        console.log(`📊 支援策略: ${Object.keys(this.ragStrategies).join(', ')}`);
    }

    parseModelName(modelName) {
        /**
         * 解析模型名稱，提取基礎模型和 RAG 策略
         * 例如: "llama3.1-vector_rag" -> { base: "llama3.1:8b", rag: "vector_rag" }
         */
        const parts = modelName.split('-');

        if (parts.length < 2) {
            return null;
        }

        const baseName = parts[0];
        const ragName = parts.slice(1).join('-');

        // 映射到完整模型名稱
        const baseModelMap = {
            'llama3.1': 'llama3.1:8b',
            'llama3': 'llama3.1:8b',
            'qwen2.5': 'qwen2.5:7b',
            'qwen': 'qwen2.5:7b',
            'gemma2': 'gemma2:2b',
            'gemma': 'gemma2:2b'
        };

        const baseModel = baseModelMap[baseName] || `${baseName}:latest`;

        if (!this.ragStrategies[ragName]) {
            return null;
        }

        return {
            base: baseModel,
            rag: ragName,
            strategy: this.ragStrategies[ragName].strategy,
            db: this.ragStrategies[ragName].db
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

    formatResponse(llmResponse, ragResults, modelInfo) {
        /**
         * 格式化最終回答，包含來源信息
         */
        let answer = llmResponse.response || '無法生成回答';

        // 添加來源信息
        answer += `\n\n---\n\n`;
        answer += `📊 **檢索信息**\n`;
        answer += `- 🔍 RAG 策略: ${modelInfo.rag}\n`;
        answer += `- 💾 資料庫: ${modelInfo.db}\n`;
        answer += `- 🤖 LLM 模型: ${modelInfo.base}\n`;

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
 * 處理生成請求，自動路由到 RAG + LLM
 */
app.post('/api/generate', async (req, res) => {
    try {
        const { model, prompt, stream = false } = req.body;

        console.log(`\n📥 收到請求: ${model}`);
        console.log(`📝 問題: ${prompt.substring(0, 100)}...`);

        // 解析模型名稱
        const modelInfo = proxy.parseModelName(model);

        if (!modelInfo) {
            // 不是 RAG 模型，直接轉發到 Ollama
            console.log(`   → 轉發到 Ollama (非 RAG 模型)`);
            const ollamaResponse = await axios.post(
                `${proxy.ollamaUrl}/api/generate`,
                req.body
            );
            return res.json(ollamaResponse.data);
        }

        console.log(`   → RAG 策略: ${modelInfo.strategy}`);
        console.log(`   → 基礎模型: ${modelInfo.base}`);

        // 步驟 1: RAG 檢索
        console.log(`   🔍 執行 RAG 檢索...`);
        const ragResults = await proxy.queryRAG(prompt, modelInfo.strategy);

        if (!ragResults) {
            return res.status(500).json({
                error: 'RAG 服務不可用'
            });
        }

        console.log(`   ✅ 檢索到 ${ragResults.sources?.length || 0} 個結果`);

        // 步驟 2: 構建 RAG 提示詞
        const ragPrompt = proxy.buildRAGPrompt(prompt, ragResults);

        // 步驟 3: LLM 生成
        console.log(`   🤖 使用 ${modelInfo.base} 生成回答...`);
        const llmResponse = await proxy.generateWithLLM(modelInfo.base, ragPrompt, stream);

        if (!llmResponse) {
            return res.status(500).json({
                error: 'LLM 生成失敗'
            });
        }

        // 步驟 4: 格式化回答
        const formattedAnswer = proxy.formatResponse(llmResponse, ragResults, modelInfo);

        console.log(`   ✅ 生成完成\n`);

        // 返回結果
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
        res.status(500).json({
            error: error.message
        });
    }
});

/**
 * Ollama API: /api/tags
 * 列出所有可用模型（包含 RAG 模型）
 */
app.get('/api/tags', async (req, res) => {
    try {
        // 獲取 Ollama 原始模型列表
        const ollamaResponse = await axios.get(`${proxy.ollamaUrl}/api/tags`);
        const models = ollamaResponse.data.models || [];

        // 添加 RAG 組合模型
        const baseModels = ['llama3.1', 'qwen2.5', 'gemma2'];
        const ragStrategies = Object.keys(proxy.ragStrategies);

        baseModels.forEach(base => {
            ragStrategies.forEach(rag => {
                const strategyInfo = proxy.ragStrategies[rag];
                models.push({
                    name: `${base}-${rag}:latest`,
                    modified_at: new Date().toISOString(),
                    size: 0,
                    digest: '',
                    details: {
                        format: 'gguf',
                        family: 'llama',
                        parameter_size: '8B',
                        quantization_level: 'Q4_0'
                    },
                    // 自定義標記，表示這是 RAG 模型
                    is_rag_model: true,
                    rag_strategy: rag,
                    rag_database: strategyInfo.db
                });
            });
        });

        res.json({ models });

    } catch (error) {
        console.error(`❌ 錯誤: ${error.message}`);
        res.status(500).json({
            error: error.message
        });
    }
});

/**
 * Ollama API: /api/chat
 * OpenWebUI 使用這個端點進行對話
 */
app.post('/api/chat', async (req, res) => {
    try {
        const { model, messages, stream = false } = req.body;

        // 提取最後一條用戶消息
        const lastMessage = messages[messages.length - 1];
        const prompt = lastMessage.content;

        console.log(`\n📥 收到聊天請求: ${model}`);
        console.log(`📝 問題: ${prompt.substring(0, 100)}...`);

        // 解析模型名稱
        const modelInfo = proxy.parseModelName(model);

        if (!modelInfo) {
            // 不是 RAG 模型，直接轉發到 Ollama
            console.log(`   → 轉發到 Ollama (非 RAG 模型)`);
            const ollamaResponse = await axios.post(
                `${proxy.ollamaUrl}/api/chat`,
                req.body
            );
            return res.json(ollamaResponse.data);
        }

        console.log(`   → RAG 策略: ${modelInfo.strategy}`);
        console.log(`   → 基礎模型: ${modelInfo.base}`);

        // 步驟 1: RAG 檢索
        console.log(`   🔍 執行 RAG 檢索...`);
        const ragResults = await proxy.queryRAG(prompt, modelInfo.strategy);

        if (!ragResults) {
            return res.status(500).json({
                error: 'RAG 服務不可用'
            });
        }

        console.log(`   ✅ 檢索到 ${ragResults.sources?.length || 0} 個結果`);

        // 步驟 2: 構建 RAG 提示詞
        const ragPrompt = proxy.buildRAGPrompt(prompt, ragResults);

        // 步驟 3: LLM 生成（使用 chat 格式）
        console.log(`   🤖 使用 ${modelInfo.base} 生成回答...`);

        // 構建 chat 消息
        const chatMessages = [
            ...messages.slice(0, -1),  // 保留歷史消息
            { role: 'user', content: ragPrompt }  // 使用增強的提示詞
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

        // 步驟 4: 格式化回答
        const llmAnswer = llmResponse.data.message?.content || llmResponse.data.response || '無法生成回答';

        let formattedAnswer = llmAnswer;
        formattedAnswer += `\n\n---\n\n`;
        formattedAnswer += `📊 **檢索信息**\n`;
        formattedAnswer += `- 🔍 RAG 策略: ${modelInfo.rag}\n`;
        formattedAnswer += `- 💾 資料庫: ${modelInfo.db}\n`;
        formattedAnswer += `- 🤖 LLM 模型: ${modelInfo.base}\n`;

        if (ragResults && ragResults.sources) {
            formattedAnswer += `- 📚 檢索來源: ${ragResults.sources.length} 個\n\n`;
            formattedAnswer += `**參考資料來源:**\n`;
            ragResults.sources.slice(0, 3).forEach((source, i) => {
                formattedAnswer += `${i + 1}. 📊 ${source.database.toUpperCase()} > ${source.source}\n`;
                formattedAnswer += `   🎯 相關度: ${source.score} | 方法: ${source.method}\n`;
            });
        }

        console.log(`   ✅ 生成完成\n`);

        // 返回結果（chat 格式）
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
        res.status(500).json({
            error: error.message
        });
    }
});

/**
 * Ollama API: /api/ps
 * 列出當前運行的模型
 */
app.get('/api/ps', async (req, res) => {
    try {
        // 轉發到真實的 Ollama
        const ollamaResponse = await axios.get(`${proxy.ollamaUrl}/api/ps`);
        res.json(ollamaResponse.data);
    } catch (error) {
        console.error(`❌ /api/ps 錯誤: ${error.message}`);
        // 返回空列表而不是錯誤
        res.json({ models: [] });
    }
});

/**
 * Ollama API: /api/version
 * 獲取 Ollama 版本信息
 */
app.get('/api/version', async (req, res) => {
    try {
        // 轉發到真實的 Ollama
        const ollamaResponse = await axios.get(`${proxy.ollamaUrl}/api/version`);
        res.json(ollamaResponse.data);
    } catch (error) {
        console.error(`❌ /api/version 錯誤: ${error.message}`);
        // 返回默認版本信息
        res.json({ version: '0.1.0' });
    }
});

/**
 * 健康檢查
 */
app.get('/health', (req, res) => {
    res.json({
        status: 'ok',
        service: 'ollama-rag-proxy',
        rag_server: proxy.ragServerUrl,
        ollama_server: proxy.ollamaUrl,
        strategies: Object.keys(proxy.ragStrategies)
    });
});

// 啟動服務器
const PORT = process.env.PROXY_PORT || 11435;  // 使用不同端口避免衝突
app.listen(PORT, () => {
    console.log('\n' + '='.repeat(60));
    console.log(`🚀 Ollama RAG Proxy Server 啟動成功！`);
    console.log(`📡 監聽端口: ${PORT}`);
    console.log(`🔗 健康檢查: http://localhost:${PORT}/health`);
    console.log(`📚 模型列表: http://localhost:${PORT}/api/tags`);
    console.log('='.repeat(60) + '\n');

    console.log('💡 使用方法:');
    console.log(`   1. 在 OpenWebUI 設置中添加 Ollama 連接:`);
    console.log(`      http://localhost:${PORT}`);
    console.log(`   2. 選擇 RAG+LLM 組合模型（例如: llama3.1-vector_rag）`);
    console.log(`   3. 開始提問！`);
    console.log('');
});

module.exports = { OllamaRAGProxy, app };
