#!/usr/bin/env python3
"""
本地資料匯入工具 - CLI介面
支援PDF、JSON、TXT等多種格式
"""

import argparse
import logging
import sys
from pathlib import Path

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 添加src路徑
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from importer import UniversalDataImporter, JSONProcessor, TextProcessor


def main():
    parser = argparse.ArgumentParser(
        description='藝術史本地資料匯入工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
範例:
  # 匯入單一檔案
  python import_local_data.py -f my_artworks.json

  # 匯入整個目錄
  python import_local_data.py -d ./my_data/

  # 只儲存到Neo4j
  python import_local_data.py -f artwork.pdf --neo4j-only

  # 只儲存到ChromaDB
  python import_local_data.py -f artwork.pdf --chromadb-only

  # 建立範例模板
  python import_local_data.py --create-template

支援的格式:
  - PDF檔案 (.pdf)
  - JSON檔案 (.json, .jsonl)
  - 文字檔 (.txt, .md, .markdown)
        """
    )

    # 主要參數
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument('-f', '--file', type=str,
                      help='要匯入的檔案路徑')
    group.add_argument('-d', '--directory', type=str,
                      help='要匯入的目錄路徑')
    group.add_argument('--create-template', action='store_true',
                      help='建立範例模板檔案')

    # 選項
    parser.add_argument('--recursive', action='store_true',
                       help='遞迴處理子目錄 (配合 -d 使用)')

    parser.add_argument('--neo4j-only', action='store_true',
                       help='只儲存到Neo4j')
    parser.add_argument('--chromadb-only', action='store_true',
                       help='只儲存到ChromaDB')
    parser.add_argument('--no-save', action='store_true',
                       help='不儲存到資料庫，僅處理檔案')

    # 資料庫連接參數
    parser.add_argument('--neo4j-uri', type=str, default='bolt://localhost:7687',
                       help='Neo4j連接URI (預設: bolt://localhost:7687)')
    parser.add_argument('--neo4j-user', type=str, default='neo4j',
                       help='Neo4j使用者名稱 (預設: neo4j)')
    parser.add_argument('--neo4j-password', type=str, default='arthistory123',
                       help='Neo4j密碼 (預設: arthistory123)')
    parser.add_argument('--chromadb-host', type=str, default='localhost',
                       help='ChromaDB主機 (預設: localhost)')
    parser.add_argument('--chromadb-port', type=int, default=8001,
                       help='ChromaDB端口 (預設: 8001)')

    # 其他選項
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='顯示詳細資訊')

    args = parser.parse_args()

    # 設置日誌級別
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # 建立範例模板
    if args.create_template:
        create_templates()
        return

    # 檢查是否提供檔案或目錄
    if not args.file and not args.directory:
        parser.print_help()
        print("\n❌ 錯誤: 請指定要匯入的檔案 (-f) 或目錄 (-d)")
        print("或使用 --create-template 建立範例模板")
        sys.exit(1)

    # 建立匯入器
    importer = UniversalDataImporter(
        neo4j_uri=args.neo4j_uri,
        neo4j_user=args.neo4j_user,
        neo4j_password=args.neo4j_password,
        chromadb_host=args.chromadb_host,
        chromadb_port=args.chromadb_port
    )

    # 決定儲存位置
    if args.no_save:
        save_to_neo4j = False
        save_to_chromadb = False
    elif args.neo4j_only:
        save_to_neo4j = True
        save_to_chromadb = False
    elif args.chromadb_only:
        save_to_neo4j = False
        save_to_chromadb = True
    else:
        save_to_neo4j = True
        save_to_chromadb = True

    # 顯示配置
    print("\n" + "="*60)
    print("🎨 藝術史本地資料匯入工具")
    print("="*60)
    print(f"儲存到Neo4j:     {'✅ 是' if save_to_neo4j else '❌ 否'}")
    print(f"儲存到ChromaDB:  {'✅ 是' if save_to_chromadb else '❌ 否'}")
    print("="*60)

    # 執行匯入
    try:
        if args.file:
            # 匯入單一檔案
            file_path = Path(args.file)
            artworks = importer.import_file(
                file_path,
                save_to_neo4j=save_to_neo4j,
                save_to_chromadb=save_to_chromadb
            )

            if artworks:
                print(f"\n✅ 成功處理 {len(artworks)} 件作品")
                print("\n範例資料:")
                for i, artwork in enumerate(artworks[:3], 1):
                    print(f"\n作品 {i}:")
                    print(f"  標題: {artwork.get('title', 'N/A')}")
                    print(f"  藝術家: {artwork.get('artist', 'N/A')}")
                    print(f"  時期: {artwork.get('period', 'N/A')}")

        elif args.directory:
            # 匯入目錄
            dir_path = Path(args.directory)
            artworks = importer.import_directory(
                dir_path,
                recursive=args.recursive,
                save_to_neo4j=save_to_neo4j,
                save_to_chromadb=save_to_chromadb
            )

            if artworks:
                print(f"\n✅ 總共處理 {len(artworks)} 件作品")

        # 顯示統計
        importer.print_stats()

        print("\n✅ 匯入完成!")
        if save_to_neo4j or save_to_chromadb:
            print("\n💡 提示: 資料已匯入資料庫，可以在OpenWebUI中立即使用")

    except KeyboardInterrupt:
        print("\n\n⚠️  使用者中斷")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ 匯入失敗: {e}", exc_info=True)
        sys.exit(1)


def create_templates():
    """建立範例模板檔案"""
    print("\n" + "="*60)
    print("📝 建立範例模板檔案")
    print("="*60)

    template_dir = Path('./import_templates')
    template_dir.mkdir(exist_ok=True)

    # JSON範例
    json_processor = JSONProcessor()
    json_processor.create_template(template_dir / 'template.json', num_examples=2)
    print(f"✅ JSON範例: {template_dir / 'template.json'}")

    # 文字檔範例
    text_processor = TextProcessor()
    text_processor.create_template(template_dir / 'template_structured.txt', 'structured')
    text_processor.create_template(template_dir / 'template_markdown.md', 'markdown')
    text_processor.create_template(template_dir / 'template_separated.txt', 'separated')
    print(f"✅ 結構化文字範例: {template_dir / 'template_structured.txt'}")
    print(f"✅ Markdown範例: {template_dir / 'template_markdown.md'}")
    print(f"✅ 分隔符範例: {template_dir / 'template_separated.txt'}")

    print("\n📁 所有範例模板已建立在: " + str(template_dir))
    print("\n💡 使用方法:")
    print("   1. 複製範例檔案")
    print("   2. 修改為您的資料")
    print("   3. 執行: python import_local_data.py -f 您的檔案.json")


if __name__ == '__main__':
    main()
