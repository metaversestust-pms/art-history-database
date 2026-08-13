#!/bin/bash

# 測試一般使用者的模型訪問權限

echo "=========================================="
echo "一般使用者模型訪問測試"
echo "=========================================="
echo ""

echo "步驟 1: 檢查數據庫中的模型"
echo "=========================================="
TOTAL_MODELS=$(docker exec art-history-openwebui sqlite3 /app/backend/data/webui.db "SELECT COUNT(*) FROM model;" 2>&1)
echo "數據庫中的模型總數: $TOTAL_MODELS"

echo ""
echo "檢查 access_control 狀態:"
docker exec art-history-openwebui sqlite3 /app/backend/data/webui.db "
SELECT
    CASE
        WHEN access_control = '{}' THEN 'Public'
        WHEN length(access_control) > 2 THEN 'Restricted'
        ELSE 'Unknown'
    END as status,
    COUNT(*) as count
FROM model
GROUP BY status;
"

echo ""
echo "步驟 2: 檢查 is_active 狀態"
echo "=========================================="
docker exec art-history-openwebui sqlite3 /app/backend/data/webui.db "
SELECT
    is_active,
    COUNT(*) as count
FROM model
GROUP BY is_active;
"

echo ""
echo "未啟用的模型:"
docker exec art-history-openwebui sqlite3 /app/backend/data/webui.db "
SELECT id FROM model WHERE is_active = 0;
"

echo ""
echo "步驟 3: 檢查使用者資訊"
echo "=========================================="
docker exec art-history-openwebui sqlite3 /app/backend/data/webui.db "
SELECT id, email, role FROM user;
"

echo ""
echo "步驟 4: 檢查 OpenWebUI 日誌"
echo "=========================================="
echo "最近的模型 API 調用:"
docker logs art-history-openwebui --tail 100 2>&1 | grep "api/models" | tail -10

echo ""
echo "步驟 5: 建議操作"
echo "=========================================="

# 檢查未啟用的模型
INACTIVE_COUNT=$(docker exec art-history-openwebui sqlite3 /app/backend/data/webui.db "SELECT COUNT(*) FROM model WHERE is_active = 0;" 2>&1)

if [ "$INACTIVE_COUNT" -gt "0" ]; then
    echo "⚠️  發現 $INACTIVE_COUNT 個未啟用的模型"
    echo ""
    echo "建議執行:"
    echo "  docker exec art-history-openwebui sqlite3 /app/backend/data/webui.db \"UPDATE model SET is_active = 1 WHERE is_active = 0;\""
    echo ""
fi

echo "一般使用者應該執行:"
echo "1. 完全登出 OpenWebUI"
echo "2. 關閉瀏覽器"
echo "3. 重新開啟瀏覽器"
echo "4. 清除快取 (Ctrl + Shift + Delete → All time)"
echo "5. 訪問 http://localhost:8080"
echo "6. 登入一般使用者帳號"
echo "7. 新對話 → 檢查模型選擇器"
echo ""

echo "如果還是沒有模型,請提供:"
echo "- 瀏覽器開發者工具的 Console 錯誤 (F12 → Console)"
echo "- Network 標籤中 /api/models 的回應 (F12 → Network → 篩選 models)"
echo ""
