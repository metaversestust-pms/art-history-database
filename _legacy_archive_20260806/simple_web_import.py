#!/usr/bin/env python3
"""
簡化版Web匯入介面 - 使用Python內建HTTP服務器
無需安裝Flask
"""

import http.server
import socketserver
import json
import os
import sys
import logging
import tempfile
import cgi
from pathlib import Path
from urllib.parse import parse_qs, urlparse
import mimetypes

# 添加src路徑
sys.path.insert(0, str(Path(__file__).parent / 'src'))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# HTML模板
HTML_PAGE = '''<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>藝術史資料匯入工具</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
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
        .upload-icon { font-size: 4em; margin-bottom: 20px; }
        .upload-text {
            font-size: 1.2em;
            color: #667eea;
            margin-bottom: 10px;
        }
        .upload-hint { color: #999; font-size: 0.9em; }
        #fileInput { display: none; }
        .file-info {
            margin-top: 20px;
            padding: 15px;
            background: #fff3cd;
            border-radius: 8px;
            display: none;
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
        .btn:hover { transform: translateY(-2px); }
        .btn:disabled { opacity: 0.5; cursor: not-allowed; }
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
        .note {
            margin-top: 30px;
            padding: 20px;
            background: #fff3cd;
            border-radius: 10px;
            font-size: 0.9em;
        }
        .note h3 { margin-bottom: 10px; color: #856404; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎨 藝術史資料匯入工具</h1>
        <p class="subtitle">簡化版 - 支援CLI命令列匯入</p>

        <div class="note">
            <h3>⚠️ Web介面需要額外依賴</h3>
            <p><strong>請使用CLI命令列介面:</strong></p>
            <pre style="background: #f5f5f5; padding: 10px; border-radius: 5px; margin-top: 10px;">
# 匯入單一檔案
python3 import_local_data.py -f 您的檔案.json

# 匯入整個目錄
python3 import_local_data.py -d ./資料夾/ --recursive

# 建立範例模板
python3 import_local_data.py --create-template
            </pre>

            <h3 style="margin-top: 20px;">📦 安裝完整Web介面(選擇性):</h3>
            <pre style="background: #f5f5f5; padding: 10px; border-radius: 5px; margin-top: 10px;">
# 方法1: 使用系統套件管理器
sudo apt install python3-flask

# 方法2: 建立虛擬環境
python3 -m venv venv
source venv/bin/activate
pip install flask werkzeug

# 然後執行
python3 web_import_server.py
            </pre>
        </div>

        <div class="note" style="margin-top: 20px; background: #d4edda; border: 1px solid #c3e6cb;">
            <h3 style="color: #155724;">💡 推薦使用CLI介面</h3>
            <p>CLI介面功能更完整,無需額外依賴,適合批次處理!</p>
            <p style="margin-top: 10px;"><strong>查看完整說明:</strong></p>
            <pre style="background: white; padding: 10px; border-radius: 5px; margin-top: 10px;">
python3 import_local_data.py --help
            </pre>
        </div>
    </div>
</body>
</html>
'''

class SimpleHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """簡單的HTTP請求處理器"""

    def do_GET(self):
        """處理GET請求"""
        if self.path == '/' or self.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode('utf-8'))
        else:
            self.send_error(404)

    def log_message(self, format, *args):
        """自定義日誌格式"""
        logger.info("%s - %s" % (self.address_string(), format % args))


def main():
    """啟動簡單HTTP服務器"""
    PORT = 5050

    print("\n" + "="*60)
    print("🎨 藝術史資料匯入 - 簡化版Web介面")
    print("="*60)
    print("\n⚠️  注意: 這是簡化版,僅提供說明頁面")
    print("\n💡 建議使用CLI命令列介面:")
    print("   python3 import_local_data.py -f 您的檔案.json")
    print("\n如需完整Web介面,請先安裝Flask:")
    print("   sudo apt install python3-flask")
    print("   然後執行: python3 web_import_server.py")
    print("\n" + "="*60)
    print(f"\n🌐 簡化版頁面: http://localhost:{PORT}")
    print("\n按 Ctrl+C 停止服務器")
    print("="*60 + "\n")

    Handler = SimpleHTTPRequestHandler

    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\n⚠️  服務器已停止")
            sys.exit(0)


if __name__ == '__main__':
    main()
