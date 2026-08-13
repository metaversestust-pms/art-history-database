#!/usr/bin/env python3
"""
僅處理ChromaDB部分 - 將文藝復興和巴洛克資料導入ChromaDB
"""

import json
import logging
from pathlib import Path
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def process_chromadb():
    """處理ChromaDB"""
    logger.info("🚀 開始處理ChromaDB...")

    # 等待ChromaDB服務啟動
    logger.info("⏳ 等待ChromaDB服務啟動...")
    time.sleep(5)

    try:
        import chromadb
        from chromadb.config import Settings

        # 載入資料
        data_dir = Path("./renaissance_baroque_data")
        combined_file = data_dir / "combined_renaissance_baroque.json"

        logger.info(f"📁 載入資料: {combined_file}")
        with open(combined_file, 'r', encoding='utf-8') as f:
            artworks = json.load(f)

        logger.info(f"✅ 成功載入 {len(artworks)} 件作品")

        # 連接ChromaDB
        logger.info("🔌 連接到ChromaDB...")
        client = chromadb.HttpClient(
            host='localhost',
            port=8001,
            settings=Settings(anonymized_telemetry=False)
        )

        collection_name = "renaissance_baroque_art"

        # 刪除舊集合並創建新集合
        try:
            client.delete_collection(collection_name)
            logger.info(f"🗑️ 刪除舊集合: {collection_name}")
        except:
            pass

        collection = client.create_collection(
            name=collection_name,
            metadata={"description": "Renaissance and Baroque Art Collection"}
        )
        logger.info(f"✨ 創建新集合: {collection_name}")

        # 準備資料
        documents = []
        metadatas = []
        ids = []

        for artwork in artworks:
            artwork_id = str(artwork.get('id', ''))
            title = artwork.get('title', 'Untitled')
            description = artwork.get('description', '')
            medium = artwork.get('medium', '')
            culture = artwork.get('culture', '')
            classification = artwork.get('classification', '')
            dated = artwork.get('dated', '')

            # 判斷時期
            text = f"{title} {description} {culture}".lower()
            if any(kw in text for kw in ['renaissance', 'raphael', 'leonardo', 'michelangelo']):
                period = 'Renaissance'
            elif any(kw in text for kw in ['baroque', 'caravaggio', 'rembrandt', 'rubens']):
                period = 'Baroque'
            else:
                period = 'Unknown'

            # 提取藝術家
            artist_names = []
            if 'people' in artwork and artwork['people']:
                for person in artwork['people']:
                    if person.get('role') in ['Artist', 'Creator', 'Maker']:
                        artist_names.append(person.get('name', ''))

            artist_str = ', '.join(artist_names) if artist_names else 'Unknown'

            # 組合文本
            text_parts = [
                f"Title: {title}",
                f"Period: {period}",
                f"Artist: {artist_str}",
                f"Dated: {dated}" if dated else "",
                f"Medium: {medium}" if medium else "",
                f"Culture: {culture}" if culture else "",
                f"Classification: {classification}" if classification else "",
                f"Description: {description}" if description else ""
            ]

            text = " | ".join([part for part in text_parts if part])[:2000]

            documents.append(text)
            metadatas.append({
                'title': title[:200],
                'artist': artist_str[:200],
                'period': period,
                'dated': dated[:100],
                'medium': medium[:200],
                'culture': culture[:100],
                'classification': classification[:100],
                'source': 'Harvard Art Museums'
            })
            ids.append(f"renaissance_baroque_{artwork_id}")

        # 批量添加
        logger.info(f"📥 添加 {len(documents)} 個文檔到ChromaDB...")
        batch_size = 100
        successful = 0

        for i in range(0, len(documents), batch_size):
            batch_docs = documents[i:i+batch_size]
            batch_metas = metadatas[i:i+batch_size]
            batch_ids = ids[i:i+batch_size]

            try:
                collection.add(
                    documents=batch_docs,
                    metadatas=batch_metas,
                    ids=batch_ids
                )
                successful += len(batch_docs)
                logger.info(f"  ✓ 進度: {min(i+batch_size, len(documents))}/{len(documents)}")
            except Exception as e:
                logger.warning(f"  ✗ 批次 {i} 失敗: {str(e)[:100]}")

        count = collection.count()
        logger.info(f"\n🎉 ChromaDB處理完成！")
        logger.info(f"   集合名稱: {collection_name}")
        logger.info(f"   文檔數量: {count}")
        logger.info(f"   成功添加: {successful} 個文檔")

    except Exception as e:
        logger.error(f"❌ ChromaDB處理失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    process_chromadb()
