#!/usr/bin/env node
/**
 * 快速文藝復興與巴洛克資料收集器
 * 優化版本，避免超時問題
 */

const axios = require('axios');
const fs = require('fs/promises');
const path = require('path');

class QuickRenaissanceBaroqueCrawler {
    constructor() {
        this.baseUrl = 'https://collectionapi.metmuseum.org/public/collection/v1';
        this.outputDir = path.join(__dirname, 'data', 'raw');
        this.collectedData = [];
    }

    async ensureOutputDir() {
        try {
            await fs.access(this.outputDir);
        } catch (error) {
            await fs.mkdir(this.outputDir, { recursive: true });
        }
    }

    async searchAndCollect(query, limit = 15) {
        try {
            console.log(`🔍 搜尋: "${query}"`);
            const searchUrl = `${this.baseUrl}/search?hasImages=true&q=${encodeURIComponent(query)}`;
            const response = await axios.get(searchUrl, { timeout: 20000 });

            if (!response.data || !response.data.objectIDs) {
                console.log(`   ❌ "${query}" 沒有找到結果`);
                return 0;
            }

            const objectIDs = response.data.objectIDs.slice(0, limit);
            console.log(`   📊 找到 ${response.data.total} 件，將收集前 ${objectIDs.length} 件`);

            let successCount = 0;
            for (let i = 0; i < objectIDs.length; i++) {
                const objectID = objectIDs[i];

                // 避免重複
                if (this.collectedData.some(item => item.id === objectID)) {
                    continue;
                }

                try {
                    const artwork = await this.getArtworkDetails(objectID);
                    if (artwork) {
                        this.collectedData.push(artwork);
                        successCount++;
                    }
                } catch (error) {
                    console.log(`   ⚠️ 跳過作品 ${objectID}: ${error.message}`);
                }

                // 延遲避免請求過頻
                await new Promise(resolve => setTimeout(resolve, 500));
            }

            console.log(`   ✅ "${query}": 成功收集 ${successCount} 件作品`);
            return successCount;
        } catch (error) {
            console.error(`   ❌ 搜尋 "${query}" 失敗:`, error.message);
            return 0;
        }
    }

    async getArtworkDetails(objectID) {
        const detailUrl = `${this.baseUrl}/objects/${objectID}`;
        const response = await axios.get(detailUrl, {
            timeout: 8000,
            headers: {
                'User-Agent': 'Art History Database Crawler'
            }
        });

        if (!response.data || !response.data.objectID) {
            return null;
        }

        const artwork = response.data;
        const period = this.determinePeriod(artwork);

        return {
            id: artwork.objectID,
            title: artwork.title || 'Unknown Title',
            artist: artwork.artistDisplayName || 'Unknown Artist',
            artistNationality: artwork.artistNationality || null,
            artistBeginDate: artwork.artistBeginDate || null,
            artistEndDate: artwork.artistEndDate || null,
            date: artwork.objectDate || 'Unknown Date',
            beginDate: artwork.objectBeginDate || null,
            endDate: artwork.objectEndDate || null,
            medium: artwork.medium || 'Unknown Medium',
            department: artwork.department || null,
            culture: artwork.culture || null,
            period: period,
            dimensions: artwork.dimensions || null,
            classification: artwork.classification || null,
            primaryImage: artwork.primaryImage || null,
            objectURL: artwork.objectURL || null,
            isHighlight: artwork.isHighlight || false,
            accessionYear: artwork.accessionYear || null,
            creditLine: artwork.creditLine || null,
            tags: artwork.tags || [],
            source: 'Metropolitan Museum of Art',
            crawledAt: new Date().toISOString()
        };
    }

    determinePeriod(artwork) {
        const text = [
            artwork.title || '',
            artwork.artistDisplayName || '',
            artwork.objectDate || '',
            artwork.period || '',
            artwork.culture || ''
        ].join(' ').toLowerCase();

        const beginDate = artwork.objectBeginDate || 0;

        // 文藝復興關鍵字
        const renaissanceKeys = [
            'renaissance', 'leonardo', 'michelangelo', 'raphael',
            'botticelli', 'donatello', 'dürer', 'van eyck'
        ];

        // 巴洛克關鍵字
        const baroqueKeys = [
            'baroque', 'caravaggio', 'rubens', 'rembrandt',
            'vermeer', 'velázquez', 'bernini'
        ];

        if (renaissanceKeys.some(key => text.includes(key)) ||
            (beginDate >= 1400 && beginDate <= 1600)) {
            return 'Renaissance';
        }

        if (baroqueKeys.some(key => text.includes(key)) ||
            (beginDate >= 1600 && beginDate <= 1750)) {
            return 'Baroque';
        }

        return artwork.period || null;
    }

    async run() {
        console.log('🎨 快速文藝復興與巴洛克資料收集');
        console.log('⏰ 開始時間:', new Date().toLocaleString());

        await this.ensureOutputDir();

        // 精選搜尋查詢 - 限制數量避免超時
        const queries = [
            'Renaissance painting',
            'Leonardo da Vinci',
            'Michelangelo',
            'Raphael',
            'Italian Renaissance',
            'Baroque painting',
            'Caravaggio',
            'Rubens',
            'Rembrandt',
            'Velázquez'
        ];

        let totalCollected = 0;
        for (const query of queries) {
            const count = await this.searchAndCollect(query, 10); // 每個查詢限制10件
            totalCollected += count;

            console.log(`   📈 目前總計: ${this.collectedData.length} 件作品\n`);

            // 延遲避免請求過頻
            await new Promise(resolve => setTimeout(resolve, 2000));
        }

        if (this.collectedData.length > 0) {
            await this.saveData();
        } else {
            console.log('❌ 沒有收集到任何資料');
        }
    }

    async saveData() {
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        const filename = `renaissance_baroque_quick_${timestamp}.json`;
        const filePath = path.join(this.outputDir, filename);

        await fs.writeFile(filePath, JSON.stringify(this.collectedData, null, 2), 'utf8');

        const renaissanceCount = this.collectedData.filter(a => a.period === 'Renaissance').length;
        const baroqueCount = this.collectedData.filter(a => a.period === 'Baroque').length;
        const withImagesCount = this.collectedData.filter(a => a.primaryImage).length;

        console.log(`💾 資料已保存到: ${filename}`);
        console.log(`📊 收集統計:`);
        console.log(`   - 總作品數: ${this.collectedData.length}`);
        console.log(`   - 文藝復興時期: ${renaissanceCount} 件`);
        console.log(`   - 巴洛克時期: ${baroqueCount} 件`);
        console.log(`   - 其他時期: ${this.collectedData.length - renaissanceCount - baroqueCount} 件`);
        console.log(`   - 有圖片作品: ${withImagesCount} 件`);

        console.log(`\n💡 匯入命令:`);
        console.log(`   node import_met_data_to_neo4j.js "${filename}"`);

        return filePath;
    }
}

if (require.main === module) {
    const crawler = new QuickRenaissanceBaroqueCrawler();
    crawler.run();
}

module.exports = QuickRenaissanceBaroqueCrawler;