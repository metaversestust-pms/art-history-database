# 多模態RAG系統上下文文件夾結構

## 🗂️ 完整目錄結構

```
art-history-database/
├── context/
│   ├── rag-frameworks/                    # RAG框架配置
│   │   ├── advanced-rag/                  # 進階RAG配置
│   │   │   ├── config.yaml               # 主要配置
│   │   │   ├── query-decomposition.json  # 查詢分解規則
│   │   │   ├── fusion-strategies.yaml    # 融合策略
│   │   │   ├── reasoning-chains.json     # 推理鏈模板
│   │   │   └── evaluation-metrics.yaml   # 評估指標
│   │   ├── vector-rag/                   # 向量RAG配置
│   │   │   ├── config.yaml
│   │   │   ├── embedding-models.json     # 嵌入模型配置
│   │   │   ├── similarity-thresholds.yaml # 相似度閾值
│   │   │   ├── index-settings.json       # 索引設置
│   │   │   └── ranking-algorithms.yaml   # 排序算法
│   │   ├── multilingual-rag/             # 多語言RAG配置
│   │   │   ├── config.yaml
│   │   │   ├── language-mappings.json    # 語言映射
│   │   │   ├── cultural-contexts.yaml    # 文化語境
│   │   │   ├── translation-models.json   # 翻譯模型
│   │   │   └── terminology-dictionaries/ # 術語詞典
│   │   │       ├── art-terms-zh.json
│   │   │       ├── art-terms-en.json
│   │   │       ├── art-terms-fr.json
│   │   │       └── art-terms-de.json
│   │   ├── graph-rag/                    # 圖譜RAG配置
│   │   │   ├── config.yaml
│   │   │   ├── neo4j-schema.cypher       # 圖譜結構
│   │   │   ├── relationship-types.json   # 關係類型定義
│   │   │   ├── entity-extraction.yaml    # 實體提取規則
│   │   │   ├── graph-algorithms.json     # 圖算法配置
│   │   │   └── cypher-templates/         # 查詢模板
│   │   │       ├── artist-relationships.cypher
│   │   │       ├── artwork-connections.cypher
│   │   │       ├── period-transitions.cypher
│   │   │       └── influence-paths.cypher
│   │   └── self-reflection-rag/          # 自反思RAG配置
│   │       ├── config.yaml
│   │       ├── quality-metrics.json      # 品質指標
│   │       ├── verification-rules.yaml   # 驗證規則
│   │       ├── confidence-models.json    # 置信度模型
│   │       └── correction-strategies.yaml # 修正策略
│   ├── llm-models/                       # LLM模型配置
│   │   ├── openai/                       # OpenAI模型
│   │   │   ├── gpt-4-config.yaml
│   │   │   ├── gpt-3.5-config.yaml
│   │   │   ├── ada-embeddings.json
│   │   │   └── prompt-templates/
│   │   │       ├── art-history-prompts.yaml
│   │   │       ├── analysis-prompts.yaml
│   │   │       └── comparison-prompts.yaml
│   │   ├── anthropic/                    # Anthropic模型
│   │   │   ├── claude-3-config.yaml
│   │   │   ├── claude-2-config.yaml
│   │   │   └── prompt-templates/
│   │   ├── open-source/                  # 開源模型
│   │   │   ├── llama2-config.yaml
│   │   │   ├── vicuna-config.yaml
│   │   │   ├── chatglm-config.yaml
│   │   │   └── local-deployment/
│   │   │       ├── docker-configs/
│   │   │       └── model-weights/
│   │   ├── custom-models/                # 自定義模型
│   │   │   ├── art-specialist-model.yaml
│   │   │   ├── multilingual-model.yaml
│   │   │   ├── fine-tuning/
│   │   │   │   ├── training-data/
│   │   │   │   ├── training-configs/
│   │   │   │   └── model-checkpoints/
│   │   │   └── evaluation/
│   │   └── experimental/                 # 實驗模型
│   │       ├── gpt-oss-20b.yaml
│   │       ├── gemma3-4b.yaml
│   │       ├── model-comparison.json
│   │       └── ab-test-configs/
│   ├── multimodal/                       # 多模態配置
│   │   ├── text-processing/              # 文本處理
│   │   │   ├── tokenizers/
│   │   │   ├── embeddings/
│   │   │   │   ├── bge-m3.yaml
│   │   │   │   ├── ada-002.yaml
│   │   │   │   └── multilingual-models.yaml
│   │   │   ├── preprocessing/
│   │   │   │   ├── cleaning-rules.yaml
│   │   │   │   ├── normalization.json
│   │   │   │   └── language-detection.yaml
│   │   │   └── postprocessing/
│   │   ├── image-processing/             # 圖像處理
│   │   │   ├── vision-models/
│   │   │   │   ├── clip-config.yaml
│   │   │   │   ├── blip-config.yaml
│   │   │   │   └── custom-vision.yaml
│   │   │   ├── feature-extraction/
│   │   │   │   ├── color-analysis.yaml
│   │   │   │   ├── style-detection.yaml
│   │   │   │   └── object-recognition.yaml
│   │   │   ├── preprocessing/
│   │   │   │   ├── resize-configs.yaml
│   │   │   │   ├── normalization.yaml
│   │   │   │   └── augmentation.yaml
│   │   │   └── datasets/
│   │   │       ├── art-images-metadata.json
│   │   │       └── style-classification-labels.yaml
│   │   ├── audio-processing/             # 音頻處理
│   │   │   ├── speech-models/
│   │   │   │   ├── whisper-config.yaml
│   │   │   │   ├── wavenet-config.yaml
│   │   │   │   └── multilingual-asr.yaml
│   │   │   ├── feature-extraction/
│   │   │   ├── preprocessing/
│   │   │   └── datasets/
│   │   └── fusion/                       # 多模態融合
│   │       ├── alignment-strategies.yaml  # 對齊策略
│   │       ├── fusion-architectures.json # 融合架構
│   │       ├── cross-modal-attention.yaml # 跨模態注意力
│   │       └── unified-embeddings.json   # 統一嵌入
│   ├── knowledge-bases/                  # 知識庫配置
│   │   ├── structured/                   # 結構化知識
│   │   │   ├── postgresql/
│   │   │   │   ├── schema-definitions.sql
│   │   │   │   ├── index-optimizations.sql
│   │   │   │   ├── data-migrations/
│   │   │   │   └── backup-strategies.yaml
│   │   │   ├── mongodb/
│   │   │   │   ├── collection-schemas.json
│   │   │   │   ├── aggregation-pipelines.js
│   │   │   │   └── indexing-strategies.json
│   │   │   └── elasticsearch/
│   │   │       ├── mapping-templates.json
│   │   │       ├── search-configs.yaml
│   │   │       ├── analyzers.json
│   │   │       └── aggregation-queries.json
│   │   ├── vector-stores/                # 向量存儲
│   │   │   ├── chromadb/
│   │   │   │   ├── collection-configs.yaml
│   │   │   │   ├── embedding-functions.json
│   │   │   │   └── persistence-settings.yaml
│   │   │   ├── pinecone/
│   │   │   │   ├── index-configurations.yaml
│   │   │   │   ├── namespace-strategies.json
│   │   │   │   └── metadata-filters.yaml
│   │   │   ├── weaviate/
│   │   │   │   ├── schema-definitions.yaml
│   │   │   │   ├── module-configurations.json
│   │   │   │   └── vectorization-settings.yaml
│   │   │   └── milvus/
│   │   │       ├── collection-schemas.yaml
│   │   │       ├── index-parameters.json
│   │   │       └── partition-strategies.yaml
│   │   ├── graph-databases/              # 圖資料庫
│   │   │   ├── neo4j/
│   │   │   │   ├── constraints.cypher
│   │   │   │   ├── indexes.cypher
│   │   │   │   ├── procedures/
│   │   │   │   └── plugins/
│   │   │   └── alternative-graphs/
│   │   │       ├── arangodb/
│   │   │       └── tigergraph/
│   │   └── external-apis/                # 外部API
│   │       ├── museum-apis/
│   │       │   ├── met-museum.yaml
│   │       │   ├── louvre.yaml
│   │       │   ├── british-museum.yaml
│   │       │   └── europeana.yaml
│   │       ├── academic-databases/
│   │       │   ├── jstor-config.yaml
│   │       │   ├── academia-config.yaml
│   │       │   └── researchgate-config.yaml
│   │       └── market-data/
│   │           ├── auction-houses.yaml
│   │           └── art-market-apis.yaml
│   ├── experiments/                      # 實驗管理
│   │   ├── experiment-designs/           # 實驗設計
│   │   │   ├── ab-test-templates.yaml
│   │   │   ├── multivariate-tests.json
│   │   │   ├── baseline-comparisons.yaml
│   │   │   └── experimental-protocols.md
│   │   ├── test-datasets/                # 測試數據集
│   │   │   ├── question-sets/
│   │   │   │   ├── basic-knowledge.json
│   │   │   │   ├── complex-reasoning.json
│   │   │   │   ├── relationship-queries.json
│   │   │   │   └── multilingual-queries.json
│   │   │   ├── ground-truth/
│   │   │   │   ├── expert-annotations.json
│   │   │   │   ├── reference-answers.yaml
│   │   │   │   └── quality-standards.md
│   │   │   └── synthetic-data/
│   │   │       ├── generated-questions.json
│   │   │       └── augmented-datasets.yaml
│   │   ├── evaluation-frameworks/        # 評估框架
│   │   │   ├── automatic-evaluation/
│   │   │   │   ├── bleu-rouge-configs.yaml
│   │   │   │   ├── bert-score-settings.json
│   │   │   │   ├── fact-checking-rules.yaml
│   │   │   │   └── semantic-similarity.json
│   │   │   ├── human-evaluation/
│   │   │   │   ├── annotation-guidelines.md
│   │   │   │   ├── inter-rater-reliability.yaml
│   │   │   │   ├── expert-rubrics.json
│   │   │   │   └── crowdsourcing-configs.yaml
│   │   │   └── hybrid-evaluation/
│   │   │       ├── combined-metrics.yaml
│   │   │       ├── weighted-scoring.json
│   │   │       └── confidence-intervals.yaml
│   │   ├── performance-monitoring/       # 性能監控
│   │   │   ├── metrics-collection.yaml
│   │   │   ├── alerting-rules.json
│   │   │   ├── dashboard-configs.yaml
│   │   │   └── profiling-settings.json
│   │   └── results-analysis/             # 結果分析
│   │       ├── statistical-tests.yaml
│   │       ├── visualization-templates.json
│   │       ├── report-generators.yaml
│   │       └── decision-frameworks.json
│   ├── agents/                          # Agent配置(擴展原有結構)
│   │   ├── web_crawler/
│   │   │   ├── multimodal-crawling.yaml  # 多模態爬取配置
│   │   │   ├── image-extraction.json
│   │   │   ├── audio-collection.yaml
│   │   │   └── quality-filters.json
│   │   ├── metadata_extractor/
│   │   │   ├── multimodal-extraction.yaml
│   │   │   ├── image-metadata.json
│   │   │   ├── audio-transcription.yaml
│   │   │   └── cross-modal-linking.json
│   │   ├── classification/
│   │   │   ├── multimodal-classification.yaml
│   │   │   ├── visual-style-analysis.json
│   │   │   ├── audio-content-classification.yaml
│   │   │   └── cross-modal-features.json
│   │   └── summarization_translation/
│   │       ├── multimodal-summarization.yaml
│   │       ├── image-captioning.json
│   │       ├── audio-summarization.yaml
│   │       └── cross-modal-translation.json
│   ├── deployment/                      # 部署配置(擴展原有結構)
│   │   ├── docker-compose-multimodal.yml
│   │   ├── kubernetes/
│   │   │   ├── rag-frameworks/
│   │   │   ├── vector-stores/
│   │   │   ├── graph-databases/
│   │   │   └── monitoring/
│   │   ├── cloud-configs/
│   │   │   ├── aws-configs.yaml
│   │   │   ├── gcp-configs.yaml
│   │   │   └── azure-configs.yaml
│   │   ├── scaling/
│   │   │   ├── auto-scaling-rules.yaml
│   │   │   ├── load-balancing.json
│   │   │   └── resource-allocation.yaml
│   │   └── security/
│   │       ├── access-controls.yaml
│   │       ├── api-rate-limits.json
│   │       └── data-encryption.yaml
│   └── ui-interfaces/                   # 用戶界面配置
│       ├── openwebui/
│       │   ├── custom-themes.css
│       │   ├── model-configurations.json
│       │   ├── user-preferences.yaml
│       │   └── plugin-configs.json
│       ├── experiment-dashboard/
│       │   ├── dashboard-layouts.json
│       │   ├── visualization-configs.yaml
│       │   ├── user-roles.json
│       │   └── reporting-templates.yaml
│       ├── admin-panel/
│       │   ├── system-monitoring.yaml
│       │   ├── user-management.json
│       │   ├── model-switching.yaml
│       │   └── experiment-controls.json
│       └── mobile-interfaces/
│           ├── responsive-configs.yaml
│           ├── mobile-optimizations.json
│           └── app-configurations.yaml
├── data/                               # 數據存儲(擴展原有結構)
│   ├── raw/
│   │   ├── text/
│   │   ├── images/
│   │   ├── audio/
│   │   ├── video/
│   │   └── 3d-models/
│   ├── processed/
│   │   ├── embeddings/
│   │   │   ├── text-vectors/
│   │   │   ├── image-vectors/
│   │   │   ├── audio-vectors/
│   │   │   └── multimodal-vectors/
│   │   ├── structured/
│   │   │   ├── sql-exports/
│   │   │   ├── json-documents/
│   │   │   └── graph-exports/
│   │   └── preprocessed/
│   │       ├── cleaned-text/
│   │       ├── normalized-images/
│   │       └── transcribed-audio/
│   ├── experiments/
│   │   ├── test-results/
│   │   ├── performance-logs/
│   │   ├── comparison-data/
│   │   └── user-feedback/
│   └── backups/
│       ├── daily/
│       ├── weekly/
│       └── monthly/
└── models/                             # 模型存儲(擴展原有結構)
    ├── language-models/
    │   ├── fine-tuned/
    │   ├── checkpoints/
    │   └── weights/
    ├── embedding-models/
    │   ├── text-embeddings/
    │   ├── image-embeddings/
    │   ├── audio-embeddings/
    │   └── multimodal-embeddings/
    ├── classification-models/
    │   ├── style-classifiers/
    │   ├── period-detectors/
    │   └── quality-assessors/
    └── experimental/
        ├── ablation-studies/
        ├── prototype-models/
        └── benchmark-results/
```

## 📋 關鍵配置文件說明

### RAG框架配置示例

#### 1. advanced-rag/config.yaml
```yaml
framework_name: "art-history-advanced-rag"
version: "1.0.0"
components:
  query_decomposer:
    enabled: true
    strategies: ["temporal", "thematic", "comparative"]
  retrieval_fusion:
    vector_weight: 0.4
    graph_weight: 0.3
    keyword_weight: 0.3
  reasoning_engine:
    chain_of_thought: true
    multi_hop_reasoning: true
    consistency_check: true
evaluation:
  response_time_threshold: 5000  # ms
  accuracy_threshold: 0.85
  completeness_threshold: 0.8
```

#### 2. vector-rag/embedding-models.json
```json
{
  "primary_model": {
    "name": "BGE-M3",
    "model_path": "BAAI/bge-m3",
    "dimension": 1024,
    "languages": ["zh", "en", "fr", "de", "it", "ja", "ko"]
  },
  "backup_models": [
    {
      "name": "OpenAI-Ada-002",
      "api_endpoint": "openai",
      "dimension": 1536
    },
    {
      "name": "Sentence-BERT",
      "model_path": "sentence-transformers/all-MiniLM-L6-v2",
      "dimension": 384
    }
  ],
  "specialized_models": {
    "art_terms": "custom-art-embeddings-v1",
    "multilingual": "xlm-roberta-large",
    "domain_specific": "art-history-bert-base"
  }
}
```

### 實驗配置示例

#### experiments/ab-test-templates.yaml
```yaml
experiment_template:
  name: "RAG Framework Comparison"
  type: "multivariate"
  duration: "7 days"
  sample_size: 1000
  confidence_level: 0.95

  factors:
    - name: "rag_framework"
      levels: ["advanced", "vector", "graph", "multilingual", "self-reflection"]
    - name: "llm_model"
      levels: ["gpt-4", "claude-3", "gpt-oss-20b", "gemma3-4b"]

  metrics:
    primary:
      - name: "accuracy"
        type: "continuous"
        measurement: "automated_evaluation"
      - name: "response_time"
        type: "continuous"
        measurement: "system_log"

    secondary:
      - name: "user_satisfaction"
        type: "ordinal"
        measurement: "user_rating"
      - name: "completeness"
        type: "continuous"
        measurement: "expert_evaluation"

  randomization:
    method: "stratified"
    blocking_factors: ["user_type", "query_complexity"]

  analysis_plan:
    statistical_tests: ["anova", "tukey_hsd", "t_test"]
    effect_size_calculation: true
    multiple_comparisons_correction: "bonferroni"
```

### 多模態配置示例

#### multimodal/fusion/alignment-strategies.yaml
```yaml
alignment_strategies:
  text_image:
    method: "clip_based"
    model: "openai/clip-vit-large-patch14"
    similarity_threshold: 0.7

  text_audio:
    method: "wav2vec_bert"
    models:
      audio: "facebook/wav2vec2-base"
      text: "bert-base-uncased"
    alignment_layer: "cross_attention"

  image_audio:
    method: "multimodal_transformer"
    fusion_strategy: "late_fusion"
    attention_mechanism: "multi_head"

  triple_alignment:
    text_image_audio:
      method: "unified_embedding_space"
      projection_dim: 512
      loss_function: "triplet_loss"
      margin: 0.2
```

## 🎯 配置文件優先級

1. **環境特定配置** (最高優先級)
   - `.env.local`, `.env.production`

2. **實驗配置**
   - `experiments/active-experiment.yaml`

3. **框架配置**
   - `rag-frameworks/{framework}/config.yaml`

4. **模型配置**
   - `llm-models/{provider}/{model}-config.yaml`

5. **默認配置** (最低優先級)
   - `defaults/system-defaults.yaml`

---

*這個上下文結構支持完整的多模態RAG系統，包括5種框架變體、多種LLM組合、科學實驗設計和全面的評估分析。*