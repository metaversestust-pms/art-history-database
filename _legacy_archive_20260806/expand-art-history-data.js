#!/usr/bin/env node
/**
 * 藝術史資料擴增主控腳本
 * 整合多個爬蟲系統，收集藝術史資料並自動向量化整合到RAG系統
 */

const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs/promises');

class ArtHistoryDataExpander {
    constructor() {
        this.baseDir = __dirname;
        this.dataDir = path.join(this.baseDir, 'data', 'raw');
        this.results = {
            crawlers: [],
            totalArtworks: 0,
            timestamp: new Date().toISOString(),
            errors: []
        };
    }

    log(message, type = 'info') {
        const timestamp = new Date().toLocaleTimeString();
        const prefix = {
            'info': '📋',
            'success': '✅',
            'error': '❌',
            'warning': '⚠️',
            'progress': '⏳'
        }[type] || '📋';

        console.log(`[${timestamp}] ${prefix} ${message}`);
    }

    async runCrawler(scriptPath, name, args = []) {
        this.log(`啟動爬蟲: ${name}`, 'progress');

        return new Promise((resolve, reject) => {
            const crawler = spawn('node', [scriptPath, ...args], {
                cwd: this.baseDir,
                stdio: 'inherit'
            });

            const result = {
                name,
                startTime: Date.now(),
                status: 'running'
            };

            crawler.on('close', (code) => {
                result.endTime = Date.now();
                result.duration = (result.endTime - result.startTime) / 1000;

                if (code === 0) {
                    result.status = 'success';
                    this.log(`${name} 完成 (${result.duration.toFixed(1)}秒)`, 'success');
                    resolve(result);
                } else {
                    result.status = 'failed';
                    result.error = `Exit code: ${code}`;
                    this.log(`${name} 失敗 (退出碼: ${code})`, 'error');
                    this.results.errors.push(`${name}: Exit code ${code}`);
                    // 不拒絕，繼續執行其他爬蟲
                    resolve(result);
                }
            });

            crawler.on('error', (error) => {
                result.status = 'failed';
                result.error = error.message;
                this.log(`${name} 錯誤: ${error.message}`, 'error');
                this.results.errors.push(`${name}: ${error.message}`);
                resolve(result);
            });
        });
    }

    async runAllCrawlers() {
        this.log('🚀 開始藝術史資料收集任務', 'info');
        this.log('═══════════════════════════════════════', 'info');

        const crawlers = [
            {
                path: './renaissance-baroque-crawler.js',
                name: '文藝復興與巴洛克時期爬蟲'
            },
            {
                path: './specialized-art-crawler.js',
                name: '專門藝術主題爬蟲'
            },
            {
                path: './harvard-art-museums-crawler.js',
                name: '哈佛藝術博物館爬蟲'
            },
            {
                path: './europeana-crawler.js',
                name: 'Europeana爬蟲'
            }
        ];

        for (const crawler of crawlers) {
            const crawlerPath = path.join(this.baseDir, crawler.path);

            // 檢查爬蟲文件是否存在
            try {
                await fs.access(crawlerPath);
                const result = await this.runCrawler(crawlerPath, crawler.name);
                this.results.crawlers.push(result);
            } catch (error) {
                this.log(`跳過 ${crawler.name}: 文件不存在`, 'warning');
                this.results.crawlers.push({
                    name: crawler.name,
                    status: 'skipped',
                    reason: '文件不存在'
                });
            }

            // 爬蟲之間間隔，避免過載
            await this.delay(3000);
        }

        this.log('═══════════════════════════════════════', 'info');
        this.log('所有爬蟲任務完成', 'success');
    }

    async countCollectedData() {
        this.log('統計收集的資料...', 'progress');

        try {
            const files = await fs.readdir(this.dataDir);
            const jsonFiles = files.filter(f => f.endsWith('.json'));

            let totalItems = 0;
            const dataStats = [];

            for (const file of jsonFiles) {
                // 只統計最近收集的資料
                const stats = await fs.stat(path.join(this.dataDir, file));
                const ageHours = (Date.now() - stats.mtimeMs) / (1000 * 60 * 60);

                if (ageHours < 24) { // 最近24小時的資料
                    try {
                        const content = await fs.readFile(
                            path.join(this.dataDir, file),
                            'utf-8'
                        );
                        const data = JSON.parse(content);

                        let count = 0;
                        if (Array.isArray(data)) {
                            count = data.length;
                        } else if (data.items && Array.isArray(data.items)) {
                            count = data.items.length;
                        } else if (typeof data === 'object') {
                            count = 1;
                        }

                        totalItems += count;
                        dataStats.push({
                            file,
                            items: count,
                            size: (stats.size / 1024).toFixed(2) + ' KB',
                            modified: stats.mtime.toLocaleString()
                        });
                    } catch (parseError) {
                        this.log(`無法解析 ${file}: ${parseError.message}`, 'warning');
                    }
                }
            }

            this.results.totalArtworks = totalItems;
            this.results.dataFiles = dataStats;

            return { totalItems, dataStats };
        } catch (error) {
            this.log(`統計資料時出錯: ${error.message}`, 'error');
            return { totalItems: 0, dataStats: [] };
        }
    }

    async delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    printSummary() {
        this.log('\n' + '═'.repeat(60), 'info');
        this.log('📊 藝術史資料收集摘要', 'info');
        this.log('═'.repeat(60), 'info');

        // 爬蟲執行結果
        this.log('\n🤖 爬蟲執行結果:', 'info');
        this.results.crawlers.forEach(crawler => {
            const statusEmoji = {
                'success': '✅',
                'failed': '❌',
                'skipped': '⚠️'
            }[crawler.status] || '❓';

            const durationStr = crawler.duration
                ? ` (${crawler.duration.toFixed(1)}秒)`
                : '';

            this.log(`  ${statusEmoji} ${crawler.name}${durationStr}`, 'info');

            if (crawler.error) {
                this.log(`     錯誤: ${crawler.error}`, 'error');
            }
        });

        // 資料統計
        this.log('\n📈 收集的資料:', 'info');
        this.log(`  總藝術品數量: ${this.results.totalArtworks}`, 'info');

        if (this.results.dataFiles && this.results.dataFiles.length > 0) {
            this.log('\n  最近收集的文件:', 'info');
            this.results.dataFiles.forEach(file => {
                this.log(`    - ${file.file}: ${file.items} 項 (${file.size})`, 'info');
            });
        }

        // 錯誤摘要
        if (this.results.errors.length > 0) {
            this.log('\n⚠️ 錯誤摘要:', 'warning');
            this.results.errors.forEach(error => {
                this.log(`  - ${error}`, 'warning');
            });
        }

        // 成功率
        const total = this.results.crawlers.length;
        const successful = this.results.crawlers.filter(c => c.status === 'success').length;
        const successRate = total > 0 ? (successful / total * 100).toFixed(1) : 0;

        this.log(`\n📊 成功率: ${successful}/${total} (${successRate}%)`, 'info');

        // 下一步指示
        this.log('\n' + '═'.repeat(60), 'info');
        this.log('🔄 下一步: 向量化與整合', 'info');
        this.log('═'.repeat(60), 'info');
        this.log('執行以下命令進行資料整合:', 'info');
        this.log('  1. 向量化並導入ChromaDB:', 'info');
        this.log('     node integrate-to-chromadb.js', 'info');
        this.log('  2. 整合到Neo4j圖譜:', 'info');
        this.log('     node integrate-to-neo4j.js', 'info');
        this.log('  3. 測試RAG系統:', 'info');
        this.log('     node test-rag-integration.js', 'info');
        this.log('═'.repeat(60) + '\n', 'info');
    }

    async saveSummary() {
        const summaryPath = path.join(this.baseDir, 'data-expansion-summary.json');
        try {
            await fs.writeFile(
                summaryPath,
                JSON.stringify(this.results, null, 2),
                'utf-8'
            );
            this.log(`摘要已保存到: ${summaryPath}`, 'success');
        } catch (error) {
            this.log(`保存摘要失敗: ${error.message}`, 'error');
        }
    }

    async run() {
        const startTime = Date.now();

        try {
            // 執行所有爬蟲
            await this.runAllCrawlers();

            // 統計收集的資料
            await this.countCollectedData();

            // 打印摘要
            this.printSummary();

            // 保存摘要
            await this.saveSummary();

            const totalTime = ((Date.now() - startTime) / 1000 / 60).toFixed(1);
            this.log(`\n✨ 資料擴增任務完成！總耗時: ${totalTime} 分鐘`, 'success');

        } catch (error) {
            this.log(`資料擴增任務失敗: ${error.message}`, 'error');
            this.log(error.stack, 'error');
            process.exit(1);
        }
    }
}

// 執行主程序
if (require.main === module) {
    const expander = new ArtHistoryDataExpander();
    expander.run().catch(error => {
        console.error('致命錯誤:', error);
        process.exit(1);
    });
}

module.exports = ArtHistoryDataExpander;
