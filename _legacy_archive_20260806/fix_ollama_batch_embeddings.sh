#!/bin/bash

# OpenWebUI Ollama 批次嵌入修復腳本
# 修復 generate_ollama_batch_embeddings 函數使用錯誤的 API 參數

set -e

echo "========================================"
echo "修復 OpenWebUI Ollama 批次嵌入問題"
echo "========================================"
echo ""

CONTAINER_NAME="art-history-openwebui"
FILE_PATH="/app/backend/open_webui/retrieval/utils.py"
BACKUP_PATH="/app/backend/open_webui/retrieval/utils.py.backup_$(date +%Y%m%d_%H%M%S)"

echo "📋 問題診斷:"
echo "   - Ollama API 使用 'prompt' 參數（單個文本）"
echo "   - OpenWebUI 使用 'input' 參數（批次，OpenAI 格式）"
echo "   - 導致 Ollama 返回空嵌入: {'embedding': []}"
echo ""

# 1. 備份原始檔案
echo "1️⃣ 備份原始檔案..."
docker exec $CONTAINER_NAME cp $FILE_PATH $BACKUP_PATH
echo "   ✅ 備份至: $BACKUP_PATH"
echo ""

# 2. 建立修復檔案
echo "2️⃣ 建立修復版本..."

cat > /tmp/fix_ollama_batch.py << 'EOF'
def generate_ollama_batch_embeddings(
    model: str,
    texts: list[str],
    url: str,
    key: str = "",
    prefix: str = None,
    user: UserModel = None,
) -> Optional[list[list[float]]]:
    try:
        log.debug(
            f"generate_ollama_batch_embeddings:model {model} batch size: {len(texts)}"
        )

        # Ollama 不支援批次嵌入，需要逐一生成
        embeddings = []
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {key}",
            **(
                {
                    "X-OpenWebUI-User-Name": quote(user.name, safe=" "),
                    "X-OpenWebUI-User-Id": user.id,
                    "X-OpenWebUI-User-Email": user.email,
                    "X-OpenWebUI-User-Role": user.role,
                }
                if ENABLE_FORWARD_USER_INFO_HEADERS and user
                else {}
            ),
        }

        for text in texts:
            json_data = {"prompt": text, "model": model}
            if isinstance(RAG_EMBEDDING_PREFIX_FIELD_NAME, str) and isinstance(prefix, str):
                json_data[RAG_EMBEDDING_PREFIX_FIELD_NAME] = prefix

            r = requests.post(
                f"{url}/api/embeddings",
                headers=headers,
                json=json_data,
            )
            r.raise_for_status()
            data = r.json()

            if "embedding" in data:
                embeddings.append(data["embedding"])
            else:
                raise Exception(f"No embedding in response for text: {text[:50]}...")

        return embeddings
    except Exception as e:
        log.exception(f"Error generating ollama batch embeddings: {e}")
        return None
EOF

echo "   ✅ 修復版本已建立"
echo ""

# 3. 讀取當前函數
echo "3️⃣ 定位並修復函數..."

docker exec $CONTAINER_NAME bash -c "cat > /tmp/fix_script.py << 'PYEOF'
import re

# 讀取檔案
with open('/app/backend/open_webui/retrieval/utils.py', 'r') as f:
    content = f.read()

# 找到並替換函數
# 尋找 generate_ollama_batch_embeddings 函數的完整定義
pattern = r'def generate_ollama_batch_embeddings\([\s\S]*?\n(?=\ndef\s)'

replacement = '''def generate_ollama_batch_embeddings(
    model: str,
    texts: list[str],
    url: str,
    key: str = \"\",
    prefix: str = None,
    user: UserModel = None,
) -> Optional[list[list[float]]]:
    try:
        log.debug(
            f\"generate_ollama_batch_embeddings:model {model} batch size: {len(texts)}\"
        )

        # Ollama 不支援批次嵌入 (使用 input 參數)，需要逐一生成
        # 修復: 改用 prompt 參數，逐一調用 API
        embeddings = []
        headers = {
            \"Content-Type\": \"application/json\",
            \"Authorization\": f\"Bearer {key}\",
            **(
                {
                    \"X-OpenWebUI-User-Name\": quote(user.name, safe=\" \"),
                    \"X-OpenWebUI-User-Id\": user.id,
                    \"X-OpenWebUI-User-Email\": user.email,
                    \"X-OpenWebUI-User-Role\": user.role,
                }
                if ENABLE_FORWARD_USER_INFO_HEADERS and user
                else {}
            ),
        }

        for text in texts:
            json_data = {\"prompt\": text, \"model\": model}
            if isinstance(RAG_EMBEDDING_PREFIX_FIELD_NAME, str) and isinstance(prefix, str):
                json_data[RAG_EMBEDDING_PREFIX_FIELD_NAME] = prefix

            r = requests.post(
                f\"{url}/api/embeddings\",
                headers=headers,
                json=json_data,
            )
            r.raise_for_status()
            data = r.json()

            if \"embedding\" in data:
                embeddings.append(data[\"embedding\"])
            else:
                raise Exception(f\"No embedding in response for text: {text[:50]}...\")

        return embeddings
    except Exception as e:
        log.exception(f\"Error generating ollama batch embeddings: {e}\")
        return None

'''

# 替換
new_content = re.sub(pattern, replacement, content)

# 檢查是否成功替換
if new_content == content:
    print('❌ 未找到函數或替換失敗')
    exit(1)

# 寫回檔案
with open('/app/backend/open_webui/retrieval/utils.py', 'w') as f:
    f.write(new_content)

print('✅ 函數已成功替換')
PYEOF

python3 /tmp/fix_script.py
"

echo ""

# 4. 驗證修改
echo "4️⃣ 驗證修改..."
docker exec $CONTAINER_NAME grep -A 5 "# Ollama 不支援批次嵌入" $FILE_PATH > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "   ✅ 修改成功驗證"
else
    echo "   ⚠️  驗證失敗，請檢查"
fi
echo ""

# 5. 重啟 OpenWebUI
echo "5️⃣ 重啟 OpenWebUI 容器..."
docker restart $CONTAINER_NAME
echo "   等待容器啟動..."
sleep 10

# 檢查容器狀態
if docker ps | grep -q $CONTAINER_NAME; then
    echo "   ✅ 容器重啟成功"
else
    echo "   ❌ 容器重啟失敗"
    exit 1
fi
echo ""

echo "========================================"
echo "✅ 修復完成！"
echo "========================================"
echo ""
echo "📊 修復摘要:"
echo "   問題: 使用 'input' 參數導致 Ollama 返回空嵌入"
echo "   解決: 改用 'prompt' 參數，逐一生成嵌入"
echo "   備份: $BACKUP_PATH"
echo ""
echo "🧪 測試上傳:"
echo "   1. 訪問 http://localhost:8080"
echo "   2. 進入 Workspace → Knowledge"
echo "   3. 上傳測試檔案"
echo "   4. 檢查是否成功"
echo ""
echo "🔧 如需恢復:"
echo "   docker exec $CONTAINER_NAME cp $BACKUP_PATH $FILE_PATH"
echo "   docker restart $CONTAINER_NAME"
echo ""
