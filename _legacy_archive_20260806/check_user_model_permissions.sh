#!/bin/bash

# 檢查 OpenWebUI 使用者的模型權限

echo "=========================================="
echo "OpenWebUI 使用者模型權限檢查"
echo "=========================================="
echo ""

# 檢查是否需要安裝 sqlite3
if ! docker exec art-history-openwebui which sqlite3 &>/dev/null; then
    echo "安裝 SQLite..."
    docker exec art-history-openwebui sh -c "apt-get update -qq && apt-get install -y sqlite3 -qq" &>/dev/null || {
        docker exec art-history-openwebui apk add --no-cache sqlite &>/dev/null || {
            echo "❌ 無法安裝 SQLite"
            exit 1
        }
    }
fi

echo "1. 查詢所有使用者:"
echo "=========================================="
docker exec art-history-openwebui sqlite3 /app/backend/data/webui.db <<EOF
.mode column
.headers on
SELECT id, email, name, role, created_at FROM user;
EOF
echo ""

echo "2. 檢查使用者表結構:"
echo "=========================================="
docker exec art-history-openwebui sqlite3 /app/backend/data/webui.db <<EOF
.schema user
EOF
echo ""

echo "3. 檢查是否有模型權限表:"
echo "=========================================="
docker exec art-history-openwebui sqlite3 /app/backend/data/webui.db <<EOF
SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%model%';
EOF
echo ""

echo "4. 檢查所有表:"
echo "=========================================="
docker exec art-history-openwebui sqlite3 /app/backend/data/webui.db <<EOF
.tables
EOF
echo ""

echo "5. 檢查 model 表 (如果存在):"
echo "=========================================="
docker exec art-history-openwebui sqlite3 /app/backend/data/webui.db <<EOF
SELECT * FROM model LIMIT 5;
EOF 2>/dev/null || echo "model 表不存在"
echo ""

echo "6. 檢查環境變數:"
echo "=========================================="
docker exec art-history-openwebui env | grep -E "(MODEL_FILTER|USER_PERMISSIONS)"
echo ""

echo "完成!"
