#!/bin/bash
# 簡化的Neo4j資料匯入腳本
# 直接使用Docker容器和cypher-shell

echo "🚀 開始匯入綜合藝術史資料到Neo4j"
echo "===================================================="

DATA_DIR="comprehensive_art_data"
IMPORTED=0

# 檢查資料目錄
if [ ! -d "$DATA_DIR" ]; then
    echo "❌ 找不到資料目錄: $DATA_DIR"
    exit 1
fi

# 處理每個時期的JSON檔案
for period_file in "$DATA_DIR"/*_artworks.json; do
    if [ -f "$period_file" ]; then
        period_name=$(basename "$period_file" _artworks.json)
        echo ""
        echo "📊 處理時期: $period_name"
        echo "===================================================="

        # 使用Python讀取JSON並生成Cypher命令
        docker exec art-history-neo4j cypher-shell -u neo4j -p arthistory123 << EOF
// 導入 $period_name 的作品
CALL apoc.load.json('file:///$period_file') YIELD value
UNWIND value AS artwork
WITH artwork
WHERE artwork.title IS NOT NULL

// 創建或更新Artwork節點
MERGE (a:Artwork {objectID: toString(coalesce(artwork.id, artwork.objectID))})
SET a.title = artwork.title,
    a.period = '$period_name',
    a.dated = coalesce(artwork.dated, artwork.objectDate, ''),
    a.culture = coalesce(artwork.culture, ''),
    a.medium = coalesce(artwork.medium, ''),
    a.dimensions = coalesce(artwork.dimensions, ''),
    a.classification = coalesce(artwork.classification, ''),
    a.department = coalesce(artwork.department, ''),
    a.image_url = coalesce(artwork.primaryimageurl, artwork.primaryImage, ''),
    a.updated_at = datetime()

// 處理藝術家
WITH a, artwork
WHERE artwork.people IS NOT NULL OR artwork.artistDisplayName IS NOT NULL
WITH a,
     CASE
         WHEN artwork.people IS NOT NULL THEN artwork.people[0].name
         WHEN artwork.artistDisplayName IS NOT NULL THEN artwork.artistDisplayName
         ELSE null
     END AS artist_name
WHERE artist_name IS NOT NULL
MERGE (artist:Artist {name: artist_name})
SET artist.period = '$period_name',
    artist.updated_at = datetime()
MERGE (artist)-[:CREATED]->(a)
RETURN count(*) as imported;
EOF

        echo "✅ $period_name 匯入完成"
    fi
done

echo ""
echo "===================================================="
echo "📊 匯入總結"
echo "===================================================="

# 顯示總計
docker exec art-history-neo4j cypher-shell -u neo4j -p arthistory123 << EOF
MATCH (n:Artwork)
RETURN count(n) as total_artworks;

MATCH (n:Artist)
RETURN count(n) as total_artists;
EOF

echo ""
echo "✅ 資料匯入完成！"
