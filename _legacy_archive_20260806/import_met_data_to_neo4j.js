#!/usr/bin/env node
/**
 * MET Museum 資料匯入 Neo4j 腳本
 * 從爬蟲資料直接匯入到 Neo4j 圖資料庫
 */

const neo4j = require('neo4j-driver');
const fs = require('fs');
const path = require('path');

// Neo4j 連接配置
const NEO4J_URI = 'bolt://localhost:7687';
const NEO4J_USER = 'neo4j';
const NEO4J_PASSWORD = 'arthistory123';

class MetDataImporter {
    constructor() {
        this.driver = neo4j.driver(NEO4J_URI, neo4j.auth.basic(NEO4J_USER, NEO4J_PASSWORD));
        this.session = null;
    }

    async connect() {
        try {
            this.session = this.driver.session();
            // 測試連接
            await this.session.run('RETURN 1');
            console.log('✅ 成功連接到 Neo4j');
            return true;
        } catch (error) {
            console.error('❌ Neo4j 連接失敗:', error.message);
            return false;
        }
    }

    async importMetData(filename = 'met_museum_2025-09-26T01-24-10-991Z.json') {
        const dataPath = path.join(__dirname, 'data', 'raw', filename);

        try {
            // 讀取 MET 資料
            const rawData = fs.readFileSync(dataPath, 'utf8');
            const artworks = JSON.parse(rawData);
            console.log(`📚 讀取到 ${artworks.length} 件藝術品資料`);

            // 清理現有資料（可選）
            await this.session.run('MATCH (n) DETACH DELETE n');
            console.log('🗑️ 清理舊資料');

            let importedCount = 0;

            // 批量匯入資料
            for (const artwork of artworks) {
                try {
                    await this.importSingleArtwork(artwork);
                    importedCount++;

                    if (importedCount % 10 === 0) {
                        console.log(`📈 已匯入 ${importedCount} 件作品...`);
                    }
                } catch (error) {
                    console.error(`⚠️ 匯入作品失敗 (ID: ${artwork.id}):`, error.message);
                }
            }

            console.log(`✅ 成功匯入 ${importedCount} 件藝術品到 Neo4j`);

            // 建立索引
            await this.createIndexes();

            // 統計資料
            await this.showStatistics();

        } catch (error) {
            console.error('❌ 資料匯入失敗:', error.message);
        }
    }

    async importSingleArtwork(artwork) {
        const query = `
            // 建立藝術品節點
            MERGE (a:Artwork {id: $id})
            SET a.title = $title,
                a.date = $date,
                a.medium = $medium,
                a.department = $department,
                a.culture = $culture,
                a.period = $period,
                a.dimensions = $dimensions,
                a.classification = $classification,
                a.primaryImage = $primaryImage,
                a.objectURL = $objectURL,
                a.source = $source

            // 建立藝術家節點（如果存在）
            ${artwork.artist ? `
            MERGE (artist:Artist {name: $artist})
            MERGE (a)-[:CREATED_BY]->(artist)
            ` : ''}

            // 建立博物館節點
            MERGE (museum:Museum {name: $source})
            MERGE (a)-[:HOUSED_IN]->(museum)

            // 建立部門節點
            ${artwork.department ? `
            MERGE (dept:Department {name: $department})
            MERGE (a)-[:BELONGS_TO]->(dept)
            ` : ''}

            // 建立時期節點（如果存在）
            ${artwork.period ? `
            MERGE (period:Period {name: $period})
            MERGE (a)-[:FROM_PERIOD]->(period)
            ` : ''}

            RETURN a
        `;

        await this.session.run(query, {
            id: artwork.id,
            title: artwork.title || 'Unknown Title',
            artist: artwork.artist || null,
            date: artwork.date || 'Unknown Date',
            medium: artwork.medium || 'Unknown Medium',
            department: artwork.department || null,
            culture: artwork.culture || null,
            period: artwork.period || null,
            dimensions: artwork.dimensions || null,
            classification: artwork.classification || null,
            primaryImage: artwork.primaryImage || null,
            objectURL: artwork.objectURL || null,
            source: artwork.source || 'Metropolitan Museum of Art'
        });
    }

    async createIndexes() {
        const indexes = [
            'CREATE INDEX IF NOT EXISTS FOR (a:Artwork) ON (a.id)',
            'CREATE INDEX IF NOT EXISTS FOR (a:Artist) ON (a.name)',
            'CREATE INDEX IF NOT EXISTS FOR (m:Museum) ON (m.name)',
            'CREATE INDEX IF NOT EXISTS FOR (d:Department) ON (d.name)',
            'CREATE INDEX IF NOT EXISTS FOR (p:Period) ON (p.name)'
        ];

        for (const indexQuery of indexes) {
            await this.session.run(indexQuery);
        }

        console.log('📊 建立索引完成');
    }

    async showStatistics() {
        const queries = {
            artworks: 'MATCH (a:Artwork) RETURN count(a) as count',
            artists: 'MATCH (a:Artist) RETURN count(a) as count',
            museums: 'MATCH (m:Museum) RETURN count(m) as count',
            departments: 'MATCH (d:Department) RETURN count(d) as count',
            periods: 'MATCH (p:Period) RETURN count(p) as count'
        };

        console.log('\n📈 Neo4j 資料統計:');

        for (const [type, query] of Object.entries(queries)) {
            const result = await this.session.run(query);
            const count = result.records[0].get('count').toNumber();
            console.log(`   ${type}: ${count}`);
        }
    }

    async close() {
        if (this.session) {
            await this.session.close();
        }
        await this.driver.close();
        console.log('🔒 Neo4j 連接已關閉');
    }
}

// 執行匯入
async function main() {
    const importer = new MetDataImporter();

    try {
        const connected = await importer.connect();
        if (connected) {
            // 檢查是否有命令行參數指定文件名
            const filename = process.argv[2] || 'met_museum_crawled_2025-09-26T07-23-53-045Z.json';
            console.log(`📂 使用資料文件: ${filename}`);

            await importer.importMetData(filename);
        }
    } catch (error) {
        console.error('❌ 執行失敗:', error.message);
    } finally {
        await importer.close();
    }
}

// 如果直接執行此腳本
if (require.main === module) {
    main();
}

module.exports = MetDataImporter;