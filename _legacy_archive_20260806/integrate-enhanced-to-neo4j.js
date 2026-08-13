#!/usr/bin/env node
/**
 * 將增強後的藝術史資料整合到Neo4j
 * 包含中文標籤和語義標籤
 */

const neo4j = require('neo4j-driver');
const fs = require('fs');
const path = require('path');

class EnhancedNeo4jIntegrator {
    constructor() {
        console.log('🎨 增強版Neo4j資料整合工具');
        console.log('═══════════════════════════════════════\n');

        // Neo4j連接配置
        this.neo4jUri = process.env.NEO4J_URI || 'bolt://localhost:7687';
        this.neo4jUser = process.env.NEO4J_USER || 'neo4j';
        this.neo4jPassword = process.env.NEO4J_PASSWORD || 'arthistory123';

        this.driver = null;
        this.stats = {
            total: 0,
            processed: 0,
            with_chinese_labels: 0,
            with_period_tags: 0,
            errors: 0
        };
    }

    async connect() {
        try {
            this.driver = neo4j.driver(
                this.neo4jUri,
                neo4j.auth.basic(this.neo4jUser, this.neo4jPassword)
            );

            // 測試連接
            await this.driver.verifyConnectivity();
            console.log('✅ Neo4j連接成功\n');

            return true;
        } catch (error) {
            console.error('❌ Neo4j連接失敗:', error.message);
            return false;
        }
    }

    async processArtwork(artwork) {
        const session = this.driver.session();

        try {
            // 1. 創建或更新Artwork節點
            await session.run(`
                MERGE (a:Artwork {id: $id})
                SET a.title = $title,
                    a.artist = $artist,
                    a.date = $date,
                    a.medium = $medium,
                    a.culture = $culture,
                    a.period = $period,
                    a.has_chinese_labels = $has_chinese,
                    a.source = $source,
                    a.updated_at = datetime()
            `, {
                id: String(artwork.id || hash(artwork)),
                title: artwork.title || 'Untitled',
                artist: artwork.artist || 'Unknown',
                date: String(artwork.date || ''),
                medium: String(artwork.medium || '').substring(0, 1000),
                culture: String(artwork.culture || ''),
                period: String(artwork.period || ''),
                has_chinese: Boolean(artwork.artist_chinese || artwork.search_text_chinese),
                source: 'enhanced'
            });

            // 2. 如果有藝術家，創建Artist節點
            if (artwork.artist && artwork.artist !== 'Unknown') {
                await session.run(`
                    MERGE (artist:Artist {name: $artist_name})
                    SET artist.name_en = $artist_name,
                        artist.name_zh = $artist_chinese
                    WITH artist
                    MATCH (artwork:Artwork {id: $artwork_id})
                    MERGE (artist)-[:CREATED]->(artwork)
                `, {
                    artist_name: artwork.artist,
                    artist_chinese: artwork.artist_chinese ? artwork.artist_chinese.join(', ') : null,
                    artwork_id: String(artwork.id || hash(artwork))
                });

                if (artwork.artist_chinese) {
                    this.stats.with_chinese_labels++;
                }
            }

            // 3. 如果有時期標籤，創建Period節點
            if (artwork.period_tags && artwork.period_tags.en) {
                for (const periodEn of artwork.period_tags.en) {
                    const periodZh = artwork.period_tags.zh ? artwork.period_tags.zh.join(', ') : '';

                    await session.run(`
                        MERGE (period:Period {name: $period_name})
                        SET period.name_en = $period_name,
                            period.name_zh = $period_zh
                        WITH period
                        MATCH (artwork:Artwork {id: $artwork_id})
                        MERGE (artwork)-[:BELONGS_TO_PERIOD]->(period)
                    `, {
                        period_name: periodEn,
                        period_zh: periodZh,
                        artwork_id: String(artwork.id || hash(artwork))
                    });

                    this.stats.with_period_tags++;
                }
            }

            // 4. 如果有類型標籤，創建Type節點
            if (artwork.type_tags && artwork.type_tags.en) {
                for (const typeEn of artwork.type_tags.en.slice(0, 3)) { // 限制數量
                    const typeZh = artwork.type_tags.zh ? artwork.type_tags.zh.slice(0, 3).join(', ') : '';

                    await session.run(`
                        MERGE (type:ArtType {name: $type_name})
                        SET type.name_en = $type_name,
                            type.name_zh = $type_zh
                        WITH type
                        MATCH (artwork:Artwork {id: $artwork_id})
                        MERGE (artwork)-[:OF_TYPE]->(type)
                    `, {
                        type_name: typeEn,
                        type_zh: typeZh,
                        artwork_id: String(artwork.id || hash(artwork))
                    });
                }
            }

            this.stats.processed++;

        } catch (error) {
            console.error(`   ⚠️ 處理作品失敗 (ID: ${artwork.id}):`, error.message);
            this.stats.errors++;
        } finally {
            await session.close();
        }
    }

    async processFile(filePath) {
        console.log(`\n📂 處理文件: ${path.basename(filePath)}`);

        try {
            const data = JSON.parse(fs.readFileSync(filePath, 'utf8'));

            console.log(`   📊 找到 ${data.length} 件作品`);
            this.stats.total += data.length;

            // 批次處理（每10件顯示進度）
            for (let i = 0; i < data.length; i++) {
                await this.processArtwork(data[i]);

                if ((i + 1) % 10 === 0) {
                    process.stdout.write(`\r   ✓ 已處理 ${i + 1}/${data.length} 件作品`);
                }
            }

            console.log(`\r   ✅ 完成處理 ${data.length} 件作品`);

        } catch (error) {
            console.error(`   ❌ 處理文件失敗:`, error.message);
        }
    }

    async run() {
        console.log('🚀 開始增強版Neo4j資料整合...\n');

        try {
            // 連接Neo4j
            const connected = await this.connect();
            if (!connected) {
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

            console.log('\n✨ 資料整合完成！');
            console.log('\n下一步：');
            console.log('  1. 測試中文查詢:');
            console.log('     curl -X POST http://localhost:8008/query \\');
            console.log('       -H "Content-Type: application/json" \\');
            console.log('       -d \'{"query": "達文西的作品", "strategy": "graph_only"}\'');
            console.log('');
            console.log('  2. 在OpenWebUI測試: http://localhost:8080');

        } catch (error) {
            console.error('\n❌ 執行失敗:', error);
        } finally {
            if (this.driver) {
                await this.driver.close();
            }
        }
    }

    printStats() {
        console.log('\n\n═══════════════════════════════════════');
        console.log('📊 資料整合統計');
        console.log('═══════════════════════════════════════');
        console.log(`總作品數: ${this.stats.total}`);
        console.log(`成功處理: ${this.stats.processed}`);
        console.log(`包含中文標籤: ${this.stats.with_chinese_labels} (${(this.stats.with_chinese_labels/this.stats.processed*100).toFixed(1)}%)`);
        console.log(`包含時期標籤: ${this.stats.with_period_tags} (${(this.stats.with_period_tags/this.stats.processed*100).toFixed(1)}%)`);
        console.log(`錯誤: ${this.stats.errors}`);
        console.log('═══════════════════════════════════════');
    }
}

function hash(obj) {
    return Math.abs(JSON.stringify(obj).split('').reduce((a, b) => {
        a = ((a << 5) - a) + b.charCodeAt(0);
        return a & a;
    }, 0));
}

async function main() {
    const integrator = new EnhancedNeo4jIntegrator();
    await integrator.run();
}

if (require.main === module) {
    main().catch(console.error);
}

module.exports = EnhancedNeo4jIntegrator;
