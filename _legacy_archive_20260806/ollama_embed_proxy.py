#!/usr/bin/env python3
"""
Ollama Embedding API 代理
修復 OpenWebUI 使用錯誤的 /api/embed 端點問題

這個代理服務器會:
1. 監聽 /api/embed 請求
2. 將請求轉發到正確的 /api/embeddings 端點
3. 返回結果給 OpenWebUI
"""

from flask import Flask, request, jsonify
import requests
import logging

# 配置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Ollama API 配置
OLLAMA_HOST = "http://localhost:11434"

@app.route('/health', methods=['GET'])
def health():
    """健康檢查端點"""
    return jsonify({"status": "healthy"}), 200

@app.route('/api/embed', methods=['POST'])
def embed_proxy():
    """
    代理 /api/embed 請求到 /api/embeddings
    """
    try:
        # 獲取請求數據
        data = request.get_json()
        logger.info(f"Received embed request: {data}")

        # 轉換請求格式
        # OpenWebUI 發送: {"model": "nomic-embed-text", "input": "text"}
        # Ollama 期望: {"model": "nomic-embed-text", "prompt": "text"}

        model = data.get('model', 'nomic-embed-text')
        input_text = data.get('input') or data.get('prompt')

        if not input_text:
            return jsonify({"error": "No input text provided"}), 400

        # 構建 Ollama API 請求
        ollama_request = {
            "model": model,
            "prompt": input_text
        }

        # 調用正確的 Ollama embeddings 端點
        response = requests.post(
            f"{OLLAMA_HOST}/api/embeddings",
            json=ollama_request,
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            # 返回嵌入向量
            logger.info(f"Successfully generated embedding (dimension: {len(result.get('embedding', []))})")
            return jsonify(result), 200
        else:
            logger.error(f"Ollama API error: {response.status_code} - {response.text}")
            return jsonify({"error": "Failed to generate embedding"}), response.status_code

    except Exception as e:
        logger.error(f"Error in embed_proxy: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/api/embeddings', methods=['POST'])
def embeddings():
    """
    直接轉發到 Ollama 的 /api/embeddings
    """
    try:
        data = request.get_json()
        logger.info(f"Received embeddings request: {data}")

        response = requests.post(
            f"{OLLAMA_HOST}/api/embeddings",
            json=data,
            timeout=30
        )

        return response.content, response.status_code, response.headers.items()

    except Exception as e:
        logger.error(f"Error in embeddings: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/api/tags', methods=['GET'])
def tags():
    """轉發 /api/tags 請求"""
    try:
        response = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=10)
        return response.content, response.status_code, response.headers.items()
    except Exception as e:
        logger.error(f"Error in tags: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    logger.info("Starting Ollama Embed API Proxy on port 11435")
    logger.info(f"Proxying requests to {OLLAMA_HOST}")
    app.run(host='0.0.0.0', port=11435, debug=False)
