#!/usr/bin/env node
/**
 * 增強已爬取的藝術史資料
 * 加入標籤、中文翻譯、關鍵詞等，提升檢索準確度
 */

const fs = require('fs');
const path = require('path');

class DataEnhancer {
    constructor() {
        console.log('🎨 藝術史資料增強工具');
        console.log('═══════════════════════════════════════\n');

        // 載入中英文詞典
        const dictPath = path.join(__dirname, 'art_history_terms_dictionary.json');
        if (!fs.existsSync(dictPath)) {
            throw new Error('找不到 art_history_terms_dictionary.json 詞典文件');
        }

        this.termsDict = JSON.parse(fs.readFileSync(dictPath, 'utf8'));
        console.log('✅ 已載入中英文術語詞典');

        this.stats = {
            total: 0,
            enhanced: 0,
            with_period_tags: 0,
            with_artist_tags: 0,
            with_type_tags: 0
        };
    }

    enhanceArtwork(artwork) {
        const enhanced = { ...artwork };

        // 1. 提取並加入時期標籤
        enhanced.period_tags = this.extractPeriodTags(artwork);
        if (enhanced.period_tags.en.length > 0 || enhanced.period_tags.zh.length > 0) {
            this.stats.with_period_tags++;
        }

        // 2. 加入藝術家中文名稱
        enhanced.artist_chinese = this.getChineseArtistName(artwork.artist);
        if (enhanced.artist_chinese) {
            this.stats.with_artist_tags++;
        }

        // 3. 提取作品類型標籤
        enhanced.type_tags = this.extractTypeTags(artwork);
        if (enhanced.type_tags.en.length > 0 || enhanced.type_tags.zh.length > 0) {
            this.stats.with_type_tags++;
        }

        // 4. 提取材料標籤
        enhanced.material_tags = this.extractMaterialTags(artwork);

        // 5. 提取藝術概念標籤
        enhanced.concept_tags = this.extractConceptTags(artwork);

        // 6. 創建增強的搜尋文本（包含中英文）
        enhanced.search_text = this.createSearchText(enhanced);
        enhanced.search_text_chinese = this.createChineseSearchText(enhanced);

        // 7. 創建標籤列表（用於快速檢索）
        enhanced.all_tags = this.createTagList(enhanced);

        this.stats.enhanced++;

        return enhanced;
    }

    extractPeriodTags(artwork) {
        const text = `${artwork.title || ''} ${artwork.period || ''} ${artwork.date || ''}`.toLowerCase();
        const tags = { en: [], zh: [] };

        for (const [periodEn, translations] of Object.entries(this.termsDict.art_periods)) {
            if (text.includes(periodEn.toLowerCase()) ||
                (artwork.period && artwork.period.toLowerCase().includes(periodEn.toLowerCase()))) {
                if (!tags.en.includes(periodEn)) {
                    tags.en.push(periodEn);
                    tags.zh.push(...translations.zh);
                }
            }
        }

        // 根據日期推斷時期
        const dateBasedPeriod = this.inferPeriodFromDate(artwork);
        if (dateBasedPeriod && !tags.en.includes(dateBasedPeriod.en)) {
            tags.en.push(dateBasedPeriod.en);
            tags.zh.push(...dateBasedPeriod.zh);
        }

        return tags;
    }

    inferPeriodFromDate(artwork) {
        // 嘗試從日期字段推斷時期
        const beginDate = parseInt(artwork.beginDate || artwork.objectBeginDate || 0);

        if (beginDate >= 1400 && beginDate <= 1600) {
            return {
                en: 'Renaissance',
                zh: this.termsDict.art_periods['Renaissance'].zh
            };
        } else if (beginDate >= 1600 && beginDate <= 1750) {
            return {
                en: 'Baroque',
                zh: this.termsDict.art_periods['Baroque'].zh
            };
        }

        return null;
    }

    getChineseArtistName(artistName) {
        if (!artistName) return null;

        for (const [artistEn, translations] of Object.entries(this.termsDict.famous_artists)) {
            // 完整匹配
            if (artistName.includes(artistEn)) {
                return translations.zh;
            }

            // 部分匹配（如 "Leonardo" 匹配 "Leonardo da Vinci"）
            const parts = artistEn.split(' ');
            if (parts.some(part => artistName.includes(part) && part.length > 3)) {
                return translations.zh;
            }
        }

        return null;
    }

    extractTypeTags(artwork) {
        const text = `${artwork.title || ''} ${artwork.objectName || ''} ${artwork.classification || ''} ${artwork.medium || ''}`.toLowerCase();
        const tags = { en: [], zh: [] };

        for (const [typeEn, translations] of Object.entries(this.termsDict.art_types)) {
            if (text.includes(typeEn.toLowerCase())) {
                if (!tags.en.includes(typeEn)) {
                    tags.en.push(typeEn);
                    tags.zh.push(...translations.zh);
                }
            }
        }

        return tags;
    }

    extractMaterialTags(artwork) {
        const text = `${artwork.medium || ''} ${artwork.materials || ''}`.toLowerCase();
        const tags = { en: [], zh: [] };

        for (const [materialEn, translations] of Object.entries(this.termsDict.materials || {})) {
            if (text.includes(materialEn.toLowerCase())) {
                if (!tags.en.includes(materialEn)) {
                    tags.en.push(materialEn);
                    tags.zh.push(...translations.zh);
                }
            }
        }

        return tags;
    }

    extractConceptTags(artwork) {
        const text = `${artwork.title || ''} ${artwork.description || ''} ${artwork.tags || ''}`.toLowerCase();
        const tags = { en: [], zh: [] };

        for (const [conceptEn, translations] of Object.entries(this.termsDict.art_concepts || {})) {
            if (text.includes(conceptEn.toLowerCase())) {
                if (!tags.en.includes(conceptEn)) {
                    tags.en.push(conceptEn);
                    tags.zh.push(...translations.zh);
                }
            }
        }

        return tags;
    }

    createSearchText(artwork) {
        const parts = [];

        // 基本資訊（英文）
        if (artwork.title) parts.push(artwork.title);
        if (artwork.artist) parts.push(artwork.artist);
        if (artwork.period) parts.push(artwork.period);
        if (artwork.date) parts.push(artwork.date);

        // 標籤（英文）
        if (artwork.period_tags?.en) parts.push(...artwork.period_tags.en);
        if (artwork.type_tags?.en) parts.push(...artwork.type_tags.en);
        if (artwork.material_tags?.en) parts.push(...artwork.material_tags.en);
        if (artwork.concept_tags?.en) parts.push(...artwork.concept_tags.en);

        return parts.join(' | ');
    }

    createChineseSearchText(artwork) {
        const parts = [];

        // 中文標籤
        if (artwork.artist_chinese) {
            parts.push(...artwork.artist_chinese);
        }
        if (artwork.period_tags?.zh) {
            parts.push(...artwork.period_tags.zh);
        }
        if (artwork.type_tags?.zh) {
            parts.push(...artwork.type_tags.zh);
        }
        if (artwork.material_tags?.zh) {
            parts.push(...artwork.material_tags.zh);
        }
        if (artwork.concept_tags?.zh) {
            parts.push(...artwork.concept_tags.zh);
        }

        return parts.join(' | ');
    }

    createTagList(artwork) {
        const tags = new Set();

        // 英文標籤
        [artwork.period_tags?.en,
         artwork.type_tags?.en,
         artwork.material_tags?.en,
         artwork.concept_tags?.en].forEach(tagArray => {
            if (tagArray) tagArray.forEach(tag => tags.add(tag));
        });

        // 中文標籤
        [artwork.period_tags?.zh,
         artwork.type_tags?.zh,
         artwork.material_tags?.zh,
         artwork.concept_tags?.zh].forEach(tagArray => {
            if (tagArray) tagArray.forEach(tag => tags.add(tag));
        });

        // 藝術家中文名
        if (artwork.artist_chinese) {
            artwork.artist_chinese.forEach(name => tags.add(name));
        }

        return Array.from(tags);
    }

    async processDataFile(inputFile, outputFile) {
        console.log(`\n📂 處理文件: ${path.basename(inputFile)}`);

        try {
            const data = JSON.parse(fs.readFileSync(inputFile, 'utf8'));

            let artworks = [];
            if (Array.isArray(data)) {
                artworks = data;
            } else if (data.items) {
                artworks = data.items;
            } else if (data.artworks) {
                artworks = data.artworks;
            } else {
                console.log('   ⚠️ 無法識別資料格式，跳過');
                return;
            }

            console.log(`   📊 找到 ${artworks.length} 件作品`);
            this.stats.total += artworks.length;

            const enhanced = artworks.map(artwork => this.enhanceArtwork(artwork));

            fs.writeFileSync(outputFile, JSON.stringify(enhanced, null, 2));

            console.log(`   ✅ 已增強 ${enhanced.length} 件作品`);
            console.log(`   💾 輸出: ${path.basename(outputFile)}`);

            // 顯示範例
            if (enhanced.length > 0) {
                const sample = enhanced[0];
                console.log(`\n   📌 增強範例:`);
                console.log(`      標題: ${sample.title || 'N/A'}`);
                console.log(`      藝術家: ${sample.artist || 'N/A'}`);
                if (sample.artist_chinese) {
                    console.log(`      藝術家(中文): ${sample.artist_chinese.join(', ')}`);
                }
                if (sample.period_tags?.en?.length > 0) {
                    console.log(`      時期標籤: ${sample.period_tags.en.join(', ')} | ${sample.period_tags.zh.join(', ')}`);
                }
                if (sample.all_tags?.length > 0) {
                    console.log(`      所有標籤: ${sample.all_tags.slice(0, 10).join(', ')}${sample.all_tags.length > 10 ? '...' : ''}`);
                }
            }

            return enhanced;

        } catch (error) {
            console.error(`   ❌ 處理失敗: ${error.message}`);
        }
    }

    printStats() {
        console.log('\n\n═══════════════════════════════════════');
        console.log('📊 資料增強統計');
        console.log('═══════════════════════════════════════');
        console.log(`總作品數: ${this.stats.total}`);
        console.log(`成功增強: ${this.stats.enhanced}`);
        console.log(`包含時期標籤: ${this.stats.with_period_tags} (${(this.stats.with_period_tags/this.stats.enhanced*100).toFixed(1)}%)`);
        console.log(`包含藝術家中文: ${this.stats.with_artist_tags} (${(this.stats.with_artist_tags/this.stats.enhanced*100).toFixed(1)}%)`);
        console.log(`包含類型標籤: ${this.stats.with_type_tags} (${(this.stats.with_type_tags/this.stats.enhanced*100).toFixed(1)}%)`);
        console.log('═══════════════════════════════════════\n');
    }
}

async function main() {
    try {
        const enhancer = new DataEnhancer();

        // 處理所有原始資料文件
        const dataDir = path.join(__dirname, 'data', 'raw');
        const enhancedDir = path.join(__dirname, 'data', 'enhanced');

        // 創建輸出目錄
        if (!fs.existsSync(enhancedDir)) {
            fs.mkdirSync(enhancedDir, { recursive: true });
            console.log(`✅ 已創建輸出目錄: ${enhancedDir}`);
        }

        // 獲取所有JSON文件
        const files = fs.readdirSync(dataDir).filter(f => f.endsWith('.json'));
        console.log(`\n📁 找到 ${files.length} 個資料文件\n`);

        // 處理每個文件
        for (const file of files) {
            const inputPath = path.join(dataDir, file);
            const outputPath = path.join(enhancedDir, `enhanced_${file}`);

            await enhancer.processDataFile(inputPath, outputPath);
        }

        // 顯示統計
        enhancer.printStats();

        console.log('✨ 資料增強完成！');
        console.log('\n下一步：');
        console.log('  1. 檢查增強後的資料: ls -lh data/enhanced/');
        console.log('  2. 向量化並整合到資料庫: python integrate-to-vector-db.py --hours 720');
        console.log('  3. 測試中文查詢效果: node test-chinese-query.js');

    } catch (error) {
        console.error('\n❌ 執行失敗:', error.message);
        console.error(error.stack);
        process.exit(1);
    }
}

if (require.main === module) {
    main().catch(console.error);
}

module.exports = DataEnhancer;
