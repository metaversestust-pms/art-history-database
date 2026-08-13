#!/usr/bin/env python3
"""
自動執行新古典主義和浪漫主義時期藝術史資料爬蟲
"""

import sys
import logging
from pathlib import Path
from datetime import datetime

# 添加langchain-rag目錄到路徑
langchain_rag_dir = Path(__file__).parent / "langchain-rag"
sys.path.insert(0, str(langchain_rag_dir))

from harvard_art_museums_crawler import HarvardArtMuseumsCrawler, HarvardCrawlerConfig

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 新古典主義和浪漫主義藝術家
NEOCLASSICAL_ROMANTIC_ARTISTS = [
    # 新古典主義
    "Jacques-Louis David",
    "Jean-Auguste-Dominique Ingres",
    "Antonio Canova",
    "Jacques-Louis David",

    # 浪漫主義
    "Francisco Goya",
    "Eugène Delacroix",
    "Théodore Géricault",
    "J.M.W. Turner",
    "John Constable",
    "Caspar David Friedrich",
    "William Blake",
    "Gustave Courbet",
    "Jean-François Millet"
]

# 關鍵詞
KEYWORDS = [
    "Neoclassicism",
    "Romanticism",
    "Sublime",
    "新古典主義",
    "浪漫主義",
    "Neoclassical",
    "Romantic"
]

def main():
    """主函數"""
    print("\n" + "="*70)
    print("🎨 新古典主義與浪漫主義藝術史資料爬蟲")
    print("="*70)

    # 創建輸出目錄
    output_dir = Path("./comprehensive_art_data/neoclassical_romantic")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Harvard API配置
    harvard_api_key = "cfe24845-aa4f-4c93-9d86-f6880440af5f"

    config = HarvardCrawlerConfig(
        api_key=harvard_api_key,
        max_per_page=100,
        delay_seconds=0.5,
        output_dir=str(output_dir / "harvard")
    )

    crawler = HarvardArtMuseumsCrawler(config)
    all_objects = []

    # 1. 依世紀爬取 (18-19世紀)
    logger.info("\n📅 方法1: 依世紀爬取...")
    for century in [18, 19]:
        try:
            logger.info(f"   爬取第 {century} 世紀作品...")
            filters = {'century': century}
            objects = crawler.crawl_all_objects(max_pages=5, filters=filters)
            if objects:
                all_objects.extend(objects)
                logger.info(f"   ✅ 找到 {len(objects)} 件作品")
        except Exception as e:
            logger.warning(f"   ⚠️ 第 {century} 世紀爬取失敗: {e}")

    # 2. 依藝術家爬取
    logger.info("\n👨‍🎨 方法2: 依藝術家爬取...")
    for artist in NEOCLASSICAL_ROMANTIC_ARTISTS:
        try:
            logger.info(f"   搜尋藝術家: {artist}")
            objects = crawler.search_by_artist(artist, max_pages=3)
            if objects:
                all_objects.extend(objects)
                logger.info(f"   ✅ 找到 {len(objects)} 件作品")
        except Exception as e:
            logger.warning(f"   ⚠️ {artist} 爬取失敗: {e}")

    # 3. 依關鍵詞爬取
    logger.info("\n🔍 方法3: 依關鍵詞爬取...")
    for keyword in KEYWORDS:
        try:
            logger.info(f"   搜尋關鍵詞: {keyword}")
            objects = crawler.search_by_keyword(keyword, max_pages=2)
            if objects:
                all_objects.extend(objects)
                logger.info(f"   ✅ 找到 {len(objects)} 件作品")
        except Exception as e:
            logger.warning(f"   ⚠️ {keyword} 搜尋失敗: {e}")

    # 去重
    unique_objects = {}
    for obj in all_objects:
        obj_id = obj.get('id') or obj.get('objectid')
        if obj_id and obj_id not in unique_objects:
            unique_objects[obj_id] = obj

    final_objects = list(unique_objects.values())

    # 保存結果
    import json
    output_file = output_dir / f"neoclassical_romantic_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(final_objects, f, ensure_ascii=False, indent=2)

    # 統計報告
    print("\n" + "="*70)
    print("📊 爬取結果統計")
    print("="*70)
    print(f"總計收集: {len(final_objects)} 件作品（去重後）")
    print(f"原始收集: {len(all_objects)} 件作品")
    print(f"輸出檔案: {output_file}")

    # 按藝術家統計
    artist_stats = {}
    for obj in final_objects:
        people = obj.get('people', [])
        for person in people:
            name = person.get('name', 'Unknown')
            artist_stats[name] = artist_stats.get(name, 0) + 1

    if artist_stats:
        print("\n📈 藝術家作品數量 (Top 10):")
        sorted_artists = sorted(artist_stats.items(), key=lambda x: x[1], reverse=True)
        for i, (artist, count) in enumerate(sorted_artists[:10], 1):
            print(f"   {i}. {artist}: {count} 件")

    print("\n✅ 爬取完成!")
    print("="*70 + "\n")

    return output_file

if __name__ == "__main__":
    main()
