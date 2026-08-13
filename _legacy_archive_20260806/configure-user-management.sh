#!/bin/bash

# OpenWebUI 使用者管理配置腳本
# 版本: 1.0.0
# 日期: 2025-12-08

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置文件路徑
COMPOSE_FILE="docker-compose.openwebui.yml"
BACKUP_DIR="./backups"

# 函數：列印彩色訊息
print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# 函數：列印標題
print_header() {
    echo ""
    print_message "$BLUE" "=============================================="
    print_message "$BLUE" "$1"
    print_message "$BLUE" "=============================================="
    echo ""
}

# 函數：檢查 Docker 服務是否運行
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        print_message "$RED" "❌ Docker 未運行，請先啟動 Docker"
        exit 1
    fi
    print_message "$GREEN" "✅ Docker 運行中"
}

# 函數：備份當前配置
backup_config() {
    print_header "備份當前配置"

    mkdir -p "$BACKUP_DIR"

    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="$BACKUP_DIR/docker-compose.openwebui.yml.backup_$timestamp"

    if [ -f "$COMPOSE_FILE" ]; then
        cp "$COMPOSE_FILE" "$backup_file"
        print_message "$GREEN" "✅ 配置文件已備份至: $backup_file"
    fi

    # 備份資料庫
    if docker ps | grep -q art-history-openwebui; then
        local db_backup="$BACKUP_DIR/webui_backup_$timestamp.db"
        docker cp art-history-openwebui:/app/backend/data/webui.db "$db_backup" 2>/dev/null || true
        if [ -f "$db_backup" ]; then
            print_message "$GREEN" "✅ 資料庫已備份至: $db_backup"
        fi
    fi
}

# 函數：顯示當前配置
show_current_config() {
    print_header "當前認證配置"

    if docker ps | grep -q art-history-openwebui; then
        echo "正在檢查容器環境變數..."
        docker exec art-history-openwebui env 2>/dev/null | grep -E "(WEBUI_AUTH|ENABLE_SIGNUP|DEFAULT_USER_ROLE)" | while read line; do
            if [[ $line == *"WEBUI_AUTH=true"* ]]; then
                print_message "$GREEN" "✅ $line"
            elif [[ $line == *"WEBUI_AUTH=false"* ]]; then
                print_message "$RED" "❌ $line (認證已關閉)"
            else
                print_message "$YELLOW" "⚠️  $line"
            fi
        done
    else
        print_message "$YELLOW" "⚠️  OpenWebUI 容器未運行"
    fi
    echo ""
}

# 函數：顯示配置選單
show_menu() {
    print_header "選擇使用者管理策略"

    echo "請選擇適合你的配置方案："
    echo ""
    echo "1) 小型團隊模式 (推薦內部使用)"
    echo "   - 啟用認證"
    echo "   - 允許自行註冊"
    echo "   - 自動獲得 User 權限"
    echo ""
    echo "2) 審核模式 (推薦對外開放)"
    echo "   - 啟用認證"
    echo "   - 允許自行註冊"
    echo "   - 需管理員審核"
    echo ""
    echo "3) 企業模式 (最安全)"
    echo "   - 啟用認證"
    echo "   - 禁止自行註冊"
    echo "   - 僅管理員建立使用者"
    echo ""
    echo "4) 開發模式 (當前配置)"
    echo "   - 關閉認證"
    echo "   - 任何人可使用"
    echo ""
    echo "5) 查看當前配置"
    echo "6) 退出"
    echo ""
    read -p "請輸入選項 [1-6]: " choice
}

# 函數：更新配置
update_config() {
    local auth_enabled=$1
    local signup_enabled=$2
    local default_role=$3
    local mode_name=$4

    print_header "更新配置為 $mode_name"

    # 備份
    backup_config

    # 檢查配置文件是否存在
    if [ ! -f "$COMPOSE_FILE" ]; then
        print_message "$RED" "❌ 找不到配置文件: $COMPOSE_FILE"
        exit 1
    fi

    # 使用 sed 更新配置
    print_message "$YELLOW" "正在修改配置文件..."

    # 更新 WEBUI_AUTH
    sed -i "s/WEBUI_AUTH=.*/WEBUI_AUTH=$auth_enabled/" "$COMPOSE_FILE"

    # 更新 ENABLE_SIGNUP
    sed -i "s/ENABLE_SIGNUP=.*/ENABLE_SIGNUP=$signup_enabled/" "$COMPOSE_FILE"

    # 更新 DEFAULT_USER_ROLE
    sed -i "s/DEFAULT_USER_ROLE=.*/DEFAULT_USER_ROLE=$default_role/" "$COMPOSE_FILE"

    print_message "$GREEN" "✅ 配置文件已更新"

    # 顯示變更
    echo ""
    print_message "$BLUE" "新配置："
    grep -E "(WEBUI_AUTH|ENABLE_SIGNUP|DEFAULT_USER_ROLE)" "$COMPOSE_FILE" | sed 's/^[ \t]*//' | sed 's/^- //'
    echo ""
}

# 函數：重啟服務
restart_service() {
    print_header "重啟 OpenWebUI 服務"

    print_message "$YELLOW" "正在重啟服務..."

    if docker-compose -f "$COMPOSE_FILE" restart openwebui 2>/dev/null; then
        print_message "$GREEN" "✅ 服務重啟成功"
    else
        print_message "$YELLOW" "⚠️  使用 docker restart 重啟..."
        docker restart art-history-openwebui
    fi

    # 等待服務啟動
    print_message "$YELLOW" "等待服務啟動..."
    sleep 5

    # 檢查服務狀態
    if docker ps | grep -q art-history-openwebui; then
        print_message "$GREEN" "✅ OpenWebUI 服務運行中"

        # 顯示新配置
        echo ""
        print_message "$BLUE" "新的環境變數："
        docker exec art-history-openwebui env 2>/dev/null | grep -E "(WEBUI_AUTH|ENABLE_SIGNUP|DEFAULT_USER_ROLE)"
    else
        print_message "$RED" "❌ 服務啟動失敗，請檢查日誌"
        print_message "$YELLOW" "查看日誌: docker logs art-history-openwebui --tail 50"
    fi
}

# 函數：顯示後續步驟
show_next_steps() {
    local mode=$1

    print_header "配置完成 - 後續步驟"

    print_message "$GREEN" "✅ 使用者管理系統已配置為: $mode"
    echo ""

    case $mode in
        "小型團隊模式")
            echo "📝 下一步："
            echo "1. 訪問 http://localhost:8080"
            echo "2. 首次訪問時註冊管理員帳號"
            echo "3. 團隊成員可自行註冊並立即使用"
            echo ""
            print_message "$YELLOW" "⚠️  提醒：所有註冊使用者都會自動獲得 User 權限"
            ;;
        "審核模式")
            echo "📝 下一步："
            echo "1. 訪問 http://localhost:8080"
            echo "2. 首次訪問時註冊管理員帳號"
            echo "3. 新使用者註冊後狀態為 Pending"
            echo "4. 管理員需進入 Admin Panel → Users 審核新使用者"
            echo ""
            print_message "$YELLOW" "⚠️  提醒：記得定期檢查待審核使用者"
            ;;
        "企業模式")
            echo "📝 下一步："
            echo "1. 訪問 http://localhost:8080"
            echo "2. 首次訪問時註冊管理員帳號"
            echo "3. 其他使用者無法自行註冊"
            echo "4. 管理員需在 Admin Panel → Users → Add User 建立帳號"
            echo ""
            print_message "$GREEN" "✅ 這是最安全的配置，適合生產環境"
            ;;
    esac

    echo ""
    print_message "$BLUE" "📚 詳細文檔："
    echo "   ./OpenWebUI使用者管理指南.md"
    echo ""
    print_message "$BLUE" "🔍 查看日誌："
    echo "   docker logs art-history-openwebui --tail 50 -f"
    echo ""
}

# 主程式
main() {
    clear
    print_header "OpenWebUI 使用者管理配置工具"

    # 檢查 Docker
    check_docker

    # 顯示當前配置
    show_current_config

    # 顯示選單
    show_menu

    case $choice in
        1)
            update_config "true" "true" "user" "小型團隊模式"
            read -p "確定要重啟服務嗎？[y/N] " confirm
            if [[ $confirm == [yY] ]]; then
                restart_service
                show_next_steps "小型團隊模式"
            else
                print_message "$YELLOW" "配置已保存，請手動重啟服務"
            fi
            ;;
        2)
            update_config "true" "true" "pending" "審核模式"
            read -p "確定要重啟服務嗎？[y/N] " confirm
            if [[ $confirm == [yY] ]]; then
                restart_service
                show_next_steps "審核模式"
            else
                print_message "$YELLOW" "配置已保存，請手動重啟服務"
            fi
            ;;
        3)
            update_config "true" "false" "user" "企業模式"
            read -p "確定要重啟服務嗎？[y/N] " confirm
            if [[ $confirm == [yY] ]]; then
                restart_service
                show_next_steps "企業模式"
            else
                print_message "$YELLOW" "配置已保存，請手動重啟服務"
            fi
            ;;
        4)
            update_config "false" "true" "user" "開發模式"
            read -p "確定要重啟服務嗎？[y/N] " confirm
            if [[ $confirm == [yY] ]]; then
                restart_service
                print_message "$YELLOW" "⚠️  警告：認證已關閉，任何人都可以訪問系統"
            fi
            ;;
        5)
            show_current_config
            read -p "按 Enter 繼續..."
            main
            ;;
        6)
            print_message "$GREEN" "再見！"
            exit 0
            ;;
        *)
            print_message "$RED" "無效的選項"
            exit 1
            ;;
    esac
}

# 執行主程式
main
