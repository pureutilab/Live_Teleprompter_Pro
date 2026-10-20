# -*- coding: utf-8 -*-
"""
Live_Teleprompter_Pro AI 决策大脑模块
包含:
1. Level 1 本地规则初筛 (LocalFilter): 过滤无意义水弹幕，极大节省 Token
2. Level 2 大模型智能问答 (AIBrain): 结合直播间知识库输出精练口播话术
3. 无 API Key 本地智能降级兜底: 确保离线或未填 Key 情况下完整运行
4. AIEngineWorker (QThread): 异步调用线程，彻底杜绝主界面卡顿
"""

import re
import queue
import time
from typing import Optional, Tuple
from PyQt6.QtCore import QThread, pyqtSignal

import config


# ==============================================================================
# Level 1: 本地规则初筛器
# ==============================================================================
class LocalFilter:
    """第一级过滤器：基于启发式规则初筛，拦截低价值水弹幕"""

    # 常见疑问引导词
    QUESTION_WORDS = [
        "什么", "怎么", "多大", "哪", "几", "谁", "是否", "吗", "么", "能不能",
        "能", "可不可以", "行不行", "有没有", "合适", "合适吗", "建议", "推荐",
        "怎么选", "多少", "会不会", "真不真", "哪个"
    ]

    # 电商直播高频业务关键词
    BUSINESS_KEYWORDS = [
        "尺码", "码数", "身高", "体重", "斤", "cm", "公分", "长短", "厚度",
        "发货", "快递", "顺丰", "中通", "几天到", "什么时候发", "偏远地区",
        "运费险", "退换", "退货", "售后", "保障", "正品", "保真", "质量",
        "起球", "掉色", "褪色", "缩水", "面料", "材质", "纯棉", "透气", "保暖", "掉毛",
        "优惠", "券", "折扣", "多少钱", "减", "拍两件", "活动", "价格", "便宜",
        "版型", "显瘦", "宽松", "内胆", "现货", "预售", "加绒"
    ]

    # 典型无意义水词（若弹幕仅由此类词组成且无疑问特征，直接过滤）
    PURE_WATER_PATTERNS = [
        r"^[0-9]+$",                         # 纯数字 (666, 111)
        r"^[a-zA-Z\s]+$",                     # 纯英文字母
        r"^(哈){2,}$",                        # 哈哈哈
        r"^(牛){1,}$",                        # 牛/牛牛牛
        r"^(来了|打卡|签到|支持|关注了|已点赞|主播好|晚上好|早上好|前排|占座|好看|好帅|好美|真好|爱了)+[！!~。.]*$"
    ]

    @classmethod
    def is_potential_question(cls, content: str) -> bool:
        """
        判断一条弹幕是否包含提问特征或业务意图
        True: 保留进入二级 AI 处理
        False: 过滤忽略
        """
        text = content.strip()

        # 规则 1: 长度小于 3 个字符，极大概率为无意义互动 (如 "6", "好", "在?")
        if len(text) < 3:
            return False

        # 规则 2: 纯数字或典型水弹幕模式
        for pattern in cls.PURE_WATER_PATTERNS:
            if re.match(pattern, text):
                return False

        # 规则 3: 包含问号 (中英文问号)
        if "?" in text or "？" in text:
            return True

        # 规则 4: 包含疑问引导词
        for q_word in cls.QUESTION_WORDS:
            if q_word in text:
                return True

        # 规则 5: 包含电商业务关键词
        for b_word in cls.BUSINESS_KEYWORDS:
            if b_word in text:
                return True

        return False


# ==============================================================================
# Level 2: AI 大脑与本地降级回复引擎
# ==============================================================================
class AIBrain:
    """第二级处理器：OpenAI API 问答 + 本地智能模拟兜底"""

    def __init__(self):
        self.api_key = getattr(config, "AI_API_KEY", getattr(config, "OPENAI_API_KEY", "")).strip()
        self.base_url = config.OPENAI_BASE_URL.strip()
        self.model = config.OPENAI_MODEL.strip()
        self.knowledge_base = config.SYSTEM_KNOWLEDGE_BASE.strip()
        self._openai_client = None
        self._init_client()

    def _init_client(self):
        """根据当前 API Key 初始化或重置 OpenAI 客户端"""
        if self.api_key:
            try:
                from openai import OpenAI
                self._openai_client = OpenAI(
                    api_key=self.api_key,
                    base_url=self.base_url
                )
            except Exception as e:
                print(f"[AIBrain] 初始化 OpenAI 客户端失败: {e}")
                self._openai_client = None
        else:
            self._openai_client = None

    def update_api_config(self, new_key: str, new_base_url: str = "", new_model: str = "") -> Tuple[bool, str]:
        """动态更新 API Key、Base URL 与 Model 并重新初始化客户端"""
        self.api_key = new_key.strip()
        if new_base_url.strip():
            self.base_url = new_base_url.strip()
        if new_model.strip():
            self.model = new_model.strip()
        self._init_client()
        if self.api_key and self._openai_client:
            return True, f"已接入 [{self.model}] 实时推理模式"
        elif not self.api_key:
            return True, "已切换为本地智能模拟回复 (免 Key 模式)"
        else:
            return False, "客户端初始化异常，已自动降级为本地智能话术"

    def update_api_key(self, new_key: str) -> Tuple[bool, str]:
        """兼容旧接口"""
        return self.update_api_config(new_key)

    def answer_question(self, nickname: str, question: str) -> Optional[Tuple[str, str]]:
        """
        对提问生成口播回答话术
        返回: (回答话术文本, 来源类型标识 'api' 或 'mock')
        若 AI 判断为非问题返回 None
        """
        # 1. 若无 API Key 或客户端初始化失败，直接触发本地智能降级引擎
        if not self._openai_client or not self.api_key:
            return self._local_smart_mock_reply(nickname, question), "mock"

        # 2. 具备 API Key，调用大模型分析与生成
        try:
            system_prompt = f"""你是一位顶级抖音带货直播间专业场控与提词AI智囊。
你的任务是实时研判粉丝弹幕提问，并根据以下【直播间背景知识库】迅速生成主播口播回答话术。

{self.knowledge_base}

【严格执行规则】：
1. 研判粉丝弹幕是否属于需要主播解答的商品、尺码、面料、物流、优惠等真实提问。
2. 若完全不是问题或纯无意义水聊，请只输出纯文本：IGNORE
3. 若是有效提问，请基于知识库直接输出主播对粉丝的【口播回答话术】。
4. 要求：极度简短精练（严格控制在 45 个字以内），自然口语化、亲切有销售力（如“家人们/宝贝...”），主播可直接照着念。
5. 严禁包含任何前缀、解释、引号或引言（绝对不要写“建议主播回答：”），直接输出台词本身！"""

            response = self._openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"粉丝【{nickname}】提问：{question}"}
                ],
                temperature=0.3,
                max_tokens=100
            )

            raw_text = response.choices[0].message.content.strip()
            if "IGNORE" in raw_text or not raw_text:
                return None
            
            # 清理可能的多余引号或前缀
            clean_text = raw_text.replace("“", "").replace("”", "").replace('"', "")
            if clean_text.startswith("建议回答："):
                clean_text = clean_text[5:]
            elif clean_text.startswith("主播口播："):
                clean_text = clean_text[5:]

            return clean_text[:50], "api"

        except Exception as e:
            # API 调用异常时优雅降级到本地智能回复
            print(f"[AIBrain] API 调用异常，降级到本地规则: {e}")
            return self._local_smart_mock_reply(nickname, question), "mock"

    def _local_smart_mock_reply(self, nickname: str, question: str) -> str:
        """
        【重要降级逻辑】本地智能模拟回复
        根据电商直播知识库进行精准模式匹配，输出富有主播口播感的自然回答
        """
        q = question.lower()

        # 1. 运费险 / 售后 / 退换（优先研判售后保障意图）
        if any(w in q for w in ["运费险", "退换", "退货", "能退吗", "包退", "售后"]):
            return "全场免费赠送运费险！支持7天无理由退换，试穿不合适退货免邮费，零风险下单！"

        # 2. 优惠 / 折扣 / 券 / 价格
        if any(w in q for w in ["优惠", "便宜", "券", "立减", "活动", "两件", "多少钱"]):
            return "今天直播间拍1件立减30，拍两件立减80！点上方关注再领5元无门槛粉丝券！"

        # 3. 发货 / 快递 / 物流
        if any(w in q for w in ["发货", "快递", "顺丰", "中通", "几天", "现货"]):
            return "全场现货！下单48小时内顺丰中通极速包邮发出，早拍早排单极速收货！"

        # 4. 面料 / 起球 / 掉色 / 缩水 / 掉毛
        if any(w in q for w in ["起球", "掉色", "褪色", "缩水", "面料", "材质", "纯棉", "质量", "扎", "掉毛"]):
            return "宝贝放一万个心！420g高克重纯棉加定型预缩水工艺，承诺100%不起球不掉色！"

        # 5. 尺码 / 身高 / 体重匹配
        if any(w in q for w in ["多大", "尺码", "码", "穿什么", "建议", "多高", "适合"]):
            # 精确匹配体重数值（带“斤”或“kg”或“体重”）
            weight_val = None
            weight_match = re.search(r'(?:体重\s*)?(\d{2,3})\s*斤', q)
            if not weight_match:
                weight_match = re.search(r'体重\s*(\d{2,3})', q)
            if not weight_match:
                kg_match = re.search(r'(\d{2,3})\s*kg', q)
                if kg_match:
                    try:
                        weight_val = int(kg_match.group(1)) * 2
                    except Exception:
                        pass
            else:
                try:
                    weight_val = int(weight_match.group(1))
                except Exception:
                    pass

            if weight_val:
                if weight_val < 115:
                    return f"建议闭眼冲S码！合身微宽松，上身显高显精神，115斤内穿S版型绝了！"
                elif weight_val <= 135:
                    return f"推荐选M码！宽松不勒身微落肩，135斤内穿M微廓形超帅！"
                elif weight_val <= 155:
                    return f"强烈推荐L码！遮肉挺括显瘦，美式街头微廓形，穿L正正好！"
                elif weight_val <= 180:
                    return f"建议拍XL码！包容性绝了，180斤内穿XL帅气大方，完全不挑人！"
                else:
                    return f"直接选XXL码！宽松无束缚，420g重磅质感拉满，微胖兄弟必入！"
            return f"宝贝把身高体重打公屏！微宽松选推荐码，偏爱美式Oversize直接拍大一码！"

        # 6. 通用兜底话术
        return f"感谢【{nickname}】提问！这是当季主推爆款，重磅好版型，放心闭眼冲！"


# ==============================================================================
# 异步后台处理 Worker 线程
# ==============================================================================
class AIEngineWorker(QThread):
    """
    负责在后台消费提问队列并调用 AIBrain
    彻底隔离网络 IO 与 PyQt 主界面的事件循环
    """
    # 信号定义
    # question_answered: (nickname, question, answer, source_tag)
    question_answered = pyqtSignal(str, str, str, str)
    status_updated = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.brain = AIBrain()
        self._queue = queue.Queue()
        self._is_running = False

    def enqueue_question(self, nickname: str, question: str):
        """主线程推送待处理的初筛提问"""
        self._queue.put((nickname, question))

    def update_api_config(self, new_key: str, new_base_url: str = "", new_model: str = "") -> Tuple[bool, str]:
        """动态更新 API Key、Base URL 与 Model 并通知状态"""
        ok, msg = self.brain.update_api_config(new_key, new_base_url, new_model)
        self.status_updated.emit(f"🧠 AI 配置更新: {msg}")
        return ok, msg

    def update_api_key(self, new_key: str) -> Tuple[bool, str]:
        """兼容旧接口"""
        return self.update_api_config(new_key)

    def stop(self):
        self._is_running = False
        self.quit()
        self.wait(1000)

    def run(self):
        self._is_running = True
        api_mode_desc = "OpenAI API" if self.brain.api_key else "本地智能规则引擎 (无 Key 模式)"
        self.status_updated.emit(f"🧠 AI 决策核心已就绪 [{api_mode_desc}]")

        while self._is_running:
            try:
                # 非阻塞或带超时等待
                try:
                    nickname, question = self._queue.get(timeout=0.5)
                except queue.Empty:
                    continue

                # 调用 AI 大脑生成口播建议
                result = self.brain.answer_question(nickname, question)
                if result is not None:
                    answer, source = result
                    self.question_answered.emit(nickname, question, answer, source)

                self._queue.task_done()
            except Exception as e:
                self.status_updated.emit(f"⚠️ AI 线程瞬态异常: {e}")
                time.sleep(0.5)
