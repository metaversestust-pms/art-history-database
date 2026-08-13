# 爬蟲運作流程（標準作業步驟）

本文件定義每日爬蟲從「啟動」到「資料可在 Open WebUI 查詢」的完整依序步驟。
對應的自動化腳本：[daily_crawl_and_sync.sh](daily_crawl_and_sync.sh)（可手動執行，也已排程每天 03:00 自動執行）。

## 執行前置檢查

| 步驟 | 動作 | 對應指令 |
|---|---|---|
| 0 | 確認 4 個原生服務（Neo4j / ChromaDB / rag-manager-v2 / Open WebUI）都在運作 | `Start-NativeServices.ps1` |

## 主流程（依序執行，單一來源失敗不中斷後續步驟，每個來源間隔 30 秒避免限流碰撞）

| 步驟 | 來源 | 腳本 | 是否需要 API Key | 備註 |
|---|---|---|---|---|
| 1 | Europeana | `europeana-crawler.js` | ✅ | 唯一有品質分數機制的原始來源 |
| 2 | Harvard Art Museums | `harvard-art-museums-crawler.js` | ✅ | 唯一有「品質分數＋研究價值」雙評分的來源 |
| 3 | MET Museum | `start-single-crawler.js` | ❌ | 依 19 個部門系統性涵蓋 |
| 4 | Renaissance/Baroque（MET API） | `renaissance-baroque-crawler.js` | ❌ | 與步驟3同打 MET API |
| 5 | Specialized Art | `specialized-art-crawler.js` | ❌ | |
| 6 | Google Books | `fetch_google_books.js` | ✅ | 容易碰到 429 限流，屬預期狀況 |
| 7 | Art Institute of Chicago | `art-institute-chicago-crawler.js` | ❌ | 有品質分數機制 |
| 8 | Victoria and Albert Museum | `va-museum-crawler.js` | ❌ | 有品質分數機制 |
| 9 | Cleveland Museum of Art | `cleveland-museum-crawler.js` | ❌ | 有品質分數機制 |

## 資料整合階段

| 步驟 | 動作 | 對應腳本 |
|---|---|---|
| 10 | 檢查重複資料（ID 重複 / 標題+創作者近似重複，僅回報不阻擋） | `check_duplicates.py` |
| 11 | 匯入 Neo4j（除 Europeana 外的 8 個來源） | `import_all_museums_to_neo4j.py` |
| 12 | 同步 Europeana（Neo4j + ChromaDB 雙寫） | `sync_europeana_to_databases.py` |
| 13 | 回報各來源品質分數 | `report_quality_score.py` |
| 14 | 清除 RAG 查詢快取，確保下次查詢拿到最新資料 | `POST /api/v1/cache/clear` |

## ⭐ 累加模式（2026-08-03 起預設行為）

**步驟 11、12 預設都是「累加模式」，不是每天重新整理**：
- 不清除舊資料，只用 `MERGE`（Neo4j）／`upsert`（ChromaDB）依各來源的穩定 id 寫入
- 同一件作品被重複爬到 → 只更新屬性，**不會產生重複節點**
- 不同天爬到不一樣的作品 → 持續累積，資料庫只會越來越完整
- 如果某次爬蟲只抓到之前的子集合，不會因此遺失先前已收集但這次沒抓到的資料

若需要清除重建（例如修正資料品質問題），手動加上 `--clean` 參數：
```bash
python langchain-rag/import_all_museums_to_neo4j.py --clean
```

## 驗證階段

| 步驟 | 動作 |
|---|---|
| 15 | 執行 `diagnose.py` 確認 4 個服務健康狀態、掃描是否有已知錯誤 |
| 16 | （建議）用已知關鍵字（如藝術家名）實際查一次 GraphRAG，確認新資料查得到 |

## 資料品質指標

- **平均品質分數**：Europeana、Harvard、Art Institute of Chicago、V&A Museum、Cleveland Museum of Art 共 5 個來源有此機制（0-100 分制，各自依 API 可取得欄位微調配分），其餘來源（MET、Renaissance/Baroque、Specialized Art、Google Books、Masterpieces Curated）沒有
- **重複率**：`check_duplicates.py` 檢查原始爬蟲檔案層級的重複；Neo4j/ChromaDB 寫入階段另外用 `MERGE`/`upsert` 做二次防呆，就算原始檔案有重複 ID 也不會產生重複節點

## 時間紀錄

- 每次執行的 log 檔案（`logs/daily_crawl/crawl_<timestamp>.log`）會記錄每個步驟的耗時與整體開始/結束時間
- 歷史彙總記錄在 [logs/crawl_history.csv](../logs/crawl_history.csv)，每次執行累加一行（開始時間/結束時間/總耗時/匯入結果/Artwork總筆數），方便追蹤趨勢，不會被自動清理

## 例行執行方式

```powershell
# 完整流程一鍵執行（步驟 0 + 1-14）
.\scripts\Run-DailyCrawl.ps1

# 只檢查重複、健康狀態、品質分數
wsl -d Ubuntu-22.04 -- python3 /mnt/c/Users/user/Desktop/藝術史資料庫/art-history-database/scripts/check_duplicates.py
wsl -d Ubuntu-22.04 -- python3 /mnt/c/Users/user/Desktop/藝術史資料庫/art-history-database/scripts/diagnose.py
wsl -d Ubuntu-22.04 -- python3 /mnt/c/Users/user/Desktop/藝術史資料庫/art-history-database/scripts/report_quality_score.py
```

排程：Windows 工作排程器「**ArtHistoryDB-DailyCrawl**」，每天 03:00 自動執行整套流程。
