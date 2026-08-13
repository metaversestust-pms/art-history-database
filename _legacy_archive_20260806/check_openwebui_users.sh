#!/bin/bash

# 檢查 OpenWebUI 使用者資訊

echo "=========================================="
echo "OpenWebUI 使用者資訊查詢"
echo "=========================================="
echo ""

if ! docker ps | grep -q art-history-openwebui; then
    echo "❌ OpenWebUI 容器未運行"
    echo "請先啟動容器: docker-compose -f docker-compose.openwebui.yml up -d"
    exit 1
fi

echo "正在查詢使用者資訊..."
echo ""

# 檢查 SQLite 是否可用
if ! docker exec art-history-openwebui which sqlite3 &>/dev/null; then
    echo "安裝 SQLite 客戶端..."
    docker exec art-history-openwebui apk add --no-cache sqlite &>/dev/null
fi

# 查詢使用者
echo "=========================================="
echo "使用者列表:"
echo "=========================================="
docker exec art-history-openwebui sqlite3 /app/backend/data/webui.db <<EOF
.headers on
.mode column
SELECT
    id,
    name,
    email,
    role,
    created_at
FROM user
ORDER BY created_at;
EOF

echo ""
echo "=========================================="
echo "統計資訊:"
echo "=========================================="
docker exec art-history-openwebui sqlite3 /app/backend/data/webui.db <<EOF
SELECT 'Total Users: ' || COUNT(*) FROM user;
SELECT 'Admins: ' || COUNT(*) FROM user WHERE role='admin';
SELECT 'Regular Users: ' || COUNT(*) FROM user WHERE role='user';
SELECT 'Pending Users: ' || COUNT(*) FROM user WHERE role='pending';
EOF

echo ""
