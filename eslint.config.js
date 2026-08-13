'use strict';

/**
 * ESLint 9 flat config。
 *
 * 分工：排版一律交給 Prettier（見 .prettierrc.json），這裡只管邏輯正確性，
 * 避免兩套工具互相打架。
 *
 * 規則選擇依據實測現況：全 repo 為 CommonJS、0 個 var、0 個 ==，
 * 因此 no-var / eqeqeq 直接設為 error 不會產生既有噪音。
 */

const js = require('@eslint/js');
const globals = require('globals');

module.exports = [
    {
        ignores: [
            'node_modules/**',
            'coverage/**',
            '_legacy_archive_20260806/**',
            'db_backups/**',
            'data/**',
            'notebooks/**',
            'public/**',
            '**/*.min.js'
        ]
    },

    js.configs.recommended,

    {
        languageOptions: {
            ecmaVersion: 2023,
            sourceType: 'commonjs',
            globals: {
                ...globals.node,
                ...globals.es2023
            }
        },
        rules: {
            // 既有程式碼已 100% 符合，設為 error 可防止回退。
            'no-var': 'error',
            eqeqeq: ['error', 'always', { null: 'ignore' }],

            // 存量問題設為 warn，不阻擋 lint 通過，但持續可見。
            'no-unused-vars': [
                'warn',
                { argsIgnorePattern: '^_', varsIgnorePattern: '^_', caughtErrors: 'none' }
            ],
            'prefer-const': 'warn',
            'no-empty': ['warn', { allowEmptyCatch: true }],

            'no-throw-literal': 'error',
            'no-return-await': 'warn',
            'require-atomic-updates': 'off'
        }
    },

    {
        // 應用程式碼已有 winston logger（src/utils/logger.js），
        // 直接用 console 會繞過結構化日誌與檔案輪替。
        files: ['src/**/*.js', 'agents/**/*.js'],
        rules: {
            'no-console': 'warn'
        }
    },

    {
        // 一次性腳本、爬蟲、測試工具用 console 是合理的。
        files: ['scripts/**/*.js', 'tests/**/*.js', '*.js'],
        rules: {
            'no-console': 'off'
        }
    },

    {
        files: ['tests/**/*.js', '**/*.test.js', '**/*.spec.js'],
        languageOptions: {
            globals: {
                ...globals.jest
            }
        }
    },

    {
        // OpenWebUI 的自訂模型管理腳本是在瀏覽器裡執行的前端程式碼。
        files: ['openwebui-config/**/*.js', 'public/**/*.js'],
        languageOptions: {
            globals: {
                ...globals.browser
            }
        }
    },

    {
        // 爬蟲會把 callback 丟進 page.evaluate() 於瀏覽器分頁內執行，
        // 那個 scope 裡的 document / window 是合法的。
        files: ['agents/web-crawler/**/*.js', '**/*crawler*.js', 'src/utils/crawlerWorker.js'],
        languageOptions: {
            globals: {
                ...globals.browser
            }
        }
    },

    {
        // 這裡的控制字元是刻意的：dataCleaner 的職責就是把它們從輸入中剝除。
        files: ['src/utils/dataCleaner.js'],
        rules: {
            'no-control-regex': 'off'
        }
    }
];
