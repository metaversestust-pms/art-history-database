#!/usr/bin/env python3
"""
文藝復興和巴洛克時期藝術史資料爬蟲
專門收集文藝復興（Renaissance）和巴洛克（Baroque）時期的藝術史資料
"""

import json
import logging
import time
import sys
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

class RenaissanceBaroqueCrawler:
    """文藝復興和巴洛克時期藝術史資料爬蟲"""

    def __init__(self, output_dir="./renaissance_baroque_data"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 配置Harvard爬蟲
        config = HarvardCrawlerConfig(
            api_key="cfe24845-aa4f-4c93-9d86-f6880440af5f",
            max_per_page=50,
            delay_seconds=0.5,
            output_dir=str(self.output_dir / "harvard_data")
        )

        self.harvard_crawler = HarvardArtMuseumsCrawler(config)

        # 文藝復興和巴洛克時期的關鍵詞
        self.renaissance_keywords = [
            "Renaissance", "Raphael", "Leonardo", "Michelangelo",
            "Titian", "Botticelli", "Donatello", "Brunelleschi",
            "Giotto", "Masaccio", "Fra Angelico", "Piero della Francesca",
            "Mantegna", "Bellini", "Perugino", "Ghirlandaio",
            "Filippo Lippi", "Andrea del Sarto", "Correggio"
        ]

        self.baroque_keywords = [
            "Baroque", "Caravaggio", "Rembrandt", "Rubens",
            "Velázquez", "Vermeer", "Bernini", "Artemisia Gentileschi",
            "Poussin", "Claude Lorrain", "Georges de La Tour",
            "Guido Reni", "Guercino", "Carracci", "Ribera",
            "Zurbarán", "Murillo", "Frans Hals"
        ]

        # 時期過濾
        self.renaissance_period = {
            'datebegin': '1300',
            'dateend': '1600'
        }

        self.baroque_period = {
            'datebegin': '1600',
            'dateend': '1750'
        }

    def crawl_by_period_and_keywords(self, period_name: str, keywords: list, date_filters: dict, max_pages: int = 10):
        """根據時期和關鍵詞爬取資料"""
        logger.info(f"\n{'='*60}")
        logger.info(f"開始爬取{period_name}時期資料")
        logger.info(f"{'='*60}")

        all_objects = []
        all_people = []

        # 1. 爬取特定時期的作品
        logger.info(f"\n🎨 爬取{period_name}時期作品（依日期過濾）...")
        try:
            # 使用日期過濾
            filters = {
                'century': self._get_century_filter(date_filters)
            }
            objects = self.harvard_crawler.crawl_all_objects(max_pages=max_pages, filters=filters)
            if objects:
                all_objects.extend(objects)
                logger.info(f"✅ 獲取 {len(objects)} 件{period_name}時期作品")
        except Exception as e:
            logger.warning(f"⚠️ 日期過濾爬取失敗: {e}")

        # 2. 爬取關鍵藝術家的作品
        logger.info(f"\n👨‍🎨 爬取{period_name}時期重要藝術家作品...")
        for artist in keywords[:10]:  # 限制藝術家數量以節省API調用
            try:
                logger.info(f"   搜索藝術家: {artist}")
                filters = {'person': artist}
                artist_objects = self.harvard_crawler.crawl_all_objects(max_pages=2, filters=filters)
                if artist_objects:
                    all_objects.extend(artist_objects)
                    logger.info(f"   ✅ 找到 {len(artist_objects)} 件作品")
                time.sleep(1)  # 避免API限制
            except Exception as e:
                logger.warning(f"   ⚠️ 藝術家 {artist} 搜索失敗: {e}")
                continue

        # 3. 搜索關鍵詞
        logger.info(f"\n🔍 搜索{period_name}時期關鍵詞...")
        for keyword in [period_name, f"{period_name} art"]:
            try:
                logger.info(f"   搜索關鍵詞: {keyword}")
                filters = {'keyword': keyword}
                keyword_objects = self.harvard_crawler.crawl_all_objects(max_pages=3, filters=filters)
                if keyword_objects:
                    all_objects.extend(keyword_objects)
                    logger.info(f"   ✅ 找到 {len(keyword_objects)} 件作品")
                time.sleep(1)
            except Exception as e:
                logger.warning(f"   ⚠️ 關鍵詞 {keyword} 搜索失敗: {e}")
                continue

        # 去除重複作品（根據ID）
        unique_objects = self._remove_duplicates(all_objects)
        logger.info(f"\n✅ {period_name}時期共獲取 {len(unique_objects)} 件獨特作品")

        # 保存數據
        self._save_period_data(period_name, unique_objects)

        return unique_objects

    def _get_century_filter(self, date_filters: dict) -> str:
        """生成世紀過濾條件"""
        # Harvard API使用世紀作為過濾條件
        # 文藝復興：14-16世紀
        # 巴洛克：17-18世紀
        start = int(date_filters['datebegin']) // 100
        end = int(date_filters['dateend']) // 100
        return f"{start}|{end}"

    def _remove_duplicates(self, objects: list) -> list:
        """根據ID去除重複作品"""
        seen_ids = set()
        unique_objects = []
        for obj in objects:
            obj_id = obj.get('id')
            if obj_id and obj_id not in seen_ids:
                seen_ids.add(obj_id)
                unique_objects.append(obj)
        return unique_objects

    def _save_period_data(self, period_name: str, objects: list):
        """保存時期數據"""
        filename = f"{period_name.lower()}_artworks.json"
        filepath = self.output_dir / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(objects, f, ensure_ascii=False, indent=2)

        logger.info(f"💾 {period_name}時期數據已保存到: {filepath}")

        # 保存摘要
        summary = {
            'period': period_name,
            'total_artworks': len(objects),
            'timestamp': datetime.now().isoformat(),
            'sample_titles': [obj.get('title', 'Untitled')[:100] for obj in objects[:10]]
        }

        summary_file = self.output_dir / f"{period_name.lower()}_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

    def crawl_all_periods(self, max_pages_per_period: int = 10):
        """爬取所有時期的資料"""
        logger.info("🚀 開始爬取文藝復興和巴洛克時期藝術史資料")
        logger.info("="*60)

        start_time = datetime.now()
        results = {}

        # 1. 爬取文藝復興時期
        renaissance_objects = self.crawl_by_period_and_keywords(
            "Renaissance",
            self.renaissance_keywords,
            self.renaissance_period,
            max_pages=max_pages_per_period
        )
        results['renaissance'] = {
            'count': len(renaissance_objects),
            'objects': renaissance_objects
        }

        # 2. 爬取巴洛克時期
        baroque_objects = self.crawl_by_period_and_keywords(
            "Baroque",
            self.baroque_keywords,
            self.baroque_period,
            max_pages=max_pages_per_period
        )
        results['baroque'] = {
            'count': len(baroque_objects),
            'objects': baroque_objects
        }

        # 3. 合併所有資料
        all_objects = renaissance_objects + baroque_objects
        unique_all = self._remove_duplicates(all_objects)

        logger.info(f"\n{'='*60}")
        logger.info("📊 爬取總結")
        logger.info(f"{'='*60}")
        logger.info(f"文藝復興時期: {len(renaissance_objects)} 件作品")
        logger.info(f"巴洛克時期: {len(baroque_objects)} 件作品")
        logger.info(f"總計（去重）: {len(unique_all)} 件作品")
        logger.info(f"API調用次數: {self.harvard_crawler.api_calls_count}")

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        logger.info(f"總耗時: {duration:.2f} 秒")

        # 保存合併數據
        combined_file = self.output_dir / "combined_renaissance_baroque.json"
        with open(combined_file, 'w', encoding='utf-8') as f:
            json.dump(unique_all, f, ensure_ascii=False, indent=2)

        logger.info(f"\n💾 合併數據已保存到: {combined_file}")

        # 保存最終摘要
        final_summary = {
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'duration_seconds': duration,
            'api_calls': self.harvard_crawler.api_calls_count,
            'results': {
                'renaissance_count': len(renaissance_objects),
                'baroque_count': len(baroque_objects),
                'total_unique': len(unique_all)
            }
        }

        summary_file = self.output_dir / "crawl_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(final_summary, f, ensure_ascii=False, indent=2)

        return results

def main():
    """主函數"""
    print("\n🎨 文藝復興和巴洛克時期藝術史資料爬蟲")
    print("="*60)
    print("此爬蟲將收集以下時期的藝術史資料：")
    print("  📖 文藝復興時期（Renaissance, 1300-1600）")
    print("  📖 巴洛克時期（Baroque, 1600-1750）")
    print("="*60)

    # 詢問配置
    output_dir = input("\n輸出目錄（按Enter使用默認: ./renaissance_baroque_data）: ").strip()
    if not output_dir:
        output_dir = "./renaissance_baroque_data"

    max_pages = input("每個時期最大爬取頁數（建議5-10，按Enter使用默認: 8）: ").strip()
    if not max_pages:
        max_pages = 8
    else:
        max_pages = int(max_pages)

    confirm = input(f"\n確認開始爬取？(y/n): ").strip().lower()
    if confirm != 'y':
        print("❌ 已取消")
        return

    # 創建爬蟲並執行
    crawler = RenaissanceBaroqueCrawler(output_dir=output_dir)
    results = crawler.crawl_all_periods(max_pages_per_period=max_pages)

    print("\n"+"="*60)
    print("✅ 文藝復興和巴洛克時期資料爬取完成！")
    print("="*60)
    print(f"📁 所有數據已保存到: {output_dir}/")
    print("\n💡 下一步：")
    print("  1. 運行完整的資料處理流程（包含Neo4j和ChromaDB）")
    print("  2. 使用以下命令：")
    print(f"     python3 complete_data_pipeline.py")

if __name__ == "__main__":
    main()
