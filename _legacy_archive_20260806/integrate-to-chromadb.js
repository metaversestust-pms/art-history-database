#!/usr/bin/env node
/**
 * 將增強後的藝術史資料整合到ChromaDB
 * 使用ChromaDB v2 HTTP API和Ollama embedding
 */

const axios = require('axios');
const fs = require('fs');
const path = require('path');

class ChromaDBIntegrator {
    constructor() {
        console.log('🎨 ChromaDB資料整合工具');
        console.log('═══════════════════════════════════════\n');

        this.chromaBaseUrl = 'http://localhost:8001';
        this.tenant = 'default_tenant';
        this.database = 'default_database';
        this.chromaUrl = `${this.chromaBaseUrl}/api/v2/tenants/${this.tenant}/databases/${this.database}`;
        this.ollamaUrl = 'http://localhost:11434';
        this.collectionName = 'art_history_collection';  // 使用未初始化的collection
        this.embeddingModel = 'nomic-embed-text';

        this.stats = {
            total: 0,
            processed: 0,
            with_chinese_labels: 0,
            errors: 0,
            embeddings_generated: 0
        };
    }

    async initialize() {
        console.log('🔧 初始化ChromaDB集合...\n');

        try {
            // 檢查集合是否存在並獲取ID
            const collections = await axios.get(`${this.chromaUrl}/collections`);
            const existingCollection = collections.data.find(c => c.name === this.collectionName);

            if (existingCollection) {
                console.log(`⚠️  集合 "${this.collectionName}" 已存在`);
                this.collectionId = existingCollection.id;

                // 清空集合而非刪除（保留collection ID）
                console.log(`   清空現有集合 (ID: ${this.collectionId})...`);
                // ChromaDB v2沒有直接的clear方法，我們使用現有集合
            } else {
                // 創建新集合
                const createResponse = await axios.post(`${this.chromaUrl}/collections`, {
                    name: this.collectionName,
                    metadata: {
                        description: 'Enhanced art history database with Chinese labels',
                        created_at: new Date().toISOString()
                    }
                });

                this.collectionId = createResponse.data.id;
            }

            console.log(`✅ 集合準備完成 (ID: ${this.collectionId})\n`);
            return true;

        } catch (error) {
            console.error('❌ 初始化失敗:', error.message);
            if (error.response) {
                console.error('   響應數據:', JSON.stringify(error.response.data, null, 2));
            }
            return false;
        }
    }

    async generateEmbedding(text) {
        try {
            const response = await axios.post(`${this.ollamaUrl}/api/embeddings`, {
                model: this.embeddingModel,
                prompt: text
            });

            this.stats.embeddings_generated++;
            return response.data.embedding;

        } catch (error) {
            console.error(`   ⚠️  生成embedding失敗: ${error.message}`);
            return null;
        }
    }

    createTextRepresentation(artwork) {
        const parts = [];

        // 標題
        if (artwork.title) {
            parts.push(`Title: ${artwork.title}`);
        }

        // 藝術家
        if (artwork.artist) {
            parts.push(`Artist: ${artwork.artist}`);
        }

        // 藝術家中文
        if (artwork.artist_chinese && artwork.artist_chinese.length > 0) {
            parts.push(`藝術家: ${artwork.artist_chinese.join(', ')}`);
        }

        // 時期
        if (artwork.period) {
            parts.push(`Period: ${artwork.period}`);
        }

        // 時期中文
        if (artwork.period_tags && artwork.period_tags.zh) {
            parts.push(`時期: ${artwork.period_tags.zh.join(', ')}`);
        }

        // 年代
        if (artwork.date) {
            parts.push(`Date: ${artwork.date}`);
        }

        // 類型
        if (artwork.classification) {
            parts.push(`Type: ${artwork.classification}`);
        }

        // 類型中文
        if (artwork.type_tags && artwork.type_tags.zh) {
            parts.push(`類型: ${artwork.type_tags.zh.join(', ')}`);
        }

        // 材料
        if (artwork.medium) {
            parts.push(`Medium: ${artwork.medium.substring(0, 200)}`);
        }

        // 材料中文
        if (artwork.material_tags && artwork.material_tags.zh) {
            parts.push(`材料: ${artwork.material_tags.zh.join(', ')}`);
        }

        // 描述
        if (artwork.description) {
            parts.push(`Description: ${artwork.description.substring(0, 500)}`);
        }

        // 收藏
        if (artwork.collection) {
            parts.push(`Collection: ${artwork.collection}`);
        }

        // 地點
        if (artwork.location) {
            parts.push(`Location: ${artwork.location}`);
        }

        return parts.join('\n');
    }

    async processArtwork(artwork, index) {
        try {
            // 創建文本表示
            const text = this.createTextRepresentation(artwork);

            // 生成embedding
            const embedding = await this.generateEmbedding(text);
            if (!embedding) {
                this.stats.errors++;
                return false;
            }

            // 準備metadata
            const metadata = {
                title: String(artwork.title || 'Untitled'),
                artist: String(artwork.artist || 'Unknown'),
                date: String(artwork.date || ''),
                period: String(artwork.period || ''),
                medium: String(artwork.medium || '').substring(0, 500),
                classification: String(artwork.classification || ''),
                culture: String(artwork.culture || ''),
                collection: String(artwork.collection || ''),
                has_chinese: Boolean(artwork.artist_chinese || artwork.search_text_chinese),
                source: 'enhanced'
            };

            // 添加到ChromaDB (使用collection UUID)
            const addResponse = await axios.post(
                `${this.chromaUrl}/collections/${this.collectionId}/add`,
                {
                    ids: [`artwork_${index}_${Date.now()}`],
                    embeddings: [embedding],
                    metadatas: [metadata],
                    documents: [text]
                }
            );

            if (artwork.artist_chinese || artwork.search_text_chinese) {
                this.stats.with_chinese_labels++;
            }

            this.stats.processed++;
            return true;

        } catch (error) {
            console.error(`   ⚠️  處理作品失敗: ${error.message}`);
            this.stats.errors++;
            return false;
        }
    }

    async processFile(filePath) {
        console.log(`\n📂 處理文件: ${path.basename(filePath)}`);

        try {
            const data = JSON.parse(fs.readFileSync(filePath, 'utf8'));
            console.log(`   📊 找到 ${data.length} 件作品`);
            this.stats.total += data.length;

            let startIndex = this.stats.processed;

            // 批次處理（每5件作品顯示進度）
            for (let i = 0; i < data.length; i++) {
                await this.processArtwork(data[i], startIndex + i);

                if ((i + 1) % 5 === 0) {
                    process.stdout.write(`\r   ✓ 已處理 ${i + 1}/${data.length} 件作品 (生成 ${this.stats.embeddings_generated} 個向量)`);
                }

                // 避免過快請求Ollama
                if ((i + 1) % 10 === 0) {
                    await this.delay(500);
                }
            }

            console.log(`\r   ✅ 完成處理 ${data.length} 件作品                    `);

        } catch (error) {
            console.error(`   ❌ 處理文件失敗:`, error.message);
        }
    }

    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    async run() {
        console.log('🚀 開始ChromaDB資料整合...\n');

        try {
            // 初始化ChromaDB集合
            const initialized = await this.initialize();
            if (!initialized) {
                process.exit(1);
            }

            // 查找所有增強後的資料文件
            const dataDir = path.join(__dirname, 'data', 'enhanced');
            const files = fs.readdirSync(dataDir)
                .filter(f => (f.startsWith('enhanced_renaissance_baroque') || f.startsWith('enhanced_masterpieces')) && f.endsWith('.json'))
                .map(f => path.join(dataDir, f));

            console.log(`📁 找到 ${files.length} 個增強後的資料文件\n`);

            if (files.length === 0) {
                console.log('⚠️  沒有找到增強後的資料文件');
                return;
            }

            // 處理每個文件
            for (const file of files) {
                await this.processFile(file);
            }

            // 顯示統計
            this.printStats();

            console.log('\n✨ ChromaDB資料整合完成！');
            console.log('\n下一步：');
            console.log('  1. 測試向量檢索:');
            console.log('     curl -X POST http://localhost:8008/query \\');
            console.log('       -H "Content-Type: application/json" \\');
            console.log('       -d \'{"query": "達文西的作品", "strategy": "vector_only"}\'');
            console.log('');
            console.log('  2. 測試混合檢索:');
            console.log('     curl -X POST http://localhost:8008/query \\');
            console.log('       -H "Content-Type: application/json" \\');
            console.log('       -d \'{"query": "文藝復興時期的繪畫", "strategy": "hybrid_balanced"}\'');
            console.log('');
            console.log('  3. 在OpenWebUI測試: http://localhost:8080');

        } catch (error) {
            console.error('\n❌ 執行失敗:', error);
        }
    }

    printStats() {
        console.log('\n\n═══════════════════════════════════════');
        console.log('📊 ChromaDB整合統計');
        console.log('═══════════════════════════════════════');
        console.log(`總作品數: ${this.stats.total}`);
        console.log(`成功處理: ${this.stats.processed}`);
        console.log(`包含中文標籤: ${this.stats.with_chinese_labels} (${(this.stats.with_chinese_labels/this.stats.processed*100).toFixed(1)}%)`);
        console.log(`生成向量: ${this.stats.embeddings_generated}`);
        console.log(`錯誤: ${this.stats.errors}`);
        console.log(`成功率: ${(this.stats.processed/this.stats.total*100).toFixed(1)}%`);
        console.log('═══════════════════════════════════════');
    }
}

async function main() {
    const integrator = new ChromaDBIntegrator();
    await integrator.run();
}

if (require.main === module) {
    main().catch(console.error);
}

module.exports = ChromaDBIntegrator;
