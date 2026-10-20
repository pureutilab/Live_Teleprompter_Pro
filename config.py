# -*- coding: utf-8 -*-
"""
Live_Teleprompter_Pro 核心配置模块
集中管理 API 配置、运行模式、直播间地址以及背景知识库
"""

import os
import sys
import re

# ============================
# 1. 运行模式配置
# ============================
# 是否开启模拟模式 (True: 自动生成仿真弹幕; False: Playwright真实监听抖音网页)
MOCK_MODE: bool = True

# 真实模式下监听的抖音直播间 URL (支持 DOUYIN_ROOM_URL 与 DOUYIN_LIVE_URL 兼容)
DOUYIN_ROOM_URL: str = "https://live.douyin.com/545089240259"
DOUYIN_LIVE_URL: str = "https://live.douyin.com/545089240259"

# ============================
# 2. AI 模型配置 (OpenAI SDK 兼容)
# ============================
# AI API Key (支持 AI_API_KEY 与 OPENAI_API_KEY 兼容)
# 当 API_KEY 为空字符串时，系统自动无缝降级为“本地智能回复引擎”，免 Key 即可完整运行调试
AI_API_KEY: str = ""
OPENAI_API_KEY: str = ""

# API 请求基础地址 (默认配置 DeepSeek 国内极速接口，亦可切换为 OpenAI, 月之暗面, 通义千问等)
OPENAI_BASE_URL: str = "https://api.deepseek.com"

# 使用的模型名称 (如: deepseek-chat, gpt-4o-mini, qwen-turbo)
OPENAI_MODEL: str = "deepseek-chat"

# ============================
# 3. 提词器 UI 参数
# ============================
MAX_DISPLAY_CARDS: int = 40       # 提词面板保留的最大卡片数量
AUTO_SCROLL_ENABLED: bool = True  # 默认是否开启自动滚动
ALWAYS_ON_TOP: bool = True        # 默认是否始终置顶

# ============================
# 4. 直播间背景知识库 (System Prompt 注入)
# ============================
SYSTEM_KNOWLEDGE_BASE: str = """
【直播间背景与主推商品知识库】
1. 当前主推爆款：2026早春重磅420g连帽加绒卫衣（纯棉赛络纺高支双纱）。
2. 面料与工艺：420g重磅抗风保暖，内里超细摇粒绒亲肤不扎肉；经过定型预缩水防静电处理，承诺100%不起球、不掉毛、不缩水、不褪色。
3. 尺码推荐标准：
   - S码：建议身高160-168cm，体重95-115斤
   - M码：建议身高168-175cm，体重115-135斤
   - L码：建议身高173-180cm，体重135-155斤
   - XL码：建议身高178-185cm，体重155-180斤
   - XXL码：建议身高180-192cm，体重180-210斤
   - 穿着风格提示：喜欢微宽松合身选推荐码，喜欢美式街头Oversize风格直接拍大一码。
4. 发货与物流：全场现货，下单后48小时内发出，默认顺丰/中通极速包邮。
5. 售后保障：全场赠送运费险，支持7天无理由退换货，试穿不合适退货免运费，零风险购物。
6. 今日专属优惠：单件立减30元，两件立减80元；点击上方关注主播再领5元无门槛专属粉丝券。
"""

# ============================
# 5. 动态配置持久化工具函数
# ============================
if getattr(sys, "frozen", False):
    # PyInstaller 打包后的运行环境：优先使用 exe 所在同级目录的 config.py
    _base_dir = os.path.dirname(sys.executable)
    _external_config = os.path.join(_base_dir, "config.py")
    CONFIG_FILE_PATH = _external_config if os.path.exists(_external_config) else os.path.abspath(__file__)
else:
    CONFIG_FILE_PATH = os.path.abspath(__file__)

def save_config_to_file(room_url: str = "", api_key: str = "", base_url: str = "", model_name: str = "", knowledge_base: str = "") -> bool:
    """
    将动态修改的直播间网址、AI API Key、Base URL、Model Name 与知识库持久化写回 config.py，
    并同步更新当前 Python 进程内存中的配置变量。
    """
    global DOUYIN_ROOM_URL, DOUYIN_LIVE_URL, AI_API_KEY, OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL, SYSTEM_KNOWLEDGE_BASE
    if room_url and room_url.strip():
        DOUYIN_ROOM_URL = room_url.strip()
        DOUYIN_LIVE_URL = room_url.strip()
    if api_key is not None:
        AI_API_KEY = api_key.strip()
        OPENAI_API_KEY = api_key.strip()
    if base_url and base_url.strip():
        OPENAI_BASE_URL = base_url.strip()
    if model_name and model_name.strip():
        OPENAI_MODEL = model_name.strip()
    if knowledge_base and knowledge_base.strip():
        SYSTEM_KNOWLEDGE_BASE = knowledge_base.strip()

    try:
        if not os.path.exists(CONFIG_FILE_PATH):
            return False

        with open(CONFIG_FILE_PATH, "r", encoding="utf-8") as f:
            content = f.read()

        # 正则安全替换 DOUYIN_ROOM_URL 和 DOUYIN_LIVE_URL
        content = re.sub(
            r'DOUYIN_ROOM_URL\s*:\s*str\s*=\s*([\'"]).*?\1',
            f'DOUYIN_ROOM_URL: str = "https://live.douyin.com/545089240259"',
            content
        )
        content = re.sub(
            r'DOUYIN_LIVE_URL\s*:\s*str\s*=\s*([\'"]).*?\1',
            f'DOUYIN_LIVE_URL: str = "https://live.douyin.com/545089240259"',
            content
        )

        # 正则安全替换 AI_API_KEY 和 OPENAI_API_KEY
        content = re.sub(
            r'AI_API_KEY\s*:\s*str\s*=\s*([\'"]).*?\1',
            f'AI_API_KEY: str = ""',
            content
        )
        content = re.sub(
            r'OPENAI_API_KEY\s*:\s*str\s*=\s*([\'"]).*?\1',
            f'OPENAI_API_KEY: str = ""',
            content
        )

        # 正则安全替换 OPENAI_BASE_URL 和 OPENAI_MODEL
        content = re.sub(
            r'OPENAI_BASE_URL\s*:\s*str\s*=\s*([\'"]).*?\1',
            f'OPENAI_BASE_URL: str = "https://api.deepseek.com"',
            content
        )
        content = re.sub(
            r'OPENAI_MODEL\s*:\s*str\s*=\s*([\'"]).*?\1',
            f'OPENAI_MODEL: str = "deepseek-chat"',
            content
        )

        with open(CONFIG_FILE_PATH, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    except Exception as e:
        print(f"[config] 持久化保存配置文件异常: {e}")
        return False
