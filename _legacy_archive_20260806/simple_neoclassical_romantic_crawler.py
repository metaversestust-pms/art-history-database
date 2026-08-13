#!/usr/bin/env python3
"""
簡化的新古典主義和浪漫主義藝術史資料爬蟲
直接使用 Harvard API
"""

import requests
import json
import time
from pathlib import Path
from datetime import datetime

# Harvard API 配置
API_KEY = "cfe24845-aa4f-4c93-9d86-f6880440af5f"
BASE_URL = "https://api.harvardartmuseums.org"

# 新古典主義和浪漫主義藝術家
ARTISTS = [
    # 新古典主義
    "David", "Ingres", "Canova",
    # 浪漫主義
    "Goya", "Delacroix", "Géricault", "Turner", "Constable", "Friedrich", "Blake"
]

# 關鍵詞
KEYWORDS = ["Neoclassic", "Romantic", "18th century", "19th century"]

def fetch_objects(query, max_results=50):
    """從 Harvard API 獲取作品"""
    print(f"🔍 搜尋: {query}")

    all_objects = []
    page = 1
    per_page = 100

    while len(all_objects) < max_results:
        params = {
            'apikey': API_KEY,
            'q': query,
            'page': page,
            'size': min(per_page, max_results - len(all_objects)),
            'hasimage': 0  # 不限制必須有圖片
        }

        try:
            response = requests.get(f"{BASE_URL}/object", params=params)
            if response.status_code == 200:
                data = response.json()
                records = data.get('records', [])

                if not records:
                    break

                all_objects.extend(records)
                print(f"   ✅ 找到 {len(records)} 件作品，總計 {len(all_objects)}")

                # 檢查是否還有更多頁面
                info = data.get('info', {})
                if page >= info.get('pages', 1):
                    break

                page += 1
                time.sleep(0.5)  # 避免過快請求
            elif response.status_code == 429:
                print("   ⚠️  API 速率限制，等待 60 秒...")
                time.sleep(60)
                continue
            else:
                print(f"   ❌ API 錯誤: {response.status_code}")
                break

        except Exception as e:
            print(f"   ❌ 請求失敗: {e}")
            break

    return all_objects[:max_results]

def main():
    """主函數"""
    print("\n" + "="*70)
    print("🎨 新古典主義與浪漫主義藝術史資料爬蟲")
    print("="*70 + "\n")

    # 創建輸出目錄
    output_dir = Path("./comprehensive_art_data/neoclassical_romantic")
    output_dir.mkdir(parents=True, exist_ok=True)

    all_objects = []

    # 1. 按藝術家搜尋
    print("\n👨‍🎨 方法1: 按藝術家搜尋...")
    for artist in ARTISTS:
        objects = fetch_objects(f"person:{artist}", max_results=20)
        all_objects.extend(objects)
        time.sleep(1)

    # 2. 按關鍵詞搜尋
    print("\n🔍 方法2: 按關鍵詞搜尋...")
    for keyword in KEYWORDS:
        objects = fetch_objects(keyword, max_results=30)
        all_objects.extend(objects)
        time.sleep(1)

    # 3. 按時期搜尋
    print("\n📅 方法3: 按時期搜尋...")
    # 搜索 1750-1850 年間的作品
    for decade in range(1750, 1851, 50):
        query = f"datebegin:{decade}"
        objects = fetch_objects(query, max_results=20)
        all_objects.extend(objects)
        time.sleep(1)

    # 去重
    unique_objects = {}
    for obj in all_objects:
        obj_id = obj.get('id') or obj.get('objectid')
        if obj_id and obj_id not in unique_objects:
            unique_objects[obj_id] = obj

    final_objects = list(unique_objects.values())

    # 保存結果
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = output_dir / f"neoclassical_romantic_{timestamp}.json"

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(final_objects, f, ensure_ascii=False, indent=2)

    # 統計報告
    print("\n" + "="*70)
    print("📊 爬取結果統計")
    print("="*70)
    print(f"總計收集: {len(final_objects)} 件作品（去重後）")
    print(f"原始收集: {len(all_objects)} 件作品")
    print(f"輸出檔案: {output_file}")

    # 統計分類
    classifications = {}
    cultures = {}
    periods = {}

    for obj in final_objects:
        # 分類統計
        if 'classification' in obj:
            classification = obj['classification']
            classifications[classification] = classifications.get(classification, 0) + 1

        # 文化統計
        if 'culture' in obj:
            culture = obj['culture']
            cultures[culture] = cultures.get(culture, 0) + 1

        # 時期統計
        if 'period' in obj:
            period = obj['period']
            periods[period] = periods.get(period, 0) + 1

    if classifications:
        print("\n📈 作品分類 (Top 5):")
        sorted_class = sorted(classifications.items(), key=lambda x: x[1], reverse=True)
        for i, (classification, count) in enumerate(sorted_class[:5], 1):
            print(f"   {i}. {classification}: {count} 件")

    if cultures:
        print("\n🌍 文化分布 (Top 5):")
        sorted_cultures = sorted(cultures.items(), key=lambda x: x[1], reverse=True)
        for i, (culture, count) in enumerate(sorted_cultures[:5], 1):
            print(f"   {i}. {culture}: {count} 件")

    if periods:
        print("\n📅 時期分布 (Top 5):")
        sorted_periods = sorted(periods.items(), key=lambda x: x[1], reverse=True)
        for i, (period, count) in enumerate(sorted_periods[:5], 1):
            print(f"   {i}. {period}: {count} 件")

    print("\n✅ 爬取完成!")
    print("="*70 + "\n")

    return output_file, len(final_objects)

if __name__ == "__main__":
    output_file, count = main()
    print(f"\n💾 資料已儲存到: {output_file}")
    print(f"📦 共收集 {count} 件藝術品資料")
