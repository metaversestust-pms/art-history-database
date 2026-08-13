#!/usr/bin/env node
/**
 * 將Renaissance和Baroque資料匯入ChromaDB向量資料庫
 */

const { ChromaClient } = require('chromadb');
const fs = require('fs');
const path = require('path');

// ChromaDB設定
const CHROMA_URL = process.env.CHROMA_URL || 'http://localhost:8001';
const COLLECTION_NAME = 'art_history_renaissance_baroque';

class ChromaDBImporter {
    constructor() {
        this.client = new ChromaClient({ path: CHROMA_URL });
        this.collection = null;
        this.stats = {
            imported: 0,
            skipped: 0,
            errors: 0
        };
    }

    async connect() {
        try {
            // 測試連接
            await this.client.heartbeat();
            console.log('✅ ChromaDB連接成功');

            // 獲取或創建集合
            try {
                this.collection = await this.client.getOrCreateCollection({
                    name: COLLECTION_NAME,
                    metadata: {
                        description: 'Renaissance and Baroque period artworks',
                        source: 'Metropolitan Museum of Art',
                        created_at: new Date().toISOString()
                    }
                });
                console.log(`✅ 使用集合: ${COLLECTION_NAME}`);
            } catch (error) {
                console.log(`創建新集合: ${COLLECTION_NAME}`);
                this.collection = await this.client.createCollection({
                    name: COLLECTION_NAME,
                    metadata: {
                        description: 'Renaissance and Baroque period artworks',
                        source: 'Metropolitan Museum of Art',
                        created_at: new Date().toISOString()
                    }
                });
            }

            return true;
        } catch (error) {
            console.error('❌ ChromaDB連接失敗:', error.message);
            return false;
        }
    }

    async importRenaissanceBaroqueData(filePath) {
        console.log(`\n🔄 開始匯入: ${path.basename(filePath)}`);

        // 讀取資料
        const rawData = fs.readFileSync(filePath, 'utf-8');
        const artworks = JSON.parse(rawData);

        console.log(`📊 總共 ${artworks.length} 件作品`);

        // 批次處理（每批100件）
        const batchSize = 100;
        for (let i = 0; i < artworks.length; i += batchSize) {
            const batch = artworks.slice(i, Math.min(i + batchSize, artworks.length));
            await this.importBatch(batch, i);

            console.log(`   ✓ 已處理 ${Math.min(i + batchSize, artworks.length)}/${artworks.length} 件作品`);
        }

        console.log(`\n✅ 匯入完成！`);
        console.log(`📈 統計:`);
        console.log(`   - 成功匯入: ${this.stats.imported}`);
        console.log(`   - 跳過: ${this.stats.skipped}`);
        console.log(`   - 錯誤: ${this.stats.errors}`);

        // 顯示集合統計
        const count = await this.collection.count();
        console.log(`\n📊 ChromaDB集合統計:`);
        console.log(`   ${COLLECTION_NAME}: ${count} 項`);
    }

    async importBatch(artworks, startIndex) {
        const ids = [];
        const documents = [];
        const metadatas = [];

        for (const artwork of artworks) {
            try {
                // 生成唯一ID
                const id = `met_${artwork.id}_${Date.now()}_${startIndex}`;

                // 創建文本文檔（用於向量化）
                const document = this.createDocument(artwork);

                // 創建元資料
                const metadata = this.createMetadata(artwork);

                ids.push(id);
                documents.push(document);
                metadatas.push(metadata);

                this.stats.imported++;

            } catch (error) {
                this.stats.errors++;
                console.error(`   ⚠️ 處理作品失敗 (ID: ${artwork.id}):`, error.message);
            }
        }

        // 批次加入到ChromaDB
        if (ids.length > 0) {
            try {
                await this.collection.add({
                    ids: ids,
                    documents: documents,
                    metadatas: metadatas
                });
            } catch (error) {
                console.error(`   ❌ 批次匯入失敗:`, error.message);
                this.stats.errors += ids.length;
            }
        }
    }

    createDocument(artwork) {
        // 創建豐富的文本描述以生成更好的向量嵌入
        const parts = [];

        // 標題
        if (artwork.title) {
            parts.push(`Title: ${artwork.title}`);
        }

        // 藝術家
        if (artwork.artist && artwork.artist !== 'Unknown Artist') {
            parts.push(`Artist: ${artwork.artist}`);
            if (artwork.artistNationality) {
                parts.push(`Artist Nationality: ${artwork.artistNationality}`);
            }
        }

        // 時期
        if (artwork.period) {
            parts.push(`Period: ${artwork.period}`);
        }

        // 日期
        if (artwork.date) {
            parts.push(`Date: ${artwork.date}`);
        }

        // 媒材
        if (artwork.medium) {
            parts.push(`Medium: ${artwork.medium}`);
        }

        // 尺寸
        if (artwork.dimensions) {
            parts.push(`Dimensions: ${artwork.dimensions}`);
        }

        // 文化
        if (artwork.culture) {
            parts.push(`Culture: ${artwork.culture}`);
        }

        // 部門
        if (artwork.department) {
            parts.push(`Department: ${artwork.department}`);
        }

        // 分類
        if (artwork.classification) {
            parts.push(`Classification: ${artwork.classification}`);
        }

        // 國家/地區
        if (artwork.country) {
            parts.push(`Country: ${artwork.country}`);
        }
        if (artwork.region) {
            parts.push(`Region: ${artwork.region}`);
        }

        // 標籤
        if (artwork.tags && artwork.tags.length > 0) {
            const tagTerms = artwork.tags.map(tag => tag.term || tag).filter(Boolean);
            if (tagTerms.length > 0) {
                parts.push(`Tags: ${tagTerms.join(', ')}`);
            }
        }

        return parts.join('. ');
    }

    createMetadata(artwork) {
        // 過濾掉null和undefined值
        const metadata = {};

        if (artwork.id) metadata.met_id = String(artwork.id);
        if (artwork.title) metadata.title = this.truncate(artwork.title, 500);
        if (artwork.artist) metadata.artist = this.truncate(artwork.artist, 200);
        if (artwork.date) metadata.date = this.truncate(artwork.date, 100);
        if (artwork.period) metadata.period = artwork.period;
        if (artwork.medium) metadata.medium = this.truncate(artwork.medium, 300);
        if (artwork.culture) metadata.culture = this.truncate(artwork.culture, 100);
        if (artwork.department) metadata.department = this.truncate(artwork.department, 100);
        if (artwork.classification) metadata.classification = this.truncate(artwork.classification, 100);
        if (artwork.country) metadata.country = this.truncate(artwork.country, 100);
        if (artwork.isHighlight !== undefined) metadata.is_highlight = artwork.isHighlight;
        if (artwork.primaryImage) metadata.has_image = true;
        if (artwork.objectURL) metadata.url = artwork.objectURL;

        // 添加時間範圍（用於過濾）
        if (artwork.beginDate && !isNaN(artwork.beginDate)) {
            metadata.begin_year = parseInt(artwork.beginDate);
        }
        if (artwork.endDate && !isNaN(artwork.endDate)) {
            metadata.end_year = parseInt(artwork.endDate);
        }

        metadata.source = 'Metropolitan Museum of Art';
        metadata.crawled_at = artwork.crawledAt || new Date().toISOString();

        return metadata;
    }

    truncate(str, maxLength) {
        if (!str) return '';
        str = String(str);
        return str.length > maxLength ? str.substring(0, maxLength) + '...' : str;
    }

    async testQuery(query = 'Renaissance painting') {
        console.log(`\n🔍 測試查詢: "${query}"`);

        const results = await this.collection.query({
            queryTexts: [query],
            nResults: 5
        });

        console.log(`📊 找到 ${results.ids[0].length} 項結果:`);

        for (let i = 0; i < results.ids[0].length; i++) {
            const metadata = results.metadatas[0][i];
            const distance = results.distances[0][i];

            console.log(`\n   ${i + 1}. ${metadata.title}`);
            console.log(`      藝術家: ${metadata.artist || 'Unknown'}`);
            console.log(`      時期: ${metadata.period || 'Unknown'}`);
            console.log(`      日期: ${metadata.date || 'Unknown'}`);
            console.log(`      相似度: ${(1 - distance).toFixed(4)}`);
        }
    }
}

async function main() {
    console.log('🎨 Renaissance & Baroque 資料匯入 ChromaDB');
    console.log('============================================\n');

    const importer = new ChromaDBImporter();

    // 連接ChromaDB
    const connected = await importer.connect();
    if (!connected) {
        process.exit(1);
    }

    // 找到最大的renaissance_baroque資料檔
    const dataDir = './data/raw';
    const files = fs.readdirSync(dataDir)
        .filter(f => f.startsWith('renaissance_baroque_') && f.endsWith('.json'))
        .map(f => ({
            name: f,
            size: fs.statSync(path.join(dataDir, f)).size
        }))
        .sort((a, b) => b.size - a.size);

    if (files.length === 0) {
        console.error('❌ 找不到renaissance_baroque資料檔');
        process.exit(1);
    }

    const latestFile = path.join(dataDir, files[0].name);
    console.log(`📁 使用檔案: ${files[0].name} (${(files[0].size / 1024).toFixed(2)} KB)\n`);

    try {
        // 匯入資料
        await importer.importRenaissanceBaroqueData(latestFile);

        // 測試查詢
        await importer.testQuery('Renaissance painting by Leonardo da Vinci');
        await importer.testQuery('Baroque sculpture');

        console.log('\n🎉 全部完成！');

    } catch (error) {
        console.error('\n❌ 匯入失敗:', error);
        console.error(error.stack);
    }
}

if (require.main === module) {
    main().catch(console.error);
}

module.exports = ChromaDBImporter;
