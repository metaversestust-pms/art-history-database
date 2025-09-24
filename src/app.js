const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const morgan = require('morgan');
require('dotenv').config();

const app = express();
const PORT = process.env.API_PORT || 3000;

// 中間件設定
app.use(helmet());
app.use(cors());
app.use(morgan('combined'));
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true }));

// 健康檢查端點
app.get('/health', (req, res) => {
  res.status(200).json({
    status: 'healthy',
    message: '藝術史資料庫系統運行正常',
    timestamp: new Date().toISOString(),
    version: process.env.npm_package_version || '1.0.0',
    environment: process.env.NODE_ENV || 'development'
  });
});

// 根路徑
app.get('/', (req, res) => {
  res.json({
    name: '藝術史資料庫爬蟲系統',
    description: '專注於RAG集成的藝術史資料庫爬蟲系統',
    version: '1.0.0',
    endpoints: {
      health: '/health',
      api: '/api/v1',
      docs: '/api/docs'
    },
    agents: {
      webCrawler: 'WebCrawlerAgent',
      metadataExtractor: 'MetadataExtractorAgent',
      classification: 'ClassificationAgent',
      summarizationTranslation: 'SummarizationTranslationAgent'
    }
  });
});

// API v1 路由 (暫時簡化)
app.get('/api/v1', (req, res) => {
  res.json({
    message: 'Art History Database API v1',
    endpoints: [
      'GET /api/v1/artworks',
      'GET /api/v1/artists',
      'GET /api/v1/collections',
      'GET /api/v1/metadata',
      'GET /api/v1/search',
      'GET /api/v1/rag/langchain',
      'GET /api/v1/rag/llamaindex',
      'GET /api/v1/rag/openai',
      'GET /api/v1/rag/custom'
    ]
  });
});

// 環境檢查端點
app.get('/api/v1/status', (req, res) => {
  const status = {
    server: 'running',
    database: 'checking...',
    redis: 'checking...',
    elasticsearch: 'checking...',
    agents: {
      webCrawler: 'not started',
      metadataExtractor: 'not started',
      classification: 'not started',
      summarizationTranslation: 'not started'
    }
  };

  res.json(status);
});

// 錯誤處理中間件
app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(500).json({
    error: 'Internal Server Error',
    message: process.env.NODE_ENV === 'development' ? err.message : 'Something went wrong!'
  });
});

// 404 處理
app.use((req, res) => {
  res.status(404).json({
    error: 'Not Found',
    message: `Route ${req.originalUrl} not found`,
    availableRoutes: ['/', '/health', '/api/v1', '/api/v1/status']
  });
});

// 啟動服務器
app.listen(PORT, () => {
  console.log(`🚀 藝術史資料庫系統啟動成功!`);
  console.log(`📍 服務地址: http://localhost:${PORT}`);
  console.log(`🏥 健康檢查: http://localhost:${PORT}/health`);
  console.log(`📚 API文檔: http://localhost:${PORT}/api/v1`);
  console.log(`🌍 環境: ${process.env.NODE_ENV || 'development'}`);
  console.log(`⏰ 啟動時間: ${new Date().toLocaleString()}`);
});

// 優雅關機
process.on('SIGTERM', () => {
  console.log('👋 接收到SIGTERM信號，正在優雅關機...');
  process.exit(0);
});

process.on('SIGINT', () => {
  console.log('👋 接收到SIGINT信號，正在優雅關機...');
  process.exit(0);
});

module.exports = app;