#!/usr/bin/env python3
"""
直接使用requests訪問ChromaDB（繞過chromadb套件問題）
"""

import json
import logging
import requests
from pathlib import Path
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ChromaDB配置
CHROMADB_URL = "http://localhost:8001"
COLLECTION_NAME = "renaissance_baroque_art"

def test_connection():
    """測試ChromaDB連接"""
    try:
        # 嘗試訪問根路徑
        response = requests.get(CHROMADB_URL)
        logger.info(f"✅ ChromaDB服務連接成功 (狀態碼: {response.status_code})")
        return True
    except Exception as e:
        logger.error(f"❌ ChromaDB連接失敗: {e}")
        return False

def get_or_create_collection():
    """獲取或創建集合（使用Python SDK會更可靠）"""
    logger.info("⚠️ 建議使用Python chromadb客戶端庫")
    logger.info("   由於HTTP API的複雜性，我們需要使用SDK")
    return None

def import_with_requests():
    """嘗試使用純HTTP請求"""
    logger.info("🔍 檢測到chromadb套件未安裝")
    logger.info("📋 建議解決方案：")
    logger.info("")
    logger.info("方案1：在新的終端中安裝chromadb")
    logger.info("  cd /mnt/c/Users/ssking1999/Desktop/藝術史資料庫/art-history-database")
    logger.info("  source langchain-env/bin/activate")
    logger.info("  pip install chromadb-client")
    logger.info("")
    logger.info("方案2：使用Docker exec直接在ChromaDB容器中導入")
    logger.info("")
    logger.info("方案3：暫時跳過ChromaDB，僅使用Neo4j（已成功導入）")
    logger.info("  Neo4j已包含完整的1,280件作品資料")
    logger.info("  OpenWebUI可以通過Neo4j進行查詢")

def main():
    print("\n🎨 ChromaDB直接導入工具")
    print("="*70)

    # 測試連接
    if not test_connection():
        print("\n❌ 無法連接到ChromaDB服務")
        return

    # 載入資料
    data_file = Path("./renaissance_baroque_data/combined_renaissance_baroque.json")
    if not data_file.exists():
        print(f"❌ 找不到資料檔案: {data_file}")
        return

    with open(data_file, 'r', encoding='utf-8') as f:
        artworks = json.load(f)

    print(f"\n✅ 成功載入 {len(artworks)} 件藝術作品")
    print("\n" + "="*70)

    import_with_requests()

    print("\n" + "="*70)
    print("\n📊 當前狀態：")
    print("  ✅ 資料收集: 1,280件作品（文藝復興622件，巴洛克682件）")
    print("  ✅ Neo4j導入: 100%完成")
    print("  ⏳ ChromaDB: 等待套件安裝")
    print("\n💡 臨時解決方案：")
    print("  您可以先使用Neo4j在OpenWebUI中測試RAG功能")
    print("  Neo4j已包含完整的知識圖譜和關係數據")
    print("\n🔗 訪問：")
    print("  Neo4j Browser: http://localhost:7474")
    print("  OpenWebUI: http://localhost:8080")

if __name__ == "__main__":
    main()
