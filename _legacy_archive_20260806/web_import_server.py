#!/usr/bin/env python3
"""
Web介面資料匯入服務器
提供簡單的拖放上傳介面
"""

from flask import Flask, request, jsonify, render_template_string
from werkzeug.utils import secure_filename
import logging
import sys
from pathlib import Path
import tempfile
import os

# 添加src路徑
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from importer import UniversalDataImporter

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB

# HTML模板
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>藝術史資料匯入工具</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }

        .container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            padding: 40px;
        }

        h1 {
            color: #333;
            margin-bottom: 10px;
            font-size: 2em;
        }

        .subtitle {
            color: #666;
            margin-bottom: 30px;
            font-size: 0.9em;
        }

        .upload-area {
            border: 3px dashed #667eea;
            border-radius: 15px;
            padding: 60px 20px;
            text-align: center;
            background: #f8f9ff;
            cursor: pointer;
            transition: all 0.3s;
        }

        .upload-area:hover {
            background: #e8ecff;
            border-color: #764ba2;
        }

        .upload-area.dragging {
            background: #dde4ff;
            border-color: #5568d3;
        }

        .upload-icon {
            font-size: 4em;
            margin-bottom: 20px;
        }

        .upload-text {
            font-size: 1.2em;
            color: #667eea;
            margin-bottom: 10px;
        }

        .upload-hint {
            color: #999;
            font-size: 0.9em;
        }

        #fileInput {
            display: none;
        }

        .options {
            margin-top: 30px;
            padding: 20px;
            background: #f5f5f5;
            border-radius: 10px;
        }

        .option-group {
            margin-bottom: 15px;
        }

        .option-group label {
            display: flex;
            align-items: center;
            cursor: pointer;
            font-size: 0.95em;
            color: #555;
        }

        .option-group input[type="checkbox"] {
            margin-right: 10px;
            width: 18px;
            height: 18px;
            cursor: pointer;
        }

        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 15px 40px;
            border-radius: 25px;
            font-size: 1.1em;
            cursor: pointer;
            margin-top: 20px;
            width: 100%;
            transition: transform 0.2s;
        }

        .btn:hover {
            transform: translateY(-2px);
        }

        .btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }

        .result {
            margin-top: 30px;
            padding: 20px;
            border-radius: 10px;
            display: none;
        }

        .result.success {
            background: #d4edda;
            border: 1px solid #c3e6cb;
            color: #155724;
            display: block;
        }

        .result.error {
            background: #f8d7da;
            border: 1px solid #f5c6cb;
            color: #721c24;
            display: block;
        }

        .loader {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 20px auto;
            display: none;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        .file-info {
            margin-top: 20px;
            padding: 15px;
            background: #fff3cd;
            border-radius: 8px;
            display: none;
        }

        .supported-formats {
            margin-top: 30px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 10px;
        }

        .supported-formats h3 {
            color: #333;
            margin-bottom: 10px;
            font-size: 1.1em;
        }

        .format-badge {
            display: inline-block;
            background: #667eea;
            color: white;
            padding: 5px 15px;
            border-radius: 15px;
            margin: 5px;
            font-size: 0.85em;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎨 藝術史資料匯入工具</h1>
        <p class="subtitle">支援PDF、JSON、TXT等多種格式</p>

        <div class="upload-area" id="uploadArea">
            <div class="upload-icon">📁</div>
            <div class="upload-text">拖放檔案到這裡</div>
            <div class="upload-hint">或點擊選擇檔案</div>
        </div>

        <input type="file" id="fileInput" accept=".pdf,.json,.jsonl,.txt,.md,.markdown" multiple>

        <div class="file-info" id="fileInfo"></div>

        <div class="options">
            <h3 style="margin-bottom: 15px; color: #333;">匯入選項</h3>
            <div class="option-group">
                <label>
                    <input type="checkbox" id="saveToNeo4j" checked>
                    儲存到 Neo4j 圖資料庫
                </label>
            </div>
            <div class="option-group">
                <label>
                    <input type="checkbox" id="saveToChromaDB" checked>
                    儲存到 ChromaDB 向量資料庫
                </label>
            </div>
        </div>

        <button class="btn" id="uploadBtn" disabled>開始匯入</button>

        <div class="loader" id="loader"></div>
        <div class="result" id="result"></div>

        <div class="supported-formats">
            <h3>✅ 支援的格式</h3>
            <span class="format-badge">.PDF</span>
            <span class="format-badge">.JSON</span>
            <span class="format-badge">.JSONL</span>
            <span class="format-badge">.TXT</span>
            <span class="format-badge">.MD</span>
            <span class="format-badge">.MARKDOWN</span>
        </div>
    </div>

    <script>
        const uploadArea = document.getElementById('uploadArea');
        const fileInput = document.getElementById('fileInput');
        const uploadBtn = document.getElementById('uploadBtn');
        const loader = document.getElementById('loader');
        const result = document.getElementById('result');
        const fileInfo = document.getElementById('fileInfo');
        let selectedFiles = null;

        // 點擊上傳區域
        uploadArea.addEventListener('click', () => fileInput.click());

        // 檔案選擇
        fileInput.addEventListener('change', (e) => {
            handleFiles(e.target.files);
        });

        // 拖放功能
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragging');
        });

        uploadArea.addEventListener('dragleave', () => {
            uploadArea.classList.remove('dragging');
        });

        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragging');
            handleFiles(e.dataTransfer.files);
        });

        function handleFiles(files) {
            if (files.length === 0) return;

            selectedFiles = files;
            uploadBtn.disabled = false;

            // 顯示檔案資訊
            const fileNames = Array.from(files).map(f => f.name).join(', ');
            fileInfo.textContent = `已選擇 ${files.length} 個檔案: ${fileNames}`;
            fileInfo.style.display = 'block';
        }

        // 上傳按鈕
        uploadBtn.addEventListener('click', async () => {
            if (!selectedFiles) return;

            const formData = new FormData();
            Array.from(selectedFiles).forEach(file => {
                formData.append('files', file);
            });

            formData.append('save_to_neo4j', document.getElementById('saveToNeo4j').checked);
            formData.append('save_to_chromadb', document.getElementById('saveToChromaDB').checked);

            // 顯示載入中
            loader.style.display = 'block';
            result.style.display = 'none';
            uploadBtn.disabled = true;

            try {
                const response = await fetch('/upload', {
                    method: 'POST',
                    body: formData
                });

                const data = await response.json();

                loader.style.display = 'none';
                uploadBtn.disabled = false;

                if (data.success) {
                    result.className = 'result success';
                    result.innerHTML = `
                        <h3>✅ 匯入成功!</h3>
                        <p>總計處理: ${data.stats.total_artworks} 件作品</p>
                        <p>儲存到Neo4j: ${data.stats.imported_to_neo4j} 件</p>
                        <p>儲存到ChromaDB: ${data.stats.imported_to_chromadb} 件</p>
                        <p style="margin-top: 15px; font-size: 0.9em;">
                            💡 資料已匯入，可以在OpenWebUI中立即使用!
                        </p>
                    `;
                } else {
                    result.className = 'result error';
                    result.innerHTML = `
                        <h3>❌ 匯入失敗</h3>
                        <p>${data.error}</p>
                    `;
                }
            } catch (error) {
                loader.style.display = 'none';
                uploadBtn.disabled = false;
                result.className = 'result error';
                result.innerHTML = `
                    <h3>❌ 網路錯誤</h3>
                    <p>${error.message}</p>
                `;
            }
        });
    </script>
</body>
</html>
'''


@app.route('/')
def index():
    """首頁"""
    return render_template_string(HTML_TEMPLATE)


@app.route('/upload', methods=['POST'])
def upload():
    """處理上傳"""
    try:
        # 獲取檔案
        files = request.files.getlist('files')
        if not files:
            return jsonify({'success': False, 'error': '沒有檔案'})

        # 獲取選項
        save_to_neo4j = request.form.get('save_to_neo4j', 'false') == 'true'
        save_to_chromadb = request.form.get('save_to_chromadb', 'false') == 'true'

        logger.info(f"收到 {len(files)} 個檔案")
        logger.info(f"Neo4j: {save_to_neo4j}, ChromaDB: {save_to_chromadb}")

        # 建立匯入器
        importer = UniversalDataImporter()

        # 處理每個檔案
        all_artworks = []
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            for file in files:
                if file.filename == '':
                    continue

                # 儲存臨時檔案
                filename = secure_filename(file.filename)
                filepath = tmpdir_path / filename
                file.save(str(filepath))

                # 匯入
                artworks = importer.import_file(
                    filepath,
                    save_to_neo4j=save_to_neo4j,
                    save_to_chromadb=save_to_chromadb
                )
                all_artworks.extend(artworks)

        # 返回結果
        return jsonify({
            'success': True,
            'message': '匯入成功',
            'stats': importer.stats,
            'artworks_count': len(all_artworks)
        })

    except Exception as e:
        logger.error(f"上傳失敗: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def main():
    """啟動服務器"""
    print("\n" + "="*60)
    print("🎨 藝術史資料匯入 Web 服務器")
    print("="*60)
    print("\n🌐 服務器啟動中...")
    print(f"📍 URL: http://localhost:5050")
    print("\n💡 使用方法:")
    print("   1. 在瀏覽器打開上述網址")
    print("   2. 拖放或選擇檔案")
    print("   3. 點擊「開始匯入」")
    print("\n按 Ctrl+C 停止服務器")
    print("="*60 + "\n")

    app.run(host='0.0.0.0', port=5050, debug=False)


if __name__ == '__main__':
    main()
