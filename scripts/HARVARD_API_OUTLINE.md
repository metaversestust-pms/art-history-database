# Harvard Art Museums API 整合大綱

## 一、API Key 設定

| 項目 | 內容 |
|---|---|
| 設定位置 | `.env` 檔案，`HARVARD_API_KEY=c686b1a5-43d0-431f-90b2-e9097fec7ea9` |
| 讀取方式 | `harvard-art-museums-crawler.js` 底部 `require('dotenv').config()` 載入，`process.env.HARVARD_API_KEY` 或命令列參數傳入 |
| 申請頁面 | https://www.harvardartmuseums.org/collections/api |
| 目前狀態 | ✅ 有效，已驗證正常運作（2026-08-01 測試成功抓到 96 筆資料，無 401/403 認證錯誤） |
| 每日限制 | 程式設定 `dailyLimit = 2500` 次呼叫／天，每次請求間隔 1 秒（`makeApiCall`） |
| 逾時處理 | 遇 429 限流會自動等待 5 秒後重試；遇 401 直接拋出「API Key 無效或已過期」錯誤 |

## 二、API 端點與查詢策略

| 端點 | 用途 |
|---|---|
| `GET /object` | 主要搜尋端點，依 `q` 參數查詢作品，`hasimage=1` 只取有圖片的物件 |
| `GET /person` | 依藝術家姓名查詢 Harvard 內部人物 ID，再用 `person:{id}` 查該藝術家作品 |

**四種查詢方式**（`crawlComprehensive` 依比例分配數量）：

1. **分類查詢**（40%）：`classification:Paintings`、`Sculptures`、`Drawings`、`Prints`、`Photographs`、`Textiles`、`Ceramics`、`Furniture`、`Metalwork`、`Jewelry`、`Books`、`Manuscripts`（共12類）
2. **藝術家查詢**（30%）：Picasso、Van Gogh、Monet、Renoir、Degas 等前5位知名藝術家（先查 `/person` 取得 ID，再用 ID 查作品）
3. **文化查詢**（20%）：Italian、French、Dutch、German、British 等前5個文化
4. **時期查詢**（10%）：Ancient、Medieval、Renaissance 等前3個時期

## 三、抓取的資料欄位（`processObject`）

| 分類 | 欄位 |
|---|---|
| 基本資訊 | harvardId、objectNumber、title、classification |
| 創作資訊 | people（藝術家陣列：姓名/角色/ID/文化/生卒地/生卒年）、culture、period、century、dated |
| 物理特徵 | medium、dimensions |
| 描述背景 | description、commentary、technique |
| 圖像資源 | primaryImage、images（陣列，含尺寸/說明/版權） |
| 收藏資訊 | accessionYear、provenance、exhibition、publication |
| 分類標籤 | workType、department、division |
| 元數據 | url、lastUpdate、rank |

## 四、獨有的雙評分機制

Harvard 是唯一同時有**兩種**評分的來源（其他博物館只有品質分數）：

### 1. 品質分數（qualityScore，0-100）
- 基本資訊完整性（40分）：標題、藝術家、日期/世紀、媒材
- 圖像資源（25分）：主圖(15) + 多張圖(10)
- 描述與研究價值（20分）：描述(10) + 評論或技法(10)
- 收藏完整性（15分）：入藏年份(5) + 來源記錄(5) + 展覽或出版紀錄(5)

### 2. 研究價值（researchValue，0-100，其他博物館沒有這項指標）
- 完整出版記錄：30分
- 展覽歷史：20分
- 詳細來源記錄（provenance）：20分
- 學術評論（commentary）：15分
- 技術分析（technique）：15分

最終排序依 `品質分數×0.6 + 研究價值×0.4` 綜合排序。

## 五、去重與輸出

- 去重依據：`harvardId` 優先，否則用「標題+藝術家+日期」組合鍵；重複時保留品質分數較高者
- 輸出檔名：`harvard_art_museums_<timestamp>.json`
- 檔案內附 `crawlInfo`：總筆數、API 呼叫次數、平均品質分數、平均研究價值、分類/文化/時期分布統計

## 六、目前實測數據（2026-08-01）

| 指標 | 數值 |
|---|---|
| 收集筆數 | 96 筆 |
| 平均品質分數 | 65.83/100 |
| API 呼叫次數 | 未達每日 2500 限制 |
| 已知限制 | 部分分類/藝術家查詢當下可能回傳 0 筆（如本次 Ceramics、Metalwork、Picasso、Van Gogh 等），屬 Harvard API 當下查詢結果的自然波動 |
