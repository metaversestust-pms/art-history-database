#!/usr/bin/env node
/**
 * 核心藝術品爬蟲
 * 使用Wikidata SPARQL查詢收集著名的文藝復興和巴洛克藝術作品
 */

const axios = require('axios');
const fs = require('fs');
const path = require('path');

class MasterpieceCrawler {
    constructor() {
        console.log('🎨 核心藝術品收集器');
        console.log('═══════════════════════════════════════\n');

        this.wikidataEndpoint = 'https://query.wikidata.org/sparql';

        // 核心藝術家及其代表作
        this.masterpieces = {
            'Leonardo da Vinci': [
                'Mona Lisa',
                'The Last Supper',
                'Vitruvian Man',
                'Lady with an Ermine',
                'The Annunciation'
            ],
            'Michelangelo': [
                'David',
                'Pietà',
                'The Creation of Adam',
                'The Last Judgment',
                'Moses'
            ],
            'Raphael': [
                'The School of Athens',
                'Sistine Madonna',
                'The Transfiguration',
                'La belle jardinière',
                'Portrait of Baldassare Castiglione'
            ],
            'Sandro Botticelli': [
                'The Birth of Venus',
                'Primavera',
                'The Adoration of the Magi'
            ],
            'Titian': [
                'Assumption of the Virgin',
                'Venus of Urbino',
                'Bacchus and Ariadne'
            ],
            'Caravaggio': [
                'The Calling of St Matthew',
                'Judith Beheading Holofernes',
                'The Entombment of Christ',
                'Supper at Emmaus'
            ],
            'Rembrandt': [
                'The Night Watch',
                'The Anatomy Lesson of Dr. Nicolaes Tulp',
                'Self-Portrait with Two Circles',
                'The Return of the Prodigal Son'
            ],
            'Johannes Vermeer': [
                'Girl with a Pearl Earring',
                'The Milkmaid',
                'View of Delft',
                'The Art of Painting'
            ],
            'Peter Paul Rubens': [
                'The Descent from the Cross',
                'The Garden of Eden with the Fall of Man',
                'Samson and Delilah'
            ],
            'Diego Velázquez': [
                'Las Meninas',
                'The Surrender of Breda',
                'Portrait of Pope Innocent X'
            ]
        };

        this.results = [];
        this.stats = {
            artists: 0,
            artworks_searched: 0,
            artworks_found: 0,
            errors: 0
        };
    }

    async queryWikidata(sparql) {
        try {
            const response = await axios.get(this.wikidataEndpoint, {
                params: {
                    query: sparql,
                    format: 'json'
                },
                headers: {
                    'User-Agent': 'ArtHistoryDatabase/1.0'
                },
                timeout: 30000
            });

            return response.data.results.bindings;
        } catch (error) {
            console.error(`   ❌ Wikidata 查詢失敗: ${error.message}`);
            this.stats.errors++;
            return [];
        }
    }

    async searchArtworkByTitle(artistName, artworkTitle) {
        console.log(`\n🔍 搜尋: ${artistName} - ${artworkTitle}`);

        const sparql = `
            SELECT DISTINCT ?artwork ?artworkLabel ?artworkDescription
                   ?image ?inception ?locationLabel ?materialLabel
                   ?heightValue ?widthValue ?collectionLabel
            WHERE {
                ?artwork wdt:P31 wd:Q3305213 .  # instance of painting
                ?artwork wdt:P170 ?creator .     # creator
                ?creator rdfs:label ?creatorLabel .
                FILTER(CONTAINS(LCASE(?creatorLabel), LCASE("${artistName}")))

                ?artwork rdfs:label ?artworkLabel .
                FILTER(CONTAINS(LCASE(?artworkLabel), LCASE("${artworkTitle}")))
                FILTER(LANG(?artworkLabel) = "en")

                OPTIONAL { ?artwork wdt:P18 ?image . }
                OPTIONAL { ?artwork wdt:P571 ?inception . }
                OPTIONAL { ?artwork wdt:P276 ?location . }
                OPTIONAL { ?artwork wdt:P186 ?material . }
                OPTIONAL { ?artwork wdt:P2048 ?heightValue . }
                OPTIONAL { ?artwork wdt:P2049 ?widthValue . }
                OPTIONAL { ?artwork wdt:P195 ?collection . }
                OPTIONAL { ?artwork schema:description ?artworkDescription . FILTER(LANG(?artworkDescription) = "en") }

                SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
            }
            LIMIT 5
        `;

        const results = await this.queryWikidata(sparql);
        this.stats.artworks_searched++;

        if (results.length > 0) {
            console.log(`   ✅ 找到 ${results.length} 項結果`);
            this.stats.artworks_found += results.length;

            for (const result of results) {
                const artwork = {
                    id: `wikidata_${result.artwork.value.split('/').pop()}`,
                    source: 'wikidata',
                    title: result.artworkLabel?.value || artworkTitle,
                    artist: artistName,
                    description: result.artworkDescription?.value || '',
                    date: result.inception?.value ? new Date(result.inception.value).getFullYear().toString() : '',
                    medium: result.materialLabel?.value || 'Painting',
                    classification: 'Painting',
                    period: this.inferPeriod(artistName),
                    culture: this.inferCulture(artistName),
                    location: result.locationLabel?.value || '',
                    collection: result.collectionLabel?.value || '',
                    primaryImage: result.image?.value || '',
                    dimensions: this.formatDimensions(result.heightValue?.value, result.widthValue?.value),
                    wikidata_uri: result.artwork.value,
                    is_masterpiece: true,  // 標記為傑作
                    famous_artwork: true
                };

                this.results.push(artwork);

                console.log(`      📌 ${artwork.title}`);
                if (artwork.collection) {
                    console.log(`         收藏: ${artwork.collection}`);
                }
                if (artwork.date) {
                    console.log(`         年代: ${artwork.date}`);
                }
            }
        } else {
            console.log(`   ⚠️  未找到資料`);
        }

        // 避免過快請求
        await this.delay(1000);
    }

    inferPeriod(artistName) {
        const renaissanceArtists = ['Leonardo da Vinci', 'Michelangelo', 'Raphael', 'Sandro Botticelli', 'Titian'];
        const baroqueArtists = ['Caravaggio', 'Rembrandt', 'Johannes Vermeer', 'Peter Paul Rubens', 'Diego Velázquez'];

        if (renaissanceArtists.includes(artistName)) {
            return 'Renaissance';
        } else if (baroqueArtists.includes(artistName)) {
            return 'Baroque';
        }
        return '';
    }

    inferCulture(artistName) {
        const cultures = {
            'Leonardo da Vinci': 'Italian',
            'Michelangelo': 'Italian',
            'Raphael': 'Italian',
            'Sandro Botticelli': 'Italian',
            'Titian': 'Italian',
            'Caravaggio': 'Italian',
            'Rembrandt': 'Dutch',
            'Johannes Vermeer': 'Dutch',
            'Peter Paul Rubens': 'Flemish',
            'Diego Velázquez': 'Spanish'
        };
        return cultures[artistName] || '';
    }

    formatDimensions(height, width) {
        if (height && width) {
            return `${height} × ${width} cm`;
        }
        return '';
    }

    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    async crawlAllMasterpieces() {
        console.log('🚀 開始收集核心藝術品...\n');

        for (const [artist, artworks] of Object.entries(this.masterpieces)) {
            console.log(`\n👨‍🎨 藝術家: ${artist}`);
            console.log(`   預計收集 ${artworks.length} 件代表作`);

            this.stats.artists++;

            for (const artwork of artworks) {
                await this.searchArtworkByTitle(artist, artwork);
            }

            // 藝術家之間間隔稍長
            await this.delay(2000);
        }
    }

    saveResults() {
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        const outputDir = path.join(__dirname, 'data', 'raw');
        const outputFile = path.join(outputDir, `masterpieces_${timestamp}.json`);

        if (!fs.existsSync(outputDir)) {
            fs.mkdirSync(outputDir, { recursive: true });
        }

        fs.writeFileSync(outputFile, JSON.stringify(this.results, null, 2));

        console.log(`\n💾 資料已保存到: ${outputFile}`);
        console.log(`📊 共收集 ${this.results.length} 件核心藝術品`);

        return outputFile;
    }

    printSummary() {
        console.log('\n\n═══════════════════════════════════════');
        console.log('📊 核心藝術品收集統計');
        console.log('═══════════════════════════════════════');
        console.log(`處理藝術家: ${this.stats.artists}`);
        console.log(`搜尋作品數: ${this.stats.artworks_searched}`);
        console.log(`成功找到: ${this.stats.artworks_found}`);
        console.log(`成功率: ${(this.stats.artworks_found / this.stats.artworks_searched * 100).toFixed(1)}%`);
        console.log(`錯誤: ${this.stats.errors}`);
        console.log('═══════════════════════════════════════\n');

        // 按藝術家統計
        const byArtist = {};
        this.results.forEach(artwork => {
            if (!byArtist[artwork.artist]) {
                byArtist[artwork.artist] = 0;
            }
            byArtist[artwork.artist]++;
        });

        console.log('📈 各藝術家收集統計:');
        Object.entries(byArtist)
            .sort((a, b) => b[1] - a[1])
            .forEach(([artist, count]) => {
                console.log(`   ${artist}: ${count} 件`);
            });

        console.log('\n');
    }

    async run() {
        try {
            await this.crawlAllMasterpieces();
            const outputFile = this.saveResults();
            this.printSummary();

            console.log('✨ 核心藝術品收集完成！\n');
            console.log('下一步：');
            console.log(`  1. 增強資料: node enhance-crawled-data.js`);
            console.log(`  2. 整合到Neo4j: node integrate-enhanced-to-neo4j.js`);
            console.log(`  3. 測試查詢: curl -X POST http://localhost:8008/query -d '{"query": "蒙娜麗莎"}'`);

        } catch (error) {
            console.error('\n❌ 執行失敗:', error);
            throw error;
        }
    }
}

async function main() {
    const crawler = new MasterpieceCrawler();
    await crawler.run();
}

if (require.main === module) {
    main().catch(console.error);
}

module.exports = MasterpieceCrawler;
