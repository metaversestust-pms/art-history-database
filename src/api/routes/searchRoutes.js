/**
 * 搜索路由
 * 提供統一的搜索服務API
 */

const express = require('express');
const searchController = require('../controllers/searchController');
const { rateLimitMiddleware } = require('../middleware/rateLimiter');

const router = express.Router();

// 應用速率限制（factory，必須呼叫 —— 見 collectionRoutes.js 同處說明）。
router.use(rateLimitMiddleware());

// 搜索端點
router.get('/', searchController.globalSearch.bind(searchController));
router.get('/advanced', searchController.advancedSearch.bind(searchController));
router.get('/suggestions', searchController.searchSuggestions.bind(searchController));

module.exports = router;
