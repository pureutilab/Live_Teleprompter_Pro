# -*- coding: utf-8 -*-
"""
Live_Teleprompter_Pro 弹幕监听模块
包含:
1. 模拟弹幕发生器 (MOCK_MODE=True): 真实再现公屏水弹幕与高价值提问
2. Playwright 实时监听器 (MOCK_MODE=False): 无头浏览器解析抖音直播网页公屏 DOM
3. DanmuListenerThread: 统一的 QThread 封装，与 UI 完全解耦
"""

import time
import random
import re
from typing import Optional, Set
from PyQt6.QtCore import QThread, pyqtSignal

import config


# ==============================================================================
# 模拟模式：仿真公屏弹幕数据池
# ==============================================================================
MOCK_FANS = [
    "奶茶加冰不加糖", "数码极客小飞", "晴天小喵酱", "晨曦微露2026",
    "飞奔的五花肉", "星空漫游者", "小李爱穿搭", "可乐冰红茶",
    "晴天娃娃", "运动健将大刘", "穿搭小能手", "杭州打工人",
    "爱笑的向日葵", "月下听风", "潮流先锋阿杰", "天天向上888"
]

# 水弹幕库（用于在顶部公屏流水滚动展示，模拟真实公屏热度）
MOCK_WATER_DANMU = [
    "66666",
    "来了来了！主播好",
    "主播这件穿身上真好看",
    "点赞点赞，支持一下",
    "1111",
    "已点亮粉丝灯牌！",
    "晚上好呀主播~",
    "前排占座！",
    "主播吃了晚饭没？",
    "关注了关注了",
    "哇塞这个质感真的绝",
    "666",
    "比心心[心][比心]",
    "支持国货原创！",
    "今天直播间人好多啊",
    "打卡打卡"
]

# 真实提问弹幕库（高度贴合知识库业务问题，用于触发提词卡片）
MOCK_QUESTION_DANMU = [
    "这件卫衣起球吗？洗了会不会掉色？",
    "主播，我身高175 体重140斤穿多大码合适？",
    "现在拍下什么时候发货呀？顺丰包邮吗？",
    "女生身高165 体重105斤穿哪个码好看？",
    "买两件有没有优惠？可以减多少钱？",
    "有运费险吗？万一尺码不合适支持退换吗？",
    "主播，男生182身高 170斤穿XL还是XXL宽松？",
    "面料是纯棉的吗？贴身穿扎不扎皮肤？",
    "洗过之后会缩水变形吗？帽子够不够大？",
    "偏远地区发货吗？发什么快递？",
    "现在下单有粉丝专属优惠券领吗？",
    "170 120斤穿M还是L？喜欢宽松一点的！"
]


class DanmuListenerThread(QThread):
    """
    弹幕监听后台工作线程
    支持模拟模式与 Playwright 真实直播间监听的动态切换
    """
    # 信号定义
    # danmu_received: (nickname, content)
    danmu_received = pyqtSignal(str, str)
    # status_updated: 状态消息更新
    status_updated = pyqtSignal(str)
    # mode_changed: 当前模式是否为模拟模式
    mode_changed = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.mock_mode: bool = config.MOCK_MODE
        self.live_url: str = getattr(config, "DOUYIN_ROOM_URL", getattr(config, "DOUYIN_LIVE_URL", ""))
        self._is_running: bool = False
        self._playwright_instance = None
        self._browser = None
        self._seen_danmu_keys: Set[str] = set()

    def update_live_url(self, new_url: str):
        """动态更新直播间地址"""
        self.live_url = new_url.strip()
        self._seen_danmu_keys.clear()
        self.status_updated.emit(f"📌 直播间地址已更新为: {self.live_url}")

    def set_mock_mode(self, mock_mode: bool):
        """动态切换模拟模式 / 真实监听模式"""
        if self.mock_mode == mock_mode:
            return
        self.mock_mode = mock_mode
        self.mode_changed.emit(self.mock_mode)
        # 通知更新状态
        if self.mock_mode:
            self.status_updated.emit("🔄 已切换为 [模拟仿真模式]")
        else:
            self.status_updated.emit("🔄 已切换为 [Playwright 真实监听模式]")

    def stop(self):
        """安全停止监听线程"""
        self._is_running = False
        self.quit()
        self.wait(1000)

    def run(self):
        self._is_running = True
        self.mode_changed.emit(self.mock_mode)

        while self._is_running:
            if self.mock_mode:
                self._run_mock_loop()
            else:
                self._run_playwright_loop()

    # ==========================================================================
    # 模拟模式执行逻辑
    # ==========================================================================
    def _run_mock_loop(self):
        self.status_updated.emit("🟢 模拟弹幕源已启动 (每 2.5~4 秒产生一条公屏互动)")
        
        while self._is_running and self.mock_mode:
            # 60% 概率生成普通水弹幕，40% 概率生成高质量提问
            nickname = random.choice(MOCK_FANS)
            if random.random() < 0.60:
                content = random.choice(MOCK_WATER_DANMU)
            else:
                content = random.choice(MOCK_QUESTION_DANMU)

            # 发射弹幕信号
            self.danmu_received.emit(nickname, content)

            # 模拟间隔 2.5 ~ 4.0 秒（可快速中断休眠）
            sleep_time = random.uniform(2.5, 4.0)
            elapsed = 0.0
            step = 0.2
            while elapsed < sleep_time and self._is_running and self.mock_mode:
                time.sleep(step)
                elapsed += step

    # ==========================================================================
    # 真实模式执行逻辑 (Playwright 网页监听)
    # ==========================================================================
    def _run_playwright_loop(self):
        import sys
        import subprocess

        self.status_updated.emit(f"🌐 正在启动 Playwright 引擎监听: {self.live_url}")
        self._seen_danmu_keys.clear()

        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            self.status_updated.emit("❌ 未安装 Playwright 库，请运行: pip install playwright")
            time.sleep(3)
            return

        try:
            with sync_playwright() as p:
                self._playwright_instance = p

                # 启动无头 Chromium 浏览器 (若未下载内核自动尝试安装)
                try:
                    self._browser = p.chromium.launch(
                        headless=True,
                        args=[
                            "--disable-blink-features=AutomationControlled",
                            "--mute-audio",
                            "--no-sandbox",
                            "--disable-dev-shm-usage"
                        ]
                    )
                except Exception as launch_err:
                    err_text = str(launch_err)
                    if "Executable doesn't exist" in err_text or "playwright install" in err_text:
                        self.status_updated.emit("❌ 尚未检测到浏览器内核，请点击顶部【一键安装浏览器内核】")
                    else:
                        self.status_updated.emit(f"❌ 浏览器启动异常: {err_text[:50]}")
                    raise launch_err

                context = self._browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                    viewport={"width": 1280, "height": 800}
                )
                page = context.new_page()

                # 仅屏蔽大型音视频媒体流，防止阻塞直播推流带宽
                page.route(
                    "**/*.{mp4,flv,m3u8,ts,avi,mov}",
                    lambda route: route.abort()
                )

                self.status_updated.emit("⏳ 正在连接抖音直播间网页...")
                try:
                    page.goto(self.live_url, timeout=20000, wait_until="commit")
                except Exception as e:
                    self.status_updated.emit(f"⚠️ 直播间连接提示 (仍将尝试解析): {e}")

                # 检查开播状态
                time.sleep(2.0)
                try:
                    page_content = page.content()
                    if any(k in page_content for k in ["暂时不在家", "已关播", "主播未开播", "直播已结束"]):
                        self.status_updated.emit("⚠️ 当前直播间尚未开播或处于离线状态，正在持续守候中...")
                    else:
                        self.status_updated.emit("✅ 直播间连接成功！开始实时监控公屏聊天区...")
                except Exception:
                    self.status_updated.emit("✅ 监控已启动，正在实时捕捉公屏互动...")

                # 循环轮询 DOM 提取公屏弹幕
                while self._is_running and not self.mock_mode:
                    try:
                        new_messages = self._extract_danmu_from_page(page)
                        for nick, text in new_messages:
                            key = f"{nick}:{text}"
                            if key not in self._seen_danmu_keys:
                                self._seen_danmu_keys.add(key)
                                if len(self._seen_danmu_keys) > 1000:
                                    self._seen_danmu_keys.pop()
                                self.danmu_received.emit(nick, text)
                    except Exception as err:
                        self.status_updated.emit(f"⚠️ 公屏解析瞬态重试: {str(err)[:50]}")

                    # 轮询频率 0.8 ~ 1.0 秒
                    for _ in range(5):
                        if not self._is_running or self.mock_mode:
                            break
                        time.sleep(0.2)

        except Exception as e:
            err_msg = str(e)
            if "Target closed" in err_msg or "Target page" in err_msg:
                self.status_updated.emit("🔄 监听服务已重置，等待下一次循环...")
            else:
                self.status_updated.emit(f"❌ 真实模式提示: {err_msg[:60]}")
            # 短暂等待以防循环过频
            for _ in range(15):
                if not self._is_running or self.mock_mode:
                    break
                time.sleep(0.2)
        finally:
            if self._browser:
                try:
                    self._browser.close()
                except Exception:
                    pass
                self._browser = None

    def _extract_danmu_from_page(self, page) -> list[tuple[str, str]]:
        """
        在无头浏览器中提取抖音直播公屏弹幕节点
        适配抖音主流弹幕容器及降级文本解析
        """
        js_code = """
        () => {
            const results = [];
            // 常见抖音公屏容器选择器
            const items = document.querySelectorAll(
                'div[class*="webcast-chatroom___item"], div[class*="webcast-chatroom___list"] > div, .chatroom-item, div[class*="chat-item"]'
            );
            
            for (let i = 0; i < items.length; i++) {
                const el = items[i];
                const fullText = (el.innerText || el.textContent || '').trim();
                if (!fullText) continue;
                if (fullText.includes('来了') && fullText.includes('欢迎') || fullText.includes('送出了') || fullText.includes('加入直播间')) {
                    continue;
                }
                
                // 尝试提取昵称和内容
                const nickEl = el.querySelector('span[class*="nickname"], span[class*="name"]');
                const contentEl = el.querySelector('span[class*="content"], span[class*="text"]');
                
                if (nickEl && contentEl) {
                    const n = nickEl.innerText.trim().replace(/[:：]$/, '');
                    const c = contentEl.innerText.trim();
                    if (n && c) results.push([n, c]);
                } else {
                    // 兼容格式："昵称：弹幕文本"
                    const colonIdx = fullText.search(/[:：]/);
                    if (colonIdx > 0 && colonIdx < 30) {
                        const n = fullText.slice(0, colonIdx).trim().slice(-12);
                        const c = fullText.slice(colonIdx + 1).trim();
                        if (n && c) results.push([n, c]);
                    }
                }
            }
            return results.slice(-25);
        }
        """
        try:
            raw_list = page.evaluate(js_code)
            parsed = []
            for item in raw_list:
                if isinstance(item, list) and len(item) == 2:
                    nick, text = str(item[0]).strip(), str(item[1]).strip()
                    if nick and text:
                        parsed.append((nick, text))
            return parsed
        except Exception:
            return []
