#!/usr/bin/env node
/**
 * Harvard Art Museums 簡化爬蟲
 * 直接使用curl方式收集資料
 */

const axios = require('axios');
const fs = require('fs').promises;
const path = require('path');

async function crawlHarvard() {
    require('dotenv').config();

    const apiKey = process.env.HARVARD_API_KEY;
    const baseUrl = 'https://api.harvardartmuseums.org';
    const outputDir = path.join(__dirname, 'data', 'raw');

    console.log('🚀 開始 Harvard Art Museums 簡化爬取...');
    console.log(`🔑 API Key: ${apiKey.substring(0, 8)}...`);

    const allArtworks = [];

    // 收集分類
    const classifications = ['Paintings', 'Sculptures', 'Drawings', 'Prints'];

    for (const classification of classifications) {
        console.log(`\n📊 收集: ${classification}`);

        try {
            const url = `${baseUrl}/object`;
            const response = await axios.get(url, {
                params: {
                    apikey: apiKey,
                    classification: classification,
                    size: 50,
                    hasimage: 1
                },
                timeout: 30000
            });

            if (response.status === 200 && response.data && response.data.records) {
                const records = response.data.records;
                console.log(`   ✅ 收集 ${records.length} 件作品`);

                // 處理每件作品
                for (const artwork of records) {
                    allArtworks.push({
                        harvardId: artwork.id,
                        title: artwork.title || 'Untitled',
                        classification: artwork.classification,
                        people: artwork.people || [],
                        culture: artwork.culture,
                        period: artwork.period,
                        century: artwork.century,
                        dated: artwork.dated,
                        medium: artwork.medium,
                        dimensions: artwork.dimensions,
                        description: artwork.description || artwork.creditline,
                        primaryImage: artwork.primaryimageurl,
                        department: artwork.department,
                        url: artwork.url,
                        source: 'Harvard Art Museums',
                        timestamp: new Date().toISOString()
                    });
                }

                // API限制：每秒最多1次請求
                await new Promise(resolve => setTimeout(resolve, 1000));

            } else {
                console.log(`   ⚠️ ${classification}: 無數據`);
            }

        } catch (error) {
            console.error(`   ❌ ${classification} 失敗:`, error.message);
            if (error.response) {
                console.error(`      狀態碼: ${error.response.status}`);
                console.error(`      響應:`, JSON.stringify(error.response.data).substring(0, 200));
            }
        }
    }

    // 保存結果
    console.log(`\n💾 保存結果...`);
    console.log(`   總計: ${allArtworks.length} 件作品`);

    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const filename = path.join(outputDir, `harvard_art_museums_${timestamp}.json`);

    const summary = {
        crawlInfo: {
            timestamp: new Date().toISOString(),
            totalItems: allArtworks.length,
            source: 'Harvard Art Museums API',
            classifications: classifications
        },
        data: allArtworks
    };

    await fs.writeFile(filename, JSON.stringify(summary, null, 2));

    console.log(`\n✅ 完成！`);
    console.log(`📁 保存至: ${filename}`);
    console.log(`📊 共收集 ${allArtworks.length} 件藝術品`);

    return allArtworks;
}

// 執行
crawlHarvard().catch(error => {
    console.error('❌ 爬取失敗:', error.message);
    process.exit(1);
});
