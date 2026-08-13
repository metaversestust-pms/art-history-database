# 藝術史多模態RAG實驗環境

## 📋 概述

這是一個完整的藝術史多模態RAG實驗環境，用於評估不同RAG架構和LLM模型在藝術史領域的性能。

## 🚀 快速開始

### 1. 環境準備

```bash
# 運行環境準備腳本
python3 scripts/prepare_experiment_environment.py

# 啟動實驗環境
./start_experiments.sh
```

### 2. 手動啟動服務

```bash
# 啟動Docker服務
docker-compose -f docker-compose.experiments.yml up -d

# 運行實驗
cd src/experiments
python3 art_history_experiment_suite.py
```

## 📊 服務訪問

- **Grafana 監控儀表板**: http://localhost:3001 (admin/admin123)
- **MLflow 實驗追蹤**: http://localhost:5000
- **Prometheus 監控**: http://localhost:9090
- **ChromaDB**: http://localhost:8020
- **Qdrant**: http://localhost:6333

## 🔬 實驗階段

### Phase 1: 基準性能測試
- 測試5種RAG框架 × 5種LLM模型 = 25種組合
- 評估指標：準確率、響應時間、成功率

### Phase 2: 多模態能力測試
- 測試文本、圖像、音頻等多模態數據處理能力
- 評估跨模態檢索和融合效果

### Phase 3: 領域專業化測試
- 測試在藝術史專業知識上的表現
- 評估複雜推理和文化語境理解能力

### Phase 4: 優化調參測試
- 基於前期結果優化最佳組合的參數
- 提供生產環境的配置建議

## 📁 目錄結構

```
art-history-database/
├── data/experiments/          # 實驗數據
│   ├── images/               # 圖像數據
│   ├── audio/                # 音頻數據
│   └── experiment_config.json # 實驗配置
├── src/experiments/          # 實驗代碼
│   └── art_history_experiment_suite.py
├── results/                  # 實驗結果
│   ├── experiments/          # 實驗數據
│   └── reports/              # 實驗報告
├── docker-compose.experiments.yml # Docker服務配置
└── start_experiments.sh      # 啟動腳本
```

## 🛠️ 故障排除

### 常見問題

1. **Docker服務啟動失敗**
   ```bash
   docker-compose -f docker-compose.experiments.yml logs
   ```

2. **端口衝突**
   - 修改 docker-compose.experiments.yml 中的端口映射
   - 或停止衝突的服務

3. **實驗失敗**
   - 檢查 logs/ 目錄下的日誌文件
   - 確認MCP工具服務運行正常

### 系統要求

- **內存**: 至少8GB RAM
- **磁盤**: 至少10GB可用空間
- **Docker**: 版本20.10+
- **Python**: 版本3.9+

## 📈 實驗結果解讀

實驗完成後將生成：
- 詳細的性能對比報告
- 最佳配置推薦
- 可視化儀表板
- 原始實驗數據

查看結果：
- 在 `results/reports/` 目錄找到生成的報告
- 通過 Grafana 查看實時監控數據
- 通過 MLflow 查看實驗追蹤記錄
