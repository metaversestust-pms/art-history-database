#!/usr/bin/env python3
"""
綜合藝術史資料爬蟲系統
專注收集：文藝復興、中世紀、巴洛克與洛可可、新古典與浪漫主義時期
資料來源：Harvard Art Museums、Met Museum、Google Scholar
"""

import json
import logging
import time
import sys
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 添加langchain-rag目錄到路徑
langchain_rag_dir = Path(__file__).parent / "langchain-rag"
sys.path.insert(0, str(langchain_rag_dir))

from harvard_art_museums_crawler import HarvardArtMuseumsCrawler, HarvardCrawlerConfig

class ComprehensiveArtHistoryCrawler:
    """綜合藝術史資料爬蟲"""

    def __init__(self, output_dir="./comprehensive_art_data"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Harvard API配置
        self.harvard_api_key = "cfe24845-aa4f-4c93-9d86-f6880440af5f"

        # 定義藝術史時期
        self.art_periods = {
            "medieval": {
                "name": "中世紀藝術",
                "display_name": "Medieval Art",
                "date_range": (500, 1400),
                "keywords": [
                    "Medieval", "Byzantine", "Romanesque", "Gothic",
                    "Illuminated Manuscript", "Stained Glass", "Cathedral",
                    "中世紀", "拜占庭", "羅馬式", "哥德式"
                ],
                "artists": [
                    "Cimabue", "Duccio", "Simone Martini",
                    "Jan van Eyck", "Rogier van der Weyden"
                ],
                "priority": "high"
            },
            "renaissance": {
                "name": "文藝復興",
                "display_name": "Renaissance",
                "date_range": (1400, 1600),
                "keywords": [
                    "Renaissance", "Early Renaissance", "High Renaissance",
                    "Italian Renaissance", "Northern Renaissance",
                    "文藝復興", "意大利文藝復興", "北方文藝復興"
                ],
                "artists": [
                    "Leonardo da Vinci", "Michelangelo", "Raphael",
                    "Botticelli", "Titian", "Donatello", "Brunelleschi",
                    "Giotto", "Masaccio", "Piero della Francesca",
                    "Mantegna", "Bellini", "Perugino", "Ghirlandaio",
                    "Albrecht Dürer", "Hieronymus Bosch", "Pieter Bruegel"
                ],
                "priority": "very_high"
            },
            "baroque_rococo": {
                "name": "巴洛克與洛可可",
                "display_name": "Baroque and Rococo",
                "date_range": (1600, 1780),
                "keywords": [
                    "Baroque", "Rococo", "Caravaggism", "Dutch Golden Age",
                    "巴洛克", "洛可可", "荷蘭黃金時代"
                ],
                "artists": [
                    "Caravaggio", "Rembrandt", "Rubens", "Velázquez",
                    "Vermeer", "Bernini", "Artemisia Gentileschi",
                    "Poussin", "Claude Lorrain", "Georges de La Tour",
                    "Frans Hals", "Ribera", "Zurbarán", "Murillo",
                    "Watteau", "Boucher", "Fragonard", "Tiepolo"
                ],
                "priority": "very_high"
            },
            "neoclassical_romantic": {
                "name": "新古典與浪漫主義",
                "display_name": "Neoclassical and Romantic",
                "date_range": (1750, 1850),
                "keywords": [
                    "Neoclassicism", "Romanticism", "Sublime",
                    "新古典主義", "浪漫主義"
                ],
                "artists": [
                    "Jacques-Louis David", "Jean-Auguste-Dominique Ingres",
                    "Antonio Canova", "Francisco Goya", "Eugène Delacroix",
                    "Théodore Géricault", "J.M.W. Turner", "John Constable",
                    "Caspar David Friedrich", "William Blake"
                ],
                "priority": "high"
            }
        }

    def crawl_harvard_by_period(self, period_id: str, max_pages: int = 10) -> List[Dict]:
        """從Harvard Art Museums爬取特定時期的資料"""
        period = self.art_periods[period_id]
        logger.info(f"\n{'='*60}")
        logger.info(f"🎨 爬取時期: {period['name']} ({period['display_name']})")
        logger.info(f"📅 年代範圍: {period['date_range'][0]} - {period['date_range'][1]}")
        logger.info(f"{'='*60}")

        # 配置Harvard爬蟲
        config = HarvardCrawlerConfig(
            api_key=self.harvard_api_key,
            max_per_page=100,
            delay_seconds=0.5,
            output_dir=str(self.output_dir / f"harvard_{period_id}")
        )

        crawler = HarvardArtMuseumsCrawler(config)
        all_objects = []

        # 1. 依年代範圍爬取
        logger.info(f"\n📅 方法1: 依年代範圍爬取...")
        try:
            # Harvard API 使用世紀作為過濾
            start_century = period['date_range'][0] // 100
            end_century = period['date_range'][1] // 100

            for century in range(start_century, end_century + 1):
                logger.info(f"   爬取第 {century} 世紀作品...")
                filters = {'century': century}
                objects = crawler.crawl_all_objects(max_pages=2, filters=filters)
                if objects:
                    all_objects.extend(objects)
                    logger.info(f"   ✅ 找到 {len(objects)} 件作品")
                time.sleep(1)

        except Exception as e:
            logger.warning(f"⚠️ 年代範圍爬取失敗: {e}")

        # 2. 依關鍵詞爬取
        logger.info(f"\n🔍 方法2: 依關鍵詞爬取...")
        for keyword in period['keywords'][:5]:  # 限制關鍵詞數量
            try:
                logger.info(f"   搜索關鍵詞: {keyword}")
                filters = {'keyword': keyword}
                objects = crawler.crawl_all_objects(max_pages=2, filters=filters)
                if objects:
                    all_objects.extend(objects)
                    logger.info(f"   ✅ 找到 {len(objects)} 件作品")
                time.sleep(1)
            except Exception as e:
                logger.warning(f"   ⚠️ 關鍵詞 {keyword} 搜索失敗: {e}")
                continue

        # 3. 依藝術家爬取
        logger.info(f"\n👨‍🎨 方法3: 依重要藝術家爬取...")
        for artist in period['artists'][:15]:  # 限制藝術家數量
            try:
                logger.info(f"   搜索藝術家: {artist}")
                filters = {'person': artist}
                objects = crawler.crawl_all_objects(max_pages=2, filters=filters)
                if objects:
                    all_objects.extend(objects)
                    logger.info(f"   ✅ 找到 {len(objects)} 件作品")
                time.sleep(1)
            except Exception as e:
                logger.warning(f"   ⚠️ 藝術家 {artist} 搜索失敗: {e}")
                continue

        # 去除重複
        unique_objects = self._remove_duplicates(all_objects)
        logger.info(f"\n✅ {period['name']} 共獲取 {len(unique_objects)} 件獨特作品")

        # 保存資料
        self._save_period_data(period_id, period, unique_objects)

        return unique_objects

    def crawl_met_museum_by_period(self, period_id: str) -> List[Dict]:
        """從Met Museum爬取特定時期的資料（使用公開API）"""
        period = self.art_periods[period_id]
        logger.info(f"\n{'='*60}")
        logger.info(f"🏛️ Met Museum - {period['name']}")
        logger.info(f"{'='*60}")

        met_objects = []

        try:
            # Met Museum Collection API
            base_url = "https://collectionapi.metmuseum.org/public/collection/v1"

            # 對每個藝術家搜索
            for artist in period['artists'][:10]:  # 限制數量
                try:
                    logger.info(f"   搜索藝術家: {artist}")

                    # 搜索作品ID
                    search_url = f"{base_url}/search"
                    params = {
                        'q': artist,
                        'hasImages': 'true'
                    }

                    response = requests.get(search_url, params=params, timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        object_ids = data.get('objectIDs', [])[:20]  # 限制每位藝術家20件作品

                        # 獲取作品詳情
                        for obj_id in object_ids:
                            try:
                                obj_url = f"{base_url}/objects/{obj_id}"
                                obj_response = requests.get(obj_url, timeout=10)
                                if obj_response.status_code == 200:
                                    obj_data = obj_response.json()
                                    met_objects.append(obj_data)
                                    time.sleep(0.3)  # 避免過於頻繁
                            except:
                                continue

                        logger.info(f"   ✅ 從Met獲取 {len(object_ids)} 件作品ID")

                    time.sleep(1)

                except Exception as e:
                    logger.warning(f"   ⚠️ Met搜索失敗: {e}")
                    continue

        except Exception as e:
            logger.error(f"❌ Met Museum API錯誤: {e}")

        logger.info(f"\n✅ Met Museum 共獲取 {len(met_objects)} 件作品")

        # 保存Met資料
        if met_objects:
            met_file = self.output_dir / f"met_{period_id}_artworks.json"
            with open(met_file, 'w', encoding='utf-8') as f:
                json.dump(met_objects, f, ensure_ascii=False, indent=2)
            logger.info(f"💾 Met資料已保存: {met_file}")

        return met_objects

    def _remove_duplicates(self, objects: List[Dict]) -> List[Dict]:
        """去除重複作品"""
        seen_ids = set()
        unique_objects = []

        for obj in objects:
            obj_id = obj.get('id') or obj.get('objectID')
            if obj_id and obj_id not in seen_ids:
                seen_ids.add(obj_id)
                unique_objects.append(obj)

        return unique_objects

    def _save_period_data(self, period_id: str, period: Dict, objects: List[Dict]):
        """保存時期資料"""
        filename = f"{period_id}_artworks.json"
        filepath = self.output_dir / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(objects, f, ensure_ascii=False, indent=2)

        logger.info(f"💾 {period['name']} 資料已保存: {filepath}")

        # 保存摘要
        summary = {
            'period_id': period_id,
            'period_name': period['name'],
            'display_name': period['display_name'],
            'date_range': period['date_range'],
            'total_artworks': len(objects),
            'timestamp': datetime.now().isoformat(),
            'sample_titles': [
                obj.get('title', obj.get('objectName', 'Untitled'))[:100]
                for obj in objects[:10]
            ]
        }

        summary_file = self.output_dir / f"{period_id}_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

    def crawl_all_periods(self, include_met: bool = True):
        """爬取所有時期的資料"""
        logger.info("🚀 開始綜合藝術史資料爬取")
        logger.info("="*60)
        logger.info("目標時期:")
        for period_id, period in self.art_periods.items():
            priority_emoji = {
                'very_high': '⭐⭐⭐',
                'high': '⭐⭐',
                'medium': '⭐'
            }.get(period['priority'], '')
            logger.info(f"  {priority_emoji} {period['name']} ({period['date_range'][0]}-{period['date_range'][1]})")
        logger.info("="*60)

        start_time = datetime.now()
        results = {}

        # 按優先級排序時期
        sorted_periods = sorted(
            self.art_periods.items(),
            key=lambda x: {'very_high': 3, 'high': 2, 'medium': 1}.get(x[1]['priority'], 0),
            reverse=True
        )

        # 爬取每個時期
        for period_id, period in sorted_periods:
            logger.info(f"\n{'#'*60}")
            logger.info(f"# 開始處理: {period['name']}")
            logger.info(f"{'#'*60}")

            # Harvard Art Museums
            harvard_objects = self.crawl_harvard_by_period(period_id, max_pages=10)

            # Met Museum（可選）
            met_objects = []
            if include_met:
                met_objects = self.crawl_met_museum_by_period(period_id)

            results[period_id] = {
                'period_name': period['name'],
                'harvard_count': len(harvard_objects),
                'met_count': len(met_objects),
                'total_count': len(harvard_objects) + len(met_objects)
            }

        # 生成總結報告
        self._generate_final_report(results, start_time)

        return results

    def _generate_final_report(self, results: Dict, start_time: datetime):
        """生成最終報告"""
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        logger.info(f"\n{'='*60}")
        logger.info("📊 爬取總結報告")
        logger.info(f"{'='*60}")

        total_artworks = 0
        for period_id, data in results.items():
            period_name = data['period_name']
            harvard = data['harvard_count']
            met = data['met_count']
            total = data['total_count']
            total_artworks += total

            logger.info(f"\n{period_name}:")
            logger.info(f"  Harvard Art Museums: {harvard} 件")
            logger.info(f"  Met Museum: {met} 件")
            logger.info(f"  小計: {total} 件")

        logger.info(f"\n{'='*60}")
        logger.info(f"總計藝術品: {total_artworks} 件")
        logger.info(f"總耗時: {duration:.2f} 秒")
        logger.info(f"{'='*60}")

        # 保存最終報告
        final_report = {
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'duration_seconds': duration,
            'results': results,
            'total_artworks': total_artworks
        }

        report_file = self.output_dir / "crawl_final_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(final_report, f, ensure_ascii=False, indent=2)

        logger.info(f"\n💾 最終報告已保存: {report_file}")

        # 下一步提示
        logger.info(f"\n{'='*60}")
        logger.info("✅ 資料爬取完成！")
        logger.info(f"{'='*60}")
        logger.info("\n💡 下一步操作:")
        logger.info("1. 將資料匯入Neo4j和ChromaDB:")
        logger.info("   python3 import_comprehensive_data.py")
        logger.info("")
        logger.info("2. 在OpenWebUI測試新資料:")
        logger.info("   http://localhost:8080")
        logger.info("")
        logger.info("3. 測試問題示例:")
        logger.info("   - 文藝復興時期有哪些重要藝術家？")
        logger.info("   - 巴洛克藝術的特點是什麼？")
        logger.info("   - 中世紀哥德式建築的特色")
        logger.info("")


def main():
    """主函數"""
    print("\n🎨 綜合藝術史資料爬蟲系統")
    print("="*60)
    print("目標時期:")
    print("  ⭐⭐⭐ 文藝復興 (1400-1600)")
    print("  ⭐⭐⭐ 巴洛克與洛可可 (1600-1780)")
    print("  ⭐⭐  中世紀藝術 (500-1400)")
    print("  ⭐⭐  新古典與浪漫主義 (1750-1850)")
    print("="*60)

    # 詢問配置
    output_dir = input("\n輸出目錄（按Enter使用默認: ./comprehensive_art_data）: ").strip()
    if not output_dir:
        output_dir = "./comprehensive_art_data"

    include_met = input("\n是否包含Met Museum資料？(y/n，按Enter默認=y): ").strip().lower()
    include_met = include_met != 'n'

    confirm = input(f"\n確認開始爬取？(y/n): ").strip().lower()
    if confirm != 'y':
        print("❌ 已取消")
        return

    # 創建爬蟲並執行
    crawler = ComprehensiveArtHistoryCrawler(output_dir=output_dir)
    results = crawler.crawl_all_periods(include_met=include_met)

    print("\n✅ 爬取完成！")


if __name__ == "__main__":
    main()
