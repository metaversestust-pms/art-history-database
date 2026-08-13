#!/usr/bin/env node
/**
 * 將Renaissance和Baroque資料匯入Neo4j
 */

const neo4j = require('neo4j-driver');
const fs = require('fs');
const path = require('path');

// Neo4j連線設定
const NEO4J_URI = process.env.NEO4J_URI || 'bolt://localhost:7687';
const NEO4J_USER = process.env.NEO4J_USER || 'neo4j';
const NEO4J_PASSWORD = process.env.NEO4J_PASSWORD || 'arthistory123';

class Neo4jImporter {
    constructor() {
        this.driver = neo4j.driver(
            NEO4J_URI,
            neo4j.auth.basic(NEO4J_USER, NEO4J_PASSWORD)
        );
        this.stats = {
            artworks: 0,
            artists: 0,
            periods: 0,
            relationships: 0,
            errors: 0
        };
    }

    async connect() {
        try {
            const session = this.driver.session();
            await session.run('RETURN 1');
            await session.close();
            console.log('✅ Neo4j連接成功');
            return true;
        } catch (error) {
            console.error('❌ Neo4j連接失敗:', error.message);
            return false;
        }
    }

    async importRenaissanceBaroqueData(filePath) {
        console.log(`\n🔄 開始匯入: ${path.basename(filePath)}`);

        // 讀取資料
        const rawData = fs.readFileSync(filePath, 'utf-8');
        const artworks = JSON.parse(rawData);

        console.log(`📊 總共 ${artworks.length} 件作品`);

        const session = this.driver.session();

        try {
            // 創建索引以提升效能
            await this.createIndexes(session);

            // 處理每件作品
            for (let i = 0; i < artworks.length; i++) {
                const artwork = artworks[i];

                try {
                    await this.importArtwork(session, artwork);

                    if ((i + 1) % 50 === 0) {
                        console.log(`   ✓ 已處理 ${i + 1}/${artworks.length} 件作品`);
                    }
                } catch (error) {
                    this.stats.errors++;
                    console.error(`   ⚠️ 處理作品失敗 (ID: ${artwork.id}):`, error.message);
                }
            }

            console.log(`\n✅ 匯入完成！`);
            console.log(`📈 統計:`);
            console.log(`   - 藝術作品: ${this.stats.artworks}`);
            console.log(`   - 藝術家: ${this.stats.artists}`);
            console.log(`   - 時期: ${this.stats.periods}`);
            console.log(`   - 關係: ${this.stats.relationships}`);
            console.log(`   - 錯誤: ${this.stats.errors}`);

        } finally {
            await session.close();
        }
    }

    async createIndexes(session) {
        const indexes = [
            'CREATE INDEX IF NOT EXISTS FOR (a:Artwork) ON (a.met_id)',
            'CREATE INDEX IF NOT EXISTS FOR (a:Artist) ON (a.name)',
            'CREATE INDEX IF NOT EXISTS FOR (p:Period) ON (p.name)',
            'CREATE INDEX IF NOT EXISTS FOR (m:Museum) ON (m.name)'
        ];

        for (const indexQuery of indexes) {
            try {
                await session.run(indexQuery);
            } catch (error) {
                // 索引可能已存在，忽略錯誤
            }
        }
    }

    async importArtwork(session, artwork) {
        // 1. 創建藝術作品節點
        const artworkProps = {
            met_id: String(artwork.id || ''),
            title: this.cleanText(artwork.title || 'Unknown'),
            date: artwork.date || '',
            begin_date: artwork.beginDate || null,
            end_date: artwork.endDate || null,
            medium: artwork.medium || '',
            dimensions: artwork.dimensions || '',
            culture: artwork.culture || '',
            department: artwork.department || '',
            classification: artwork.classification || '',
            period: artwork.period || '',
            primary_image: artwork.primaryImage || '',
            primary_image_small: artwork.primaryImageSmall || '',
            object_url: artwork.objectURL || '',
            is_highlight: artwork.isHighlight || false,
            accession_year: artwork.accessionYear || '',
            accession_number: artwork.accessionNumber || '',
            country: artwork.country || '',
            region: artwork.region || '',
            source: 'Metropolitan Museum of Art',
            crawled_at: artwork.crawledAt || new Date().toISOString()
        };

        await session.run(`
            MERGE (artwork:Artwork {met_id: $met_id})
            SET artwork += $props
        `, {
            met_id: artworkProps.met_id,
            props: artworkProps
        });

        this.stats.artworks++;

        // 2. 創建藝術家並建立關係
        const artistName = this.cleanText(artwork.artist || '');
        if (artistName && artistName !== 'Unknown Artist' && artistName !== 'Unknown') {
            const artistProps = {
                name: artistName,
                role: artwork.artistRole || 'Artist',
                nationality: artwork.artistNationality || '',
                birth_year: artwork.artistBeginDate || '',
                death_year: artwork.artistEndDate || '',
                source: 'Met Museum'
            };

            await session.run(`
                MERGE (artist:Artist {name: $name})
                SET artist += $props
            `, {
                name: artistName,
                props: artistProps
            });

            await session.run(`
                MATCH (artist:Artist {name: $artist_name})
                MATCH (artwork:Artwork {met_id: $met_id})
                MERGE (artist)-[:CREATED]->(artwork)
            `, {
                artist_name: artistName,
                met_id: artworkProps.met_id
            });

            this.stats.artists++;
            this.stats.relationships++;
        }

        // 3. 創建時期節點並建立關係
        const period = artwork.period || '';
        if (period && (period === 'Renaissance' || period === 'Baroque')) {
            await session.run(`
                MERGE (period:Period {name: $name})
                SET period.type = $type,
                    period.description = $description
            `, {
                name: period,
                type: 'Historical Period',
                description: period === 'Renaissance'
                    ? '文藝復興時期 (約1400-1600)'
                    : '巴洛克時期 (約1600-1750)'
            });

            await session.run(`
                MATCH (artwork:Artwork {met_id: $met_id})
                MATCH (period:Period {name: $period_name})
                MERGE (artwork)-[:FROM_PERIOD]->(period)
            `, {
                met_id: artworkProps.met_id,
                period_name: period
            });

            this.stats.periods++;
            this.stats.relationships++;
        }

        // 4. 創建博物館/部門節點
        const department = artwork.department || '';
        if (department) {
            const museumName = `Met Museum - ${department}`;
            await session.run(`
                MERGE (museum:Museum {name: $name})
                SET museum.type = 'Department',
                    museum.full_name = 'Metropolitan Museum of Art',
                    museum.location = 'New York, USA'
            `, {
                name: museumName
            });

            await session.run(`
                MATCH (artwork:Artwork {met_id: $met_id})
                MATCH (museum:Museum {name: $museum_name})
                MERGE (artwork)-[:HOUSED_IN]->(museum)
            `, {
                met_id: artworkProps.met_id,
                museum_name: museumName
            });

            this.stats.relationships++;
        }
    }

    cleanText(text) {
        if (!text) return '';
        return text.toString().trim();
    }

    async close() {
        await this.driver.close();
    }

    async getStatistics() {
        const session = this.driver.session();
        try {
            const result = await session.run(`
                MATCH (n)
                RETURN labels(n) as labels, count(n) as count
                ORDER BY count DESC
            `);

            console.log('\n📊 Neo4j資料庫統計:');
            result.records.forEach(record => {
                const label = record.get('labels')[0] || 'Unknown';
                const count = record.get('count').toNumber();
                console.log(`   ${label}: ${count}`);
            });

            const relResult = await session.run(`
                MATCH ()-[r]->()
                RETURN type(r) as type, count(r) as count
                ORDER BY count DESC
            `);

            console.log('\n關係統計:');
            relResult.records.forEach(record => {
                const type = record.get('type');
                const count = record.get('count').toNumber();
                console.log(`   ${type}: ${count}`);
            });

        } finally {
            await session.close();
        }
    }
}

async function main() {
    console.log('🎨 Renaissance & Baroque 資料匯入 Neo4j');
    console.log('========================================\n');

    const importer = new Neo4jImporter();

    // 連接Neo4j
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
        .sort((a, b) => b.size - a.size); // 按檔案大小排序

    if (files.length === 0) {
        console.error('❌ 找不到renaissance_baroque資料檔');
        process.exit(1);
    }

    const latestFile = path.join(dataDir, files[0].name);
    console.log(`📁 使用檔案: ${files[0].name} (${(files[0].size / 1024).toFixed(2)} KB)\n`);

    try {
        // 匯入資料
        await importer.importRenaissanceBaroqueData(latestFile);

        // 顯示統計
        await importer.getStatistics();

        console.log('\n🎉 全部完成！');

    } catch (error) {
        console.error('\n❌ 匯入失敗:', error);
    } finally {
        await importer.close();
    }
}

if (require.main === module) {
    main().catch(console.error);
}

module.exports = Neo4jImporter;
