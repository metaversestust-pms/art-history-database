#!/usr/bin/env node
/**
 * 統一資料來源管理器
 * 整合所有爬蟲模組，提供統一的資料收集和管理介面
 */

const fs = require('fs/promises');
const path = require('path');

// 導入所有爬蟲模組
const EuropeanaCrawler = require('./europeana-crawler');
const GoogleScholarCrawler = require('./google-scholar-crawler');
const HarvardArtMuseumsCrawler = require('./harvard-art-museums-crawler');

class UnifiedDataSourceManager {
    constructor() {
        this.outputDir = path.join(__dirname, 'data', 'raw');
        this.summaryDir = path.join(__dirname, 'data', 'output');
        this.dataSources = new Map();

        // 註冊所有資料來源
        this.registerDataSources();
    }

    registerDataSources() {
        // 現有資料來源
        this.dataSources.set('met_museum', {
            name: 'Metropolitan Museum of Art',
            type: 'api',
            description: '大都會博物館藝術品收藏',
            crawler: null, // 使用現有的 renaissance-baroque-crawler
            priority: 9,
            dataQuality: 'high',
            updateFrequency: 'weekly',
            categories: ['artwork', 'museum', 'visual_art']
        });

        this.dataSources.set('google_books', {
            name: 'Google Books API',
            type: 'api',
            description: '藝術史相關書籍資料',
            crawler: null, // 使用現有的 fetch_google_books
            priority: 8,
            dataQuality: 'high',
            updateFrequency: 'monthly',
            categories: ['books', 'literature', 'academic']
        });

        // 新增資料來源
        this.dataSources.set('europeana', {
            name: 'Europeana Cultural Heritage',
            type: 'api',
            description: '歐洲數位文化遺產平台',
            crawler: new EuropeanaCrawler(),
            priority: 10,
            dataQuality: 'very_high',
            updateFrequency: 'weekly',
            categories: ['cultural_heritage', 'european_art', 'museum', 'digital_collection']
        });

        this.dataSources.set('google_scholar', {
            name: 'Google Scholar Academic Papers',
            type: 'web_scraping',
            description: '藝術史學術論文和研究文獻',
            crawler: new GoogleScholarCrawler(),
            priority: 9,
            dataQuality: 'very_high',
            updateFrequency: 'daily',
            categories: ['academic', 'research', 'papers', 'scholarly']
        });

        // 新增 Harvard Art Museums
        this.dataSources.set('harvard_art_museums', {
            name: 'Harvard Art Museums',
            type: 'api',
            description: '哈佛藝術博物館收藏，包含豐富的學術研究資料和展覽記錄',
            crawler: null, // 需要API Key才能初始化
            priority: 10,
            dataQuality: 'very_high',
            updateFrequency: 'daily',
            categories: ['museum', 'academic_collection', 'research', 'exhibition', 'provenance'],
            requiresAuth: true,
            dailyLimit: 2500,
            apiUrl: 'https://api.harvardartmuseums.org'
        });
    }

    async ensureOutputDirs() {
        await fs.mkdir(this.outputDir, { recursive: true });
        await fs.mkdir(this.summaryDir, { recursive: true });
    }

    async crawlAllSources(options = {}) {
        await this.ensureOutputDirs();

        console.log('🚀 啟動統一資料來源管理器...');
        console.log(`📊 已註冊 ${this.dataSources.size} 個資料來源`);

        const results = [];
        const errors = [];

        // 按優先級排序
        const sortedSources = Array.from(this.dataSources.entries())
            .sort((a, b) => b[1].priority - a[1].priority);

        for (const [sourceId, sourceConfig] of sortedSources) {
            if (options.sources && !options.sources.includes(sourceId)) {
                console.log(`⏭️  跳過資料來源: ${sourceConfig.name}`);
                continue;
            }

            console.log(`\n🔄 處理資料來源: ${sourceConfig.name}`);
            console.log(`   📋 類型: ${sourceConfig.type}`);
            console.log(`   ⭐ 優先級: ${sourceConfig.priority}/10`);
            console.log(`   📊 品質: ${sourceConfig.dataQuality}`);

            try {
                const startTime = Date.now();
                let crawlResult = null;

                if (sourceConfig.crawler) {
                    // 使用專門的爬蟲
                    if (sourceId === 'europeana') {
                        crawlResult = await sourceConfig.crawler.crawlAllSources();
                    } else if (sourceId === 'google_scholar') {
                        crawlResult = await sourceConfig.crawler.crawlAllQueries();
                    }
                } else if (sourceId === 'harvard_art_museums') {
                    // Harvard需要特殊處理 - 檢查API Key
                    const apiKey = options.harvardApiKey || process.env.HARVARD_API_KEY;
                    if (apiKey) {
                        console.log('   🔑 使用提供的Harvard API Key');
                        const harvardCrawler = new HarvardArtMuseumsCrawler(apiKey);
                        crawlResult = await harvardCrawler.crawlComprehensive(options.maxHarvardItems || 100);
                    } else {
                        console.log('   ⚠️  跳過Harvard Art Museums - 需要API Key');
                        console.log('      設定環境變數: HARVARD_API_KEY=your_key');
                        console.log('      或使用參數: --harvardApiKey your_key');
                        continue;
                    }
                } else {
                    // 現有資料來源，檢查已有資料
                    crawlResult = await this.checkExistingData(sourceId);
                }

                const endTime = Date.now();
                const duration = (endTime - startTime) / 1000;

                const result = {
                    sourceId,
                    sourceName: sourceConfig.name,
                    status: 'success',
                    duration: `${duration.toFixed(2)}s`,
                    dataCount: Array.isArray(crawlResult) ? crawlResult.length : (crawlResult?.length || 0),
                    timestamp: new Date().toISOString(),
                    ...sourceConfig
                };

                results.push(result);
                console.log(`   ✅ 完成: ${result.dataCount} 項資料，耗時 ${result.duration}`);

            } catch (error) {
                console.error(`   ❌ 失敗: ${error.message}`);

                errors.push({
                    sourceId,
                    sourceName: sourceConfig.name,
                    error: error.message,
                    timestamp: new Date().toISOString()
                });
            }

            // 資料來源間的延遲
            if (sortedSources.indexOf([sourceId, sourceConfig]) < sortedSources.length - 1) {
                await new Promise(resolve => setTimeout(resolve, 2000));
            }
        }

        // 生成綜合報告
        const summary = await this.generateSummaryReport(results, errors);

        console.log('\n📋 統一資料來源管理完成報告:');
        console.log(`✅ 成功: ${results.length}/${this.dataSources.size} 個資料來源`);
        console.log(`❌ 失敗: ${errors.length} 個資料來源`);
        console.log(`📊 總資料量: ${summary.totalDataCount} 項`);
        console.log(`📁 報告保存至: ${summary.reportFile}`);

        return summary;
    }

    async checkExistingData(sourceId) {
        const files = await fs.readdir(this.outputDir);
        const sourceFiles = files.filter(file => file.includes(sourceId) ||
            (sourceId === 'met_museum' && file.includes('met_museum')) ||
            (sourceId === 'google_books' && file.includes('google_books')) ||
            (sourceId === 'harvard_art_museums' && file.includes('harvard_art_museums')));

        if (sourceFiles.length === 0) {
            console.log(`   📝 ${sourceId} 暫無資料，請先執行對應的爬蟲`);
            return [];
        }

        // 讀取最新的資料檔案
        const latestFile = sourceFiles.sort().pop();
        const filePath = path.join(this.outputDir, latestFile);

        try {
            const content = await fs.readFile(filePath, 'utf8');
            const data = JSON.parse(content);

            console.log(`   📁 讀取現有資料: ${latestFile}`);
            return Array.isArray(data) ? data : (data.data || []);
        } catch (error) {
            console.warn(`   ⚠️  讀取 ${latestFile} 失敗: ${error.message}`);
            return [];
        }
    }

    async generateSummaryReport(results, errors) {
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        const reportFile = path.join(this.summaryDir, `unified_data_sources_report_${timestamp}.json`);

        const totalDataCount = results.reduce((sum, result) => sum + (result.dataCount || 0), 0);
        const avgDuration = results.reduce((sum, result) => sum + parseFloat(result.duration), 0) / results.length;

        const dataQualityDistribution = {};
        const categoryDistribution = {};
        const typeDistribution = {};

        for (const result of results) {
            // 品質分佈
            dataQualityDistribution[result.dataQuality] = (dataQualityDistribution[result.dataQuality] || 0) + 1;

            // 類別分佈
            for (const category of result.categories || []) {
                categoryDistribution[category] = (categoryDistribution[category] || 0) + result.dataCount;
            }

            // 類型分佈
            typeDistribution[result.type] = (typeDistribution[result.type] || 0) + result.dataCount;
        }

        const summary = {
            reportInfo: {
                timestamp: new Date().toISOString(),
                totalSources: this.dataSources.size,
                successfulSources: results.length,
                failedSources: errors.length,
                totalDataCount: totalDataCount,
                averageDuration: `${avgDuration.toFixed(2)}s`
            },

            dataSourcesOverview: Array.from(this.dataSources.entries()).map(([id, config]) => ({
                id,
                name: config.name,
                type: config.type,
                priority: config.priority,
                dataQuality: config.dataQuality,
                updateFrequency: config.updateFrequency,
                categories: config.categories,
                description: config.description
            })),

            crawlResults: results,
            errors: errors,

            analytics: {
                dataQualityDistribution,
                categoryDistribution,
                typeDistribution,
                qualityMetrics: this.calculateQualityMetrics(results),
                recommendations: this.generateRecommendations(results, errors)
            }
        };

        await fs.writeFile(reportFile, JSON.stringify(summary, null, 2));

        return {
            ...summary,
            reportFile,
            totalDataCount
        };
    }

    calculateQualityMetrics(results) {
        const metrics = {
            highQualitySources: results.filter(r => r.dataQuality === 'very_high' || r.dataQuality === 'high').length,
            apiBasedSources: results.filter(r => r.type === 'api').length,
            regularlyUpdatedSources: results.filter(r => r.updateFrequency === 'daily' || r.updateFrequency === 'weekly').length,
            diverseCategoryCoverage: new Set(results.flatMap(r => r.categories)).size
        };

        metrics.overallQualityScore = (
            (metrics.highQualitySources / results.length) * 0.3 +
            (metrics.apiBasedSources / results.length) * 0.2 +
            (metrics.regularlyUpdatedSources / results.length) * 0.2 +
            (metrics.diverseCategoryCoverage / 10) * 0.3
        ) * 100;

        return metrics;
    }

    generateRecommendations(results, errors) {
        const recommendations = [];

        // 基於錯誤的建議
        if (errors.length > 0) {
            recommendations.push({
                type: 'error_handling',
                priority: 'high',
                message: `有 ${errors.length} 個資料來源失敗，建議檢查網路連接和 API 配置`
            });
        }

        // 基於資料品質的建議
        const lowQualitySources = results.filter(r => r.dataQuality === 'medium' || r.dataQuality === 'low');
        if (lowQualitySources.length > 0) {
            recommendations.push({
                type: 'quality_improvement',
                priority: 'medium',
                message: `建議改善 ${lowQualitySources.map(s => s.sourceName).join(', ')} 的資料品質`
            });
        }

        // 基於更新頻率的建議
        const infrequentSources = results.filter(r => r.updateFrequency === 'monthly' || r.updateFrequency === 'yearly');
        if (infrequentSources.length > 2) {
            recommendations.push({
                type: 'update_frequency',
                priority: 'low',
                message: '考慮增加某些資料來源的更新頻率以保持資料新鮮度'
            });
        }

        // 資料多樣性建議
        const categories = new Set(results.flatMap(r => r.categories));
        if (categories.size < 8) {
            recommendations.push({
                type: 'diversity',
                priority: 'medium',
                message: '建議增加更多類別的資料來源以提升資料多樣性'
            });
        }

        return recommendations;
    }

    async getDataSourcesStatus() {
        const status = {
            timestamp: new Date().toISOString(),
            totalSources: this.dataSources.size,
            sources: []
        };

        for (const [sourceId, sourceConfig] of this.dataSources.entries()) {
            const sourceStatus = {
                id: sourceId,
                name: sourceConfig.name,
                type: sourceConfig.type,
                priority: sourceConfig.priority,
                dataQuality: sourceConfig.dataQuality,
                categories: sourceConfig.categories,
                hasData: false,
                latestDataFile: null,
                dataCount: 0
            };

            try {
                // 檢查是否有資料
                const files = await fs.readdir(this.outputDir);
                const sourceFiles = files.filter(file =>
                    file.includes(sourceId) ||
                    (sourceId === 'met_museum' && file.includes('met_museum')) ||
                    (sourceId === 'google_books' && file.includes('google_books'))
                );

                if (sourceFiles.length > 0) {
                    sourceStatus.hasData = true;
                    sourceStatus.latestDataFile = sourceFiles.sort().pop();

                    // 讀取資料數量
                    const filePath = path.join(this.outputDir, sourceStatus.latestDataFile);
                    const content = await fs.readFile(filePath, 'utf8');
                    const data = JSON.parse(content);
                    sourceStatus.dataCount = Array.isArray(data) ? data.length : (data.data?.length || 0);
                }
            } catch (error) {
                console.warn(`檢查 ${sourceId} 狀態時出錯: ${error.message}`);
            }

            status.sources.push(sourceStatus);
        }

        return status;
    }
}

// 導出模組
module.exports = UnifiedDataSourceManager;

// 直接執行
if (require.main === module) {
    async function main() {
        const manager = new UnifiedDataSourceManager();

        // 解析命令列參數
        const args = process.argv.slice(2);
        const options = {};

        if (args.includes('--status')) {
            // 顯示資料來源狀態
            const status = await manager.getDataSourcesStatus();
            console.log('📊 資料來源狀態報告:');
            console.log(JSON.stringify(status, null, 2));
            return;
        }

        if (args.includes('--sources')) {
            const sourcesIndex = args.indexOf('--sources');
            if (sourcesIndex !== -1 && args[sourcesIndex + 1]) {
                options.sources = args[sourcesIndex + 1].split(',');
            }
        }

        try {
            await manager.crawlAllSources(options);
        } catch (error) {
            console.error('❌ 統一資料來源管理失敗:', error.message);
            process.exit(1);
        }
    }

    main();
}