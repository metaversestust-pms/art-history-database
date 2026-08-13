#!/usr/bin/env python3
"""
在Docker容器中運行ChromaDB導入
"""

import json
from pathlib import Path

# 這個腳本將在Docker容器中運行
try:
    import chromadb
    from chromadb.config import Settings

    print("✅ ChromaDB模組已載入")

    # 連接到ChromaDB
    client = chromadb.HttpClient(
        host='art-history-chromadb',
        port=8000,
        settings=Settings(anonymized_telemetry=False)
    )

    collection_name = "renaissance_baroque_art"

    # 刪除舊集合
    try:
        client.delete_collection(collection_name)
        print(f"🗑️ 已刪除舊集合")
    except:
        pass

    # 創建新集合
    collection = client.create_collection(
        name=collection_name,
        metadata={"description": "Renaissance and Baroque Art"}
    )
    print(f"✨ 創建集合: {collection_name}")

    # 載入資料
    with open('/data/combined_renaissance_baroque.json', 'r', encoding='utf-8') as f:
        artworks = json.load(f)

    print(f"📁 載入 {len(artworks)} 件作品")

    # 準備資料
    documents = []
    metadatas = []
    ids = []

    for artwork in artworks:
        artwork_id = str(artwork.get('id', ''))
        title = artwork.get('title', 'Untitled')[:200]

        # 提取藝術家
        artist_names = []
        if 'people' in artwork and artwork['people']:
            for person in artwork['people']:
                if person.get('role') in ['Artist', 'Creator', 'Maker']:
                    artist_names.append(person.get('name', ''))

        artist_str = ', '.join(artist_names)[:200] if artist_names else 'Unknown'

        # 簡化文本
        text = f"Title: {title} | Artist: {artist_str}"

        documents.append(text)
        metadatas.append({
            'title': title,
            'artist': artist_str,
            'source': 'Harvard Art Museums'
        })
        ids.append(f"art_{artwork_id}")

    # 批量添加
    batch_size = 100
    for i in range(0, len(documents), batch_size):
        batch_docs = documents[i:i+batch_size]
        batch_metas = metadatas[i:i+batch_size]
        batch_ids = ids[i:i+batch_size]

        collection.add(
            documents=batch_docs,
            metadatas=batch_metas,
            ids=batch_ids
        )
        print(f"✓ 進度: {min(i+batch_size, len(documents))}/{len(documents)}")

    count = collection.count()
    print(f"\n🎉 完成！集合包含 {count} 個文檔")

except ImportError:
    print("❌ chromadb模組未安裝")
    print("請運行: pip install chromadb")
except Exception as e:
    print(f"❌ 錯誤: {e}")
    import traceback
    traceback.print_exc()
