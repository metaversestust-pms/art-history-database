"""
藝術史問題範圍過濾器
用於判斷使用者問題是否屬於藝術史領域
"""

class ArtHistoryScopeFilter:
    """藝術史問題範圍過濾器"""

    def __init__(self):
        # 藝術史核心關鍵詞（中英文）
        self.core_keywords = {
            # 藝術類型
            "繪畫", "雕塑", "建築", "書法", "攝影", "版畫", "陶瓷", "工藝",
            "painting", "sculpture", "architecture", "calligraphy", "photography",

            # 藝術流派/風格
            "文藝復興", "巴洛克", "洛可可", "新古典主義", "浪漫主義", "寫實主義",
            "印象派", "後印象派", "野獸派", "立體派", "未來主義", "達達主義",
            "超現實主義", "抽象表現主義", "普普藝術", "極簡主義", "觀念藝術",
            "renaissance", "baroque", "rococo", "neoclassicism", "romanticism",
            "impressionism", "post-impressionism", "fauvism", "cubism", "surrealism",

            # 中國藝術
            "國畫", "山水畫", "花鳥畫", "人物畫", "水墨", "工筆", "寫意",
            "青銅器", "瓷器", "玉器", "漆器", "絲綢", "篆刻",

            # 藝術家相關
            "藝術家", "畫家", "雕塑家", "建築師", "設計師", "攝影師",
            "artist", "painter", "sculptor", "architect", "designer",

            # 藝術作品
            "作品", "名畫", "傑作", "畫作", "雕像", "建築物", "藝術品",
            "artwork", "masterpiece", "painting", "sculpture", "work",

            # 藝術史時期
            "古代", "中世紀", "近代", "現代", "當代", "朝代", "時期", "年代",
            "ancient", "medieval", "modern", "contemporary", "period", "era",

            # 美術館/博物館
            "美術館", "博物館", "畫廊", "展覽", "收藏", "館藏",
            "museum", "gallery", "exhibition", "collection",

            # 藝術技法/元素
            "色彩", "構圖", "筆觸", "光影", "透視", "技法", "風格", "流派",
            "color", "composition", "brushwork", "perspective", "technique", "style",

            # 藝術理論
            "美學", "藝術史", "藝術理論", "批評", "鑑賞",
            "aesthetics", "art history", "art theory", "criticism"
        }

        # 著名藝術家名字（中英文）
        self.artist_names = {
            # 西方藝術家
            "達文西", "米開朗基羅", "拉斐爾", "卡拉瓦喬", "林布蘭", "維梅爾",
            "莫內", "梵谷", "高更", "塞尚", "畢卡索", "馬諦斯", "達利",
            "leonardo", "michelangelo", "raphael", "caravaggio", "rembrandt",
            "monet", "van gogh", "gauguin", "cezanne", "picasso", "matisse", "dali",

            # 中國藝術家
            "王羲之", "顧愷之", "吳道子", "張擇端", "黃公望", "唐寅", "徐渭",
            "鄭板橋", "齊白石", "張大千", "徐悲鴻", "林風眠", "吳冠中"
        }

        # 非藝術史關鍵詞（用於排除）
        self.excluded_keywords = {
            # 技術/編程
            "代碼", "程式", "編程", "軟體", "硬體", "算法", "資料庫",
            "code", "programming", "software", "hardware", "algorithm", "database",

            # 科學
            "化學", "物理", "生物", "數學公式", "方程式", "實驗",
            "chemistry", "physics", "biology", "formula", "equation", "experiment",

            # 醫療
            "疾病", "症狀", "治療", "藥物", "手術", "醫院",
            "disease", "symptom", "treatment", "medicine", "surgery", "hospital",

            # 商業/金融
            "股票", "基金", "投資", "財報", "市場分析",
            "stock", "fund", "investment", "financial report",

            # 日常生活（非藝術相關）
            "菜譜", "烹飪", "食譜", "美食", "旅遊景點",
            "recipe", "cooking", "food", "travel destination"
        }

    def is_art_history_related(self, question: str) -> dict:
        """
        判斷問題是否與藝術史相關

        Args:
            question: 使用者提出的問題

        Returns:
            dict: {
                "is_related": bool,  # 是否相關
                "confidence": float,  # 置信度 (0-1)
                "matched_keywords": list,  # 匹配到的關鍵詞
                "reason": str  # 判斷理由
            }
        """
        question_lower = question.lower()
        matched_keywords = []
        excluded_matches = []

        # 檢查核心關鍵詞
        for keyword in self.core_keywords:
            if keyword.lower() in question_lower:
                matched_keywords.append(keyword)

        # 檢查藝術家名字
        for artist in self.artist_names:
            if artist.lower() in question_lower:
                matched_keywords.append(f"藝術家:{artist}")

        # 檢查排除關鍵詞
        for excluded in self.excluded_keywords:
            if excluded.lower() in question_lower:
                excluded_matches.append(excluded)

        # 計算置信度
        keyword_score = min(len(matched_keywords) * 0.3, 1.0)  # 每個關鍵詞+0.3分
        artist_bonus = 0.4 if any("藝術家:" in k for k in matched_keywords) else 0
        exclusion_penalty = min(len(excluded_matches) * 0.3, 0.8)  # 每個排除詞-0.3分

        confidence = max(0, min(1.0, keyword_score + artist_bonus - exclusion_penalty))

        # 判斷是否相關（置信度 > 0.3 視為相關）
        is_related = confidence > 0.3 and len(excluded_matches) == 0

        # 生成判斷理由
        if is_related:
            if matched_keywords:
                reason = f"問題包含藝術史相關關鍵詞: {', '.join(matched_keywords[:5])}"
            else:
                reason = "問題可能與藝術史相關"
        else:
            if excluded_matches:
                reason = f"問題包含非藝術史領域關鍵詞: {', '.join(excluded_matches[:3])}"
            elif len(matched_keywords) == 0:
                reason = "問題未包含明顯的藝術史相關關鍵詞"
            else:
                reason = "問題相關性不足"

        return {
            "is_related": is_related,
            "confidence": round(confidence, 2),
            "matched_keywords": matched_keywords,
            "reason": reason
        }

    def get_rejection_message(self, question: str, filter_result: dict) -> str:
        """
        生成拒絕回答的訊息

        Args:
            question: 原始問題
            filter_result: is_art_history_related() 的結果

        Returns:
            str: 友好的拒絕訊息
        """
        base_message = "🎨 **藝術史資料庫範圍說明**\n\n"

        if filter_result["confidence"] < 0.1:
            # 完全不相關
            message = base_message + (
                "抱歉，您的問題似乎不在藝術史領域範圍內。\n\n"
                "本系統專注於提供以下藝術史相關資訊：\n"
                "- 🖼️ 各時期藝術作品與藝術家\n"
                "- 🏛️ 藝術流派與風格發展\n"
                "- 🎭 中西方藝術史與文化背景\n"
                "- 🖌️ 繪畫、雕塑、建築等藝術形式\n"
                "- 📚 藝術理論與美學思想\n\n"
                "**建議提問示例：**\n"
                "- 文藝復興時期有哪些重要藝術家？\n"
                "- 印象派繪畫的特點是什麼？\n"
                "- 中國山水畫的發展歷史\n"
                "- 達文西的《蒙娜麗莎》創作背景\n"
            )
        elif filter_result["confidence"] < 0.3:
            # 相關性較低
            message = base_message + (
                f"您的問題「{question}」似乎與藝術史的關聯性較低。\n\n"
                "如果您想詢問藝術史相關問題，建議包含以下元素：\n"
                "- 具體的藝術家名稱（如：莫內、齊白石）\n"
                "- 藝術流派或風格（如：印象派、巴洛克）\n"
                "- 藝術作品或形式（如：繪畫、雕塑）\n"
                "- 藝術史時期（如：文藝復興、清代）\n"
            )
        else:
            # 被排除關鍵詞過濾
            message = base_message + (
                f"抱歉，您的問題「{question}」包含了非藝術史領域的內容。\n\n"
                f"檢測到: {filter_result['reason']}\n\n"
                "本系統專注於藝術史領域，無法回答其他領域的問題。\n"
            )

        return message


# 測試函數
def test_filter():
    """測試過濾器功能"""
    filter = ArtHistoryScopeFilter()

    test_cases = [
        "莫內的睡蓮系列有什麼特色？",  # 應該通過
        "文藝復興時期的建築風格",  # 應該通過
        "Python怎麼連接資料庫？",  # 應該拒絕
        "今天天氣怎麼樣？",  # 應該拒絕
        "齊白石的蝦畫技法",  # 應該通過
        "如何治療感冒？",  # 應該拒絕
    ]

    print("=== 藝術史問題範圍過濾器測試 ===\n")
    for question in test_cases:
        result = filter.is_art_history_related(question)
        print(f"問題: {question}")
        print(f"結果: {'✅ 通過' if result['is_related'] else '❌ 拒絕'}")
        print(f"置信度: {result['confidence']}")
        print(f"理由: {result['reason']}")
        if not result['is_related']:
            print(f"拒絕訊息:\n{filter.get_rejection_message(question, result)}")
        print("-" * 60)

if __name__ == "__main__":
    test_filter()
