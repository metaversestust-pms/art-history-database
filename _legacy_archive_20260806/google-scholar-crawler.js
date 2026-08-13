#!/usr/bin/env node
/**
 * Google Scholar 學術文獻爬蟲
 * 收集藝術史相關的學術論文和研究文獻
 */

const axios = require('axios');
const puppeteer = require('puppeteer');
const fs = require('fs/promises');
const path = require('path');

class GoogleScholarCrawler {
    constructor() {
        this.baseUrl = 'https://scholar.google.com/scholar';
        this.outputDir = path.join(__dirname, 'data', 'raw');
        this.collectedData = [];
        this.browser = null;
        this.page = null;

        // 藝術史學術搜索關鍵字
        this.academicQueries = [
            // 英文關鍵字
            'art history methodology',
            'Renaissance art criticism',
            'Baroque painting analysis',
            'Medieval iconography',
            'Gothic architecture theory',
            'Impressionism art movement',
            'Modern art criticism',
            'Contemporary art theory',
            'Art historical interpretation',
            'Visual culture studies',
            'Iconology Panofsky',
            'Art attribution methods',
            'Provenance research',
            'Museum studies',
            'Cultural heritage preservation',

            // 中文關鍵字
            '藝術史研究方法',
            '文藝復興繪畫研究',
            '巴洛克藝術分析',
            '中世紀圖像學',
            '哥德式建築理論',
            '印象派藝術運動',
            '現代藝術批評',
            '當代藝術理論',
            '藝術史詮釋',
            '視覺文化研究'
        ];

        // 重要學者和理論家
        this.importantScholars = [
            'Ernst Gombrich',
            'Erwin Panofsky',
            'Heinrich Wölfflin',
            'Aby Warburg',
            'Walter Benjamin',
            'Arthur Danto',
            'Rosalind Krauss',
            'Linda Nochlin',
            'T.J. Clark',
            'Hal Foster',
            'October journal',
            'Art Bulletin',
            'Journal of Art History'
        ];

        // 特定研究領域
        this.researchAreas = [
            'feminist art history',
            'postcolonial art studies',
            'digital art history',
            'global art history',
            'queer art theory',
            'art and technology',
            'art market studies',
            'museum anthropology',
            'curatorial studies',
            'art education research'
        ];
    }

    async initBrowser() {
        if (!this.browser) {
            this.browser = await puppeteer.launch({
                headless: 'new',
                args: [
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--no-first-run',
                    '--no-zygote',
                    '--single-process',
                    '--disable-gpu'
                ]
            });
        }

        if (!this.page) {
            this.page = await this.browser.newPage();
            await this.page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36');

            // 設置較長的超時時間
            await this.page.setDefaultTimeout(30000);
        }
    }

    async ensureOutputDir() {
        try {
            await fs.access(this.outputDir);
        } catch (error) {
            await fs.mkdir(this.outputDir, { recursive: true });
        }
    }

    async searchGoogleScholar(query, maxResults = 20) {
        try {
            console.log(`🔍 Google Scholar 搜尋: "${query}"`);

            await this.initBrowser();

            const searchUrl = `${this.baseUrl}?q=${encodeURIComponent(query)}&hl=zh-TW&as_sdt=0,5&as_vis=1`;

            await this.page.goto(searchUrl, {
                waitUntil: 'networkidle2',
                timeout: 30000
            });

            // 等待搜索結果載入
            await this.page.waitForSelector('.gs_r', { timeout: 10000 }).catch(() => {
                console.log(`   ❌ "${query}" 沒有找到結果`);
                return null;
            });

            // 提取搜索結果
            const results = await this.page.evaluate((maxResults) => {
                const resultElements = document.querySelectorAll('.gs_r');
                const results = [];

                for (let i = 0; i < Math.min(resultElements.length, maxResults); i++) {
                    const element = resultElements[i];

                    try {
                        const titleElement = element.querySelector('.gs_rt a, .gs_rt h3');
                        const title = titleElement ? titleElement.textContent.trim() : null;
                        const link = titleElement && titleElement.href ? titleElement.href : null;

                        const authorsElement = element.querySelector('.gs_a');
                        const authorsText = authorsElement ? authorsElement.textContent : '';

                        const snippetElement = element.querySelector('.gs_rs');
                        const snippet = snippetElement ? snippetElement.textContent.trim() : null;

                        const citationElement = element.querySelector('.gs_fl a[href*="cites="]');
                        const citationsText = citationElement ? citationElement.textContent : '被引用 0 次';
                        const citationCount = citationsText.match(/\\d+/) ? parseInt(citationsText.match(/\\d+/)[0]) : 0;

                        const yearMatch = authorsText.match(/\\b(19|20)\\d{2}\\b/);
                        const year = yearMatch ? yearMatch[0] : null;

                        const pdfElement = element.querySelector('.gs_or_ggsm a[href*=".pdf"]');
                        const pdfUrl = pdfElement ? pdfElement.href : null;

                        if (title) {
                            results.push({
                                title,
                                authors: authorsText,
                                year,
                                snippet,
                                link,
                                pdfUrl,
                                citationCount
                            });
                        }
                    } catch (error) {
                        console.warn('解析搜索結果時出錯:', error.message);
                    }
                }

                return results;
            }, maxResults);

            console.log(`   📊 找到 ${results.length} 篇相關論文`);

            // 處理結果
            const processedResults = [];
            for (const result of results) {
                const processedResult = this.processScholarResult(result, query);
                if (processedResult) {
                    processedResults.push(processedResult);
                }
            }

            // 隨機延遲以避免被封鎖
            await new Promise(resolve => setTimeout(resolve, 2000 + Math.random() * 3000));

            return processedResults;

        } catch (error) {
            console.error(`   ⚠️ 搜尋 "${query}" 失敗:`, error.message);
            return [];
        }
    }

    processScholarResult(result, searchQuery) {
        try {
            const processedResult = {
                // 基本信息
                title: result.title,
                authors: this.parseAuthors(result.authors),
                year: result.year,
                abstract: result.snippet,

                // 連結和資源
                scholarUrl: result.link,
                pdfUrl: result.pdfUrl,

                // 學術指標
                citationCount: result.citationCount,
                academicScore: this.calculateAcademicScore(result),

                // 分類
                researchFields: this.categorizeResearch(result),
                artHistoryRelevance: this.assessArtHistoryRelevance(result),

                // 元數據
                source: 'Google Scholar',
                searchQuery: searchQuery,
                timestamp: new Date().toISOString(),
                language: this.detectLanguage(result.title + ' ' + (result.snippet || '')),

                // 品質評估
                qualityIndicators: this.assessQualityIndicators(result)
            };

            return processedResult;

        } catch (error) {
            console.warn(`   ⚠️ 處理論文結果失敗: ${error.message}`);
            return null;
        }
    }

    parseAuthors(authorsText) {
        if (!authorsText) return [];

        // 移除年份和期刊信息，只保留作者
        let authors = authorsText.split('-')[0].trim();
        authors = authors.replace(/\\d{4}/g, '').trim();
        authors = authors.replace(/,\\s*…$/, ''); // 移除末尾的 "..."

        return authors.split(',').map(author => author.trim()).filter(author => author.length > 0);
    }

    calculateAcademicScore(result) {
        let score = 0;

        // 引用次數權重 (40%)
        if (result.citationCount > 100) score += 40;
        else if (result.citationCount > 50) score += 30;
        else if (result.citationCount > 10) score += 20;
        else if (result.citationCount > 1) score += 10;

        // 有PDF可下載 (20%)
        if (result.pdfUrl) score += 20;

        // 標題品質 (20%)
        const titleWords = result.title.split(' ').length;
        if (titleWords >= 5 && titleWords <= 15) score += 20;
        else if (titleWords >= 3) score += 10;

        // 摘要品質 (20%)
        if (result.snippet && result.snippet.length > 100) score += 20;
        else if (result.snippet && result.snippet.length > 50) score += 10;

        return Math.min(score, 100);
    }

    categorizeResearch(result) {
        const categories = [];
        const content = `${result.title} ${result.snippet || ''}`.toLowerCase();

        const researchCategories = {
            'methodology': ['methodology', 'method', 'approach', '方法', '研究方法'],
            'theory': ['theory', 'theoretical', 'criticism', '理論', '批評'],
            'historical': ['historical', 'history', 'period', '歷史', '時期'],
            'iconography': ['iconography', 'iconology', 'symbol', '圖像學', '象徵'],
            'cultural': ['cultural', 'culture', 'society', '文化', '社會'],
            'feminist': ['feminist', 'gender', 'women', '女性主義', '性別'],
            'postcolonial': ['postcolonial', 'colonial', 'empire', '後殖民', '殖民'],
            'digital': ['digital', 'computational', 'database', '數位', '計算'],
            'museum': ['museum', 'exhibition', 'curatorial', '博物館', '展覽', '策展'],
            'conservation': ['conservation', 'restoration', 'preservation', '保存', '修復']
        };

        for (const [category, keywords] of Object.entries(researchCategories)) {
            if (keywords.some(keyword => content.includes(keyword))) {
                categories.push(category);
            }
        }

        return categories;
    }

    assessArtHistoryRelevance(result) {
        const content = `${result.title} ${result.snippet || ''}`.toLowerCase();

        const artHistoryKeywords = [
            'art', 'artist', 'painting', 'sculpture', 'architecture', 'museum',
            'gallery', 'exhibition', 'visual', 'aesthetic', 'style', 'movement',
            '藝術', '藝術家', '繪畫', '雕塑', '建築', '博物館', '美術館', '展覽', '視覺', '美學'
        ];

        const matches = artHistoryKeywords.filter(keyword => content.includes(keyword));
        return Math.min((matches.length / artHistoryKeywords.length) * 100, 100);
    }

    detectLanguage(text) {
        const chineseChars = text.match(/[\\u4e00-\\u9fff]/g);
        if (chineseChars && chineseChars.length > 10) {
            return 'zh';
        }
        return 'en';
    }

    assessQualityIndicators(result) {
        const indicators = {
            hasPDF: !!result.pdfUrl,
            highCitations: result.citationCount > 50,
            recentPublication: result.year && parseInt(result.year) > 2010,
            substantialAbstract: result.snippet && result.snippet.length > 150,
            multipleAuthors: result.authors && result.authors.length > 1
        };

        indicators.overallQuality = Object.values(indicators).filter(Boolean).length / 5;
        return indicators;
    }

    async crawlAllQueries() {
        await this.ensureOutputDir();

        console.log('🚀 開始 Google Scholar 學術文獻爬取...');

        const allQueries = [
            ...this.academicQueries,
            ...this.importantScholars,
            ...this.researchAreas
        ];

        for (let i = 0; i < allQueries.length; i++) {
            const query = allQueries[i];

            console.log(`\\n📊 進度: ${i + 1}/${allQueries.length}`);

            try {
                const results = await this.searchGoogleScholar(query, 15);
                this.collectedData.push(...results);
            } catch (error) {
                console.warn(`跳過查詢 "${query}": ${error.message}`);
            }

            // 較長的延遲以避免被封鎖
            if (i < allQueries.length - 1) {
                await new Promise(resolve => setTimeout(resolve, 5000 + Math.random() * 5000));
            }
        }

        // 去重和排序
        const uniqueData = this.removeDuplicates(this.collectedData);
        uniqueData.sort((a, b) => b.academicScore - a.academicScore);

        // 保存結果
        await this.saveResults(uniqueData);

        return uniqueData;
    }

    removeDuplicates(data) {
        const seen = new Map();
        const unique = [];

        for (const item of data) {
            const key = item.title.toLowerCase().replace(/[^a-zA-Z0-9\\u4e00-\\u9fff]/g, '');

            if (!seen.has(key)) {
                seen.set(key, true);
                unique.push(item);
            } else {
                // 保留學術分數更高的
                const existingIndex = unique.findIndex(u =>
                    u.title.toLowerCase().replace(/[^a-zA-Z0-9\\u4e00-\\u9fff]/g, '') === key
                );
                if (existingIndex !== -1 && item.academicScore > unique[existingIndex].academicScore) {
                    unique[existingIndex] = item;
                }
            }
        }

        return unique;
    }

    async saveResults(data) {
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        const filename = path.join(this.outputDir, `google_scholar_${timestamp}.json`);

        const summary = {
            crawlInfo: {
                timestamp: new Date().toISOString(),
                totalPapers: data.length,
                source: 'Google Scholar',
                averageAcademicScore: data.reduce((sum, item) => sum + item.academicScore, 0) / data.length,
                averageArtHistoryRelevance: data.reduce((sum, item) => sum + item.artHistoryRelevance, 0) / data.length,
                languageDistribution: this.getLanguageDistribution(data),
                fieldDistribution: this.getFieldDistribution(data),
                qualityMetrics: this.getQualityMetrics(data)
            },
            data: data
        };

        await fs.writeFile(filename, JSON.stringify(summary, null, 2));

        console.log(`\\n✅ Google Scholar 爬取完成！`);
        console.log(`📁 資料保存至: ${filename}`);
        console.log(`📊 共收集 ${data.length} 篇學術論文`);
        console.log(`⭐ 平均學術分數: ${summary.crawlInfo.averageAcademicScore.toFixed(2)}/100`);
        console.log(`🎯 平均藝術史相關度: ${summary.crawlInfo.averageArtHistoryRelevance.toFixed(2)}%`);

        return filename;
    }

    getLanguageDistribution(data) {
        const distribution = {};
        for (const item of data) {
            distribution[item.language] = (distribution[item.language] || 0) + 1;
        }
        return distribution;
    }

    getFieldDistribution(data) {
        const distribution = {};
        for (const item of data) {
            for (const field of item.researchFields) {
                distribution[field] = (distribution[field] || 0) + 1;
            }
        }
        return distribution;
    }

    getQualityMetrics(data) {
        return {
            withPDF: data.filter(item => item.qualityIndicators.hasPDF).length,
            highCitations: data.filter(item => item.qualityIndicators.highCitations).length,
            recentPublications: data.filter(item => item.qualityIndicators.recentPublication).length,
            highQuality: data.filter(item => item.qualityIndicators.overallQuality > 0.6).length
        };
    }

    async cleanup() {
        if (this.page) {
            await this.page.close();
        }
        if (this.browser) {
            await this.browser.close();
        }
    }
}

// 導出模組
module.exports = GoogleScholarCrawler;

// 直接執行
if (require.main === module) {
    async function main() {
        const crawler = new GoogleScholarCrawler();
        try {
            await crawler.crawlAllQueries();
        } catch (error) {
            console.error('❌ Google Scholar 爬取失敗:', error.message);
        } finally {
            await crawler.cleanup();
            process.exit(0);
        }
    }

    main();
}