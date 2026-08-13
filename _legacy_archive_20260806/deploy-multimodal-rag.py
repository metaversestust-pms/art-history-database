#!/usr/bin/env python3
"""
多模態RAG部署腳本
整合現有系統與LangChain實現
"""

import asyncio
import requests
import json
import time
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import os

# 配置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class RAGConfig:
    """RAG系統配置"""
    # 現有服務地址
    api_server: str = "http://localhost:3000"
    ml_service: str = "http://localhost:8080"

    # RAG參數
    chunk_size: int = 1000
    chunk_overlap: int = 200
    top_k: int = 5

    # 多模態權重
    text_weight: float = 0.6
    image_weight: float = 0.4

class SimpleMultimodalRAG:
    """簡化版多模態RAG系統"""

    def __init__(self, config: RAGConfig):
        self.config = config
        self.session = requests.Session()

        # 設置超時
        self.session.timeout = (5, 30)  # (連接超時, 讀取超時)

    def check_services(self) -> Dict[str, bool]:
        """檢查服務狀態"""
        services = {
            'api_server': False,
            'ml_service': False
        }

        # 檢查API服務器
        try:
            response = self.session.get(f"{self.config.api_server}/health", timeout=5)
            services['api_server'] = response.status_code == 200
            logger.info(f"✅ API服務器狀態: {'正常' if services['api_server'] else '異常'}")
        except Exception as e:
            logger.warning(f"⚠️ API服務器連接失敗: {e}")

        # 檢查ML服務
        try:
            response = self.session.get(f"{self.config.ml_service}/health", timeout=5)
            services['ml_service'] = response.status_code == 200
            logger.info(f"✅ ML服務狀態: {'正常' if services['ml_service'] else '異常'}")
        except Exception as e:
            logger.warning(f"⚠️ ML服務連接失敗: {e}")

        return services

    def generate_embeddings(self, texts: List[str]) -> Optional[List[List[float]]]:
        """生成文本嵌入向量"""
        try:
            response = self.session.post(
                f"{self.config.ml_service}/embeddings",
                json={
                    "texts": texts,
                    "model": "bge-m3"
                },
                headers={"Content-Type": "application/json"}
            )

            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    logger.info(f"✅ 成功生成 {len(texts)} 個文本嵌入")
                    return result["embeddings"]

            logger.error(f"❌ 嵌入生成失敗: {response.text}")
            return None

        except Exception as e:
            logger.error(f"❌ 嵌入生成異常: {e}")
            return None

    def classify_artwork(self, text: str) -> Optional[Dict[str, Any]]:
        """藝術品分類"""
        try:
            response = self.session.post(
                f"{self.config.ml_service}/classify/artwork",
                json={"text": text},
                headers={"Content-Type": "application/json"}
            )

            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    logger.info(f"✅ 藝術品分類完成")
                    return result

            logger.error(f"❌ 藝術品分類失敗: {response.text}")
            return None

        except Exception as e:
            logger.error(f"❌ 藝術品分類異常: {e}")
            return None

    def similarity_search(self, query: str, top_k: int = None) -> Optional[List[Dict]]:
        """相似性搜索"""
        if top_k is None:
            top_k = self.config.top_k

        try:
            response = self.session.post(
                f"{self.config.ml_service}/similarity/search",
                json={
                    "query_text": query,
                    "top_k": top_k
                },
                headers={"Content-Type": "application/json"}
            )

            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    logger.info(f"✅ 相似性搜索完成，找到 {len(result['similar_items'])} 個結果")
                    return result["similar_items"]

            logger.error(f"❌ 相似性搜索失敗: {response.text}")
            return None

        except Exception as e:
            logger.error(f"❌ 相似性搜索異常: {e}")
            return None

    def rag_generate(self, question: str) -> Optional[Dict[str, Any]]:
        """RAG智能生成"""
        try:
            response = self.session.post(
                f"{self.config.ml_service}/rag/generate",
                json={"question": question},
                headers={"Content-Type": "application/json"}
            )

            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    logger.info(f"✅ RAG生成完成")
                    return result

            logger.error(f"❌ RAG生成失敗: {response.text}")
            return None

        except Exception as e:
            logger.error(f"❌ RAG生成異常: {e}")
            return None

    def multimodal_query(self, query: str) -> Dict[str, Any]:
        """多模態查詢處理"""
        start_time = time.time()

        # 1. 文本分類和理解
        classification = self.classify_artwork(query)

        # 2. 相似性檢索
        similar_items = self.similarity_search(query)

        # 3. RAG智能回答
        rag_response = self.rag_generate(query)

        # 4. 整合結果
        processing_time = time.time() - start_time

        result = {
            "query": query,
            "processing_time": f"{processing_time:.2f}秒",
            "classification": classification,
            "similar_items": similar_items,
            "rag_response": rag_response,
            "timestamp": time.time()
        }

        return result

    def batch_query(self, queries: List[str]) -> List[Dict[str, Any]]:
        """批次查詢處理"""
        logger.info(f"🔄 開始處理 {len(queries)} 個查詢...")

        results = []
        for i, query in enumerate(queries, 1):
            logger.info(f"📝 處理查詢 {i}/{len(queries)}: {query[:50]}...")
            result = self.multimodal_query(query)
            results.append(result)

        logger.info(f"✅ 批次查詢處理完成")
        return results

def deploy_multimodal_rag():
    """部署多模態RAG系統"""
    print("🚀 開始部署多模態RAG系統...")
    print("=" * 60)

    # 1. 初始化配置
    config = RAGConfig()
    rag_system = SimpleMultimodalRAG(config)

    # 2. 檢查服務狀態
    print("\n🔍 檢查服務狀態...")
    services = rag_system.check_services()

    # 允許在只有ML服務時繼續部署
    if not services['ml_service']:
        print("❌ ML服務不可用，請確保ML服務正在運行：")
        print("  - ML服務: python3 simple-app.py (port 8080)")
        return False

    if not services['api_server']:
        print("⚠️ API服務器不可用，但可以使用ML服務進行RAG功能測試")
        print("  - 注意: 某些功能可能受限制")

    # 3. 測試基本功能
    print("\n🧪 測試RAG系統功能...")

    test_queries = [
        "印象派繪畫有什麼特色？",
        "達文西的藝術風格如何？",
        "現代藝術與古典藝術的區別"
    ]

    successful_tests = 0
    total_tests = len(test_queries)

    for i, query in enumerate(test_queries, 1):
        print(f"\n📝 測試 {i}/{total_tests}: {query}")
        print("-" * 40)

        try:
            result = rag_system.multimodal_query(query)

            # 檢查結果完整性
            checks = {
                "分類結果": result.get("classification") is not None,
                "相似項目": result.get("similar_items") is not None,
                "RAG回答": result.get("rag_response") is not None
            }

            print(f"處理時間: {result['processing_time']}")

            for check_name, passed in checks.items():
                status = "✅" if passed else "❌"
                print(f"{status} {check_name}: {'通過' if passed else '失敗'}")

            if all(checks.values()):
                successful_tests += 1
                print("✅ 測試通過")
            else:
                print("❌ 測試失敗")

        except Exception as e:
            print(f"❌ 測試異常: {e}")

    # 4. 顯示部署結果
    print("\n" + "=" * 60)
    print("📊 部署結果摘要:")
    print(f"✅ 服務可用性: {sum(services.values())}/{len(services)}")
    print(f"✅ 功能測試: {successful_tests}/{total_tests}")

    success_rate = successful_tests / total_tests
    if success_rate >= 0.8:
        print("\n🎉 多模態RAG系統部署成功！")
        print("\n📋 可用功能:")
        print("  - 多語言文本嵌入生成")
        print("  - 藝術史專業分類")
        print("  - 語意相似性搜索")
        print("  - RAG智能問答")
        print("  - 多模態查詢處理")

        print("\n🌐 API端點:")
        print(f"  - 健康檢查: {config.api_server}/health")
        print(f"  - ML服務: {config.ml_service}/health")

        return True
    else:
        print(f"\n⚠️ 系統部分功能異常，成功率: {success_rate:.1%}")
        return False

def interactive_demo():
    """互動式演示"""
    config = RAGConfig()
    rag_system = SimpleMultimodalRAG(config)

    print("\n🎮 互動式RAG演示")
    print("輸入 'exit' 退出演示\n")

    while True:
        try:
            query = input("🤔 請輸入您的藝術史問題: ").strip()

            if query.lower() in ['exit', 'quit', '退出']:
                print("👋 感謝使用多模態RAG系統！")
                break

            if not query:
                continue

            print(f"\n🔄 處理中...")
            result = rag_system.multimodal_query(query)

            print(f"\n📊 查詢結果:")
            print(f"⏱️ 處理時間: {result['processing_time']}")

            if result.get('rag_response') and result['rag_response'].get('success'):
                print(f"\n💡 智能回答:")
                print(result['rag_response']['generated_text'])

            if result.get('classification') and result['classification'].get('success'):
                classification = result['classification']['classification']
                print(f"\n🏷️ 分類結果:")
                for key, value in classification.items():
                    print(f"  {key}: {value}")

            if result.get('similar_items'):
                print(f"\n🔗 相關項目: {len(result['similar_items'])} 個")

            print("\n" + "-" * 50)

        except KeyboardInterrupt:
            print("\n\n👋 感謝使用多模態RAG系統！")
            break
        except Exception as e:
            print(f"\n❌ 處理異常: {e}")

if __name__ == "__main__":
    success = deploy_multimodal_rag()

    if success:
        # 詢問是否運行演示
        try:
            demo = input("\n🎮 是否運行互動式演示？(y/N): ").strip().lower()
            if demo in ['y', 'yes', '是']:
                interactive_demo()
        except KeyboardInterrupt:
            print("\n👋 部署完成！")
    else:
        print("\n❌ 部署失敗，請檢查服務狀態")
        exit(1)