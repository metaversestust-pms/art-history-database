#!/bin/bash
# 簡易Neo4j數據導入腳本
# 使用curl和Cypher查詢直接導入數據

echo "======================================"
echo "   藝術史數據導入到Neo4j"
echo "======================================"
echo ""

NEO4J_URL="http://localhost:7474"
NEO4J_USER="neo4j"
NEO4J_PASSWORD="arthistory123"
NEO4J_BOLT="bolt://localhost:7687"

# 數據目錄
DATA_DIR="./comprehensive_art_data"

echo "檢查Neo4j連接..."
curl -s "$NEO4J_URL" > /dev/null
if [ $? -ne 0 ]; then
    echo "❌ 無法連接到Neo4j ($NEO4J_URL)"
    echo "請確認Neo4j容器正在運行"
    exit 1
fi

echo "✅ Neo4j連接正常"
echo ""

# 統計數據文件
echo "掃描數據文件..."
file_count=$(ls -1 "$DATA_DIR"/*_artworks.json 2>/dev/null | wc -l)

if [ "$file_count" -eq 0 ]; then
    echo "❌ 在 $DATA_DIR 找不到數據文件"
    exit 1
fi

echo "找到 $file_count 個數據文件"
echo ""

# 計算總作品數
total_artworks=0
for file in "$DATA_DIR"/*_artworks.json; do
    count=$(cat "$file" | python3 -c "import json, sys; print(len(json.load(sys.stdin)))" 2>/dev/null)
    if [ -n "$count" ]; then
        total_artworks=$((total_artworks + count))
        filename=$(basename "$file")
        echo "  - $filename: $count 件作品"
    fi
done

echo ""
echo "總計: $total_artworks 件作品"
echo ""

read -p "確認開始導入？(y/n): " confirm
if [ "$confirm" != "y" ]; then
    echo "❌ 已取消"
    exit 0
fi

echo ""
echo "開始導入數據到Neo4j..."
echo "======================================"

# 使用Python腳本導入（需要先安裝套件）
if python3 -c "from neo4j import GraphDatabase" 2>/dev/null; then
    echo "使用Python neo4j驅動程序..."
    python3 import_neo4j_only.py <<EOF
$DATA_DIR
y
EOF
else
    echo "❌ 缺少neo4j Python套件"
    echo ""
    echo "請執行以下命令安裝:"
    echo "  pip3 install neo4j --break-system-packages"
    echo ""
    echo "或者創建虛擬環境:"
    echo "  python3 -m venv venv"
    echo "  source venv/bin/activate"
    echo "  pip install neo4j"
    echo "  python3 import_neo4j_only.py"
    exit 1
fi

echo ""
echo "✅ 數據導入完成！"
echo ""
echo "下一步:"
echo "  1. 訪問Neo4j Browser: http://localhost:7474"
echo "  2. 執行查詢: MATCH (n) RETURN labels(n) as Type, count(n) as Count"
