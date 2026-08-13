#!/usr/bin/env node
/**
 * 增強爬蟲啟動腳本
 * 統一管理和啟動所有新增的資料來源爬蟲
 */

const fs = require('fs/promises');
const path = require('path');

// 導入所有模組
const EuropeanaCrawler = require('./europeana-crawler');
const GoogleScholarCrawler = require('./google-scholar-crawler');
const UnifiedDataSourceManager = require('./unified-data-sources-manager');

class EnhancedCrawlerLauncher {
    constructor() {
        this.crawlers = new Map();
        this.results = [];
        this.errors = [];

        // 註冊爬蟲
        this.registerCrawlers();
    }

    registerCrawlers() {
        // Europeana 爬蟲
        this.crawlers.set('europeana', {
            name: 'Europeana Cultural Heritage',
            crawler: new EuropeanaCrawler(),
            method: 'crawlAllSources',
            description: '歐洲數位文化遺產平台資料收集',
            priority: 1,
            estimatedTime: '10-15分鐘',
            expectedResults: '300-500項文化遺產資料'
        });

        // Google Scholar 爬蟲
        this.crawlers.set('google_scholar', {
            name: 'Google Scholar Academic',
            crawler: new GoogleScholarCrawler(),
            method: 'crawlAllQueries',
            description: '學術論文和研究文獻收集',
            priority: 2,
            estimatedTime: '15-25分鐘',
            expectedResults: '200-400篇學術論文'
        });
    }

    async startCrawler(crawlerId, options = {}) {
        const crawlerConfig = this.crawlers.get(crawlerId);

        if (!crawlerConfig) {
            throw new Error(`未知的爬蟲: ${crawlerId}`);
        }

        console.log(`\n🚀 啟動 ${crawlerConfig.name}...`);
        console.log(`📋 描述: ${crawlerConfig.description}`);
        console.log(`⏱️  預估時間: ${crawlerConfig.estimatedTime}`);
        console.log(`📊 預期結果: ${crawlerConfig.expectedResults}`);

        const startTime = Date.now();

        try {
            // 執行爬蟲
            let result;
            if (crawlerConfig.method === 'crawlAllSources') {
                result = await crawlerConfig.crawler.crawlAllSources(options);
            } else if (crawlerConfig.method === 'crawlAllQueries') {
                result = await crawlerConfig.crawler.crawlAllQueries(options);
            }

            const endTime = Date.now();
            const duration = (endTime - startTime) / 1000 / 60; // 轉換為分鐘

            const crawlResult = {
                crawlerId,
                name: crawlerConfig.name,
                status: 'success',
                duration: `${duration.toFixed(2)} 分鐘`,
                dataCount: Array.isArray(result) ? result.length : (result?.length || 0),
                timestamp: new Date().toISOString(),
                result: result
            };

            this.results.push(crawlResult);

            console.log(`✅ ${crawlerConfig.name} 完成！`);
            console.log(`   📊 收集資料: ${crawlResult.dataCount} 項`);
            console.log(`   ⏱️  實際耗時: ${crawlResult.duration}`);

            return crawlResult;

        } catch (error) {
            const endTime = Date.now();
            const duration = (endTime - startTime) / 1000 / 60;

            const errorResult = {
                crawlerId,
                name: crawlerConfig.name,
                status: 'error',
                duration: `${duration.toFixed(2)} 分鐘`,
                error: error.message,
                timestamp: new Date().toISOString()
            };

            this.errors.push(errorResult);

            console.error(`❌ ${crawlerConfig.name} 失敗！`);
            console.error(`   錯誤: ${error.message}`);
            console.error(`   耗時: ${errorResult.duration}`);

            throw error;
        }
    }

    async startAllCrawlers(options = {}) {
        console.log('🌟 增強爬蟲系統啟動');
        console.log('====================================');

        const { concurrent = false, skipOnError = false, crawlers = null } = options;

        // 選擇要執行的爬蟲
        const crawlersToRun = crawlers
            ? Array.from(this.crawlers.entries()).filter(([id]) => crawlers.includes(id))
            : Array.from(this.crawlers.entries());

        // 按優先級排序
        crawlersToRun.sort((a, b) => a[1].priority - b[1].priority);

        console.log(`📋 計劃執行 ${crawlersToRun.length} 個爬蟲:`);
        crawlersToRun.forEach(([id, config]) => {
            console.log(`   ${config.priority}. ${config.name} (${id})`);
        });

        if (concurrent) {
            console.log('\n🔄 並行模式啟動...');
            await this.runConcurrent(crawlersToRun, options);
        } else {
            console.log('\n🔄 序列模式啟動...');
            await this.runSequential(crawlersToRun, options, skipOnError);
        }

        // 生成摘要報告
        await this.generateSummaryReport();

        return {
            results: this.results,
            errors: this.errors,
            summary: this.getSummary()
        };
    }

    async runSequential(crawlersToRun, options, skipOnError) {
        for (const [crawlerId, config] of crawlersToRun) {
            try {
                await this.startCrawler(crawlerId, options);

                // 爬蟲間延遲
                if (crawlersToRun.indexOf([crawlerId, config]) < crawlersToRun.length - 1) {
                    console.log('⏳ 等待 30 秒後繼續...');
                    await new Promise(resolve => setTimeout(resolve, 30000));
                }

            } catch (error) {
                if (skipOnError) {
                    console.log(`⏭️  跳過失敗的爬蟲: ${config.name}`);
                    continue;
                } else {
                    console.error('🛑 爬蟲執行中斷，停止後續爬蟲');
                    break;
                }
            }
        }
    }

    async runConcurrent(crawlersToRun, options) {
        const promises = crawlersToRun.map(([crawlerId]) =>
            this.startCrawler(crawlerId, options).catch(error => ({ error, crawlerId }))
        );

        const results = await Promise.allSettled(promises);

        results.forEach((result, index) => {
            const [crawlerId, config] = crawlersToRun[index];

            if (result.status === 'fulfilled' && !result.value.error) {
                console.log(`✅ ${config.name} 並行執行成功`);
            } else {
                console.error(`❌ ${config.name} 並行執行失敗`);
            }
        });
    }

    getSummary() {
        const totalCrawlers = this.crawlers.size;
        const successfulCrawlers = this.results.length;
        const failedCrawlers = this.errors.length;
        const totalDataCount = this.results.reduce((sum, result) => sum + result.dataCount, 0);

        const avgDuration = this.results.length > 0
            ? this.results.reduce((sum, result) => sum + parseFloat(result.duration), 0) / this.results.length
            : 0;

        return {
            totalCrawlers,
            successfulCrawlers,
            failedCrawlers,
            totalDataCount,
            averageDuration: `${avgDuration.toFixed(2)} 分鐘`,
            successRate: `${((successfulCrawlers / totalCrawlers) * 100).toFixed(1)}%`
        };
    }

    async generateSummaryReport() {
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        const reportPath = path.join(__dirname, 'data', 'output', `crawler-summary-${timestamp}.json`);

        // 確保目錄存在
        await fs.mkdir(path.dirname(reportPath), exist_ok=true);

        const report = {
            reportInfo: {
                timestamp: new Date().toISOString(),
                reportType: 'Enhanced Crawlers Summary',
                version: '1.0.0'
            },
            summary: this.getSummary(),
            results: this.results,
            errors: this.errors,
            recommendations: this.generateRecommendations(),
            nextSteps: this.generateNextSteps()
        };

        await fs.writeFile(reportPath, JSON.stringify(report, null, 2));

        console.log(`\n📁 摘要報告已保存: ${reportPath}`);

        // 顯示摘要
        const summary = this.getSummary();
        console.log('\n📊 執行摘要:');
        console.log('====================================');
        console.log(`✅ 成功爬蟲: ${summary.successfulCrawlers}/${summary.totalCrawlers}`);
        console.log(`📊 總收集資料: ${summary.totalDataCount} 項`);
        console.log(`⏱️  平均耗時: ${summary.averageDuration}`);
        console.log(`📈 成功率: ${summary.successRate}`);

        if (this.errors.length > 0) {
            console.log(`❌ 失敗的爬蟲: ${this.errors.map(e => e.name).join(', ')}`);
        }

        return reportPath;
    }

    generateRecommendations() {
        const recommendations = [];

        // 基於成功率的建議
        const summary = this.getSummary();
        const successRate = parseInt(summary.successRate);

        if (successRate === 100) {
            recommendations.push({
                type: 'success',
                message: '所有爬蟲執行成功！建議將資料整合到RAG系統中。'
            });
        } else if (successRate >= 75) {
            recommendations.push({
                type: 'good',
                message: '大部分爬蟲執行成功，建議檢查失敗原因並重試。'
            });
        } else {
            recommendations.push({
                type: 'warning',
                message: '多個爬蟲失敗，建議檢查網路連接和API配置。'
            });
        }

        // 基於資料量的建議
        if (summary.totalDataCount > 500) {
            recommendations.push({
                type: 'data_quality',
                message: '收集到大量資料，建議執行資料品質評估和去重處理。'
            });
        }

        // 基於性能的建議
        const avgDuration = parseFloat(summary.averageDuration);
        if (avgDuration > 20) {
            recommendations.push({
                type: 'performance',
                message: '爬蟲執行時間較長，建議考慮並行處理或優化網路請求。'
            });
        }

        return recommendations;
    }

    generateNextSteps() {
        return [
            '1. 檢查收集到的資料品質和完整性',
            '2. 執行資料去重和標準化處理',
            '3. 將新資料整合到向量資料庫',
            '4. 更新知識圖譜結構',
            '5. 測試RAG系統對新資料的檢索效果',
            '6. 調整RAG系統配置以最佳化新資料來源',
            '7. 部署到生產環境並監控性能'
        ];
    }

    // 快速測試方法
    async quickTest() {
        console.log('🧪 快速測試模式');

        try {
            // 測試 Europeana - 只搜索一個關鍵字
            console.log('\n測試 Europeana...');
            const europeanaCrawler = new EuropeanaCrawler();
            const europeanaResult = await europeanaCrawler.searchByQuery('Renaissance', 3);
            console.log(`Europeana 測試: ${europeanaResult.length} 項結果`);

            // 測試 Google Scholar - 只搜索一個關鍵字
            console.log('\n測試 Google Scholar...');
            const scholarCrawler = new GoogleScholarCrawler();
            await scholarCrawler.initBrowser();
            const scholarResult = await scholarCrawler.searchGoogleScholar('art history', 2);
            console.log(`Google Scholar 測試: ${scholarResult.length} 項結果`);
            await scholarCrawler.cleanup();

            console.log('\n✅ 快速測試完成！系統功能正常。');

        } catch (error) {
            console.error('❌ 快速測試失敗:', error.message);
        }
    }
}

// 解析命令列參數
function parseArgs() {
    const args = process.argv.slice(2);
    const options = {
        concurrent: false,
        skipOnError: false,
        crawlers: null,
        test: false,
        quickTest: false
    };

    for (let i = 0; i < args.length; i++) {
        const arg = args[i];

        switch (arg) {
            case '--concurrent':
            case '-c':
                options.concurrent = true;
                break;

            case '--skip-on-error':
            case '-s':
                options.skipOnError = true;
                break;

            case '--crawlers':
                if (args[i + 1]) {
                    options.crawlers = args[i + 1].split(',');
                    i++;
                }
                break;

            case '--test':
            case '-t':
                options.test = true;
                break;

            case '--quick-test':
            case '-q':
                options.quickTest = true;
                break;

            case '--help':
            case '-h':
                printHelp();
                process.exit(0);
                break;
        }
    }

    return options;
}

function printHelp() {
    console.log(`
增強爬蟲啟動腳本

使用方法:
  node start-enhanced-crawlers.js [選項]

選項:
  --concurrent, -c          並行執行爬蟲
  --skip-on-error, -s       發生錯誤時跳過而不停止
  --crawlers <list>         只執行指定的爬蟲 (用逗號分隔)
                           可用值: europeana, google_scholar
  --test, -t               執行完整測試而不是爬蟲
  --quick-test, -q          執行快速測試
  --help, -h               顯示此幫助信息

範例:
  node start-enhanced-crawlers.js
  node start-enhanced-crawlers.js --concurrent
  node start-enhanced-crawlers.js --crawlers europeana
  node start-enhanced-crawlers.js --quick-test
`);
}

// 主程序
if (require.main === module) {
    async function main() {
        const options = parseArgs();
        const launcher = new EnhancedCrawlerLauncher();

        try {
            if (options.quickTest) {
                await launcher.quickTest();
            } else if (options.test) {
                const DataSourceTester = require('./test-enhanced-data-sources');
                const tester = new DataSourceTester();
                await tester.runAllTests();
            } else {
                await launcher.startAllCrawlers(options);
            }

            process.exit(0);

        } catch (error) {
            console.error('❌ 程序執行失敗:', error.message);
            process.exit(1);
        }
    }

    main();
}

module.exports = EnhancedCrawlerLauncher;