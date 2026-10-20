# -*- coding: utf-8 -*-
"""
Live_Teleprompter_Pro 主程序
基于 PyQt6 构建的独立置顶主播提词器客户端
"""

import sys
import datetime
from PyQt6.QtCore import Qt, QTimer, pyqtSlot
from PyQt6.QtGui import QFont, QColor, QPalette, QIcon, QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QCheckBox, QScrollArea, QFrame, QSizePolicy,
    QGraphicsDropShadowEffect, QLineEdit, QMessageBox
)

import config
from danmu_listener import DanmuListenerThread
from ai_brain import LocalFilter, AIEngineWorker


# ==============================================================================
# UI 组件：独立提词卡片 (PrompterCard)
# ==============================================================================
class PrompterCard(QFrame):
    """
    单张高对比度提词卡片
    包含：粉丝信息、粉丝提问（高亮黄字）、AI 建议口播话术（大号白字）、已念标记
    """
    def __init__(self, nickname: str, question: str, answer: str, source: str, parent=None):
        super().__init__(parent)
        self.setObjectName("PrompterCard")
        self.is_marked = False

        self._setup_ui(nickname, question, answer, source)

    def _setup_ui(self, nickname: str, question: str, answer: str, source: str):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 14)
        layout.setSpacing(10)

        # 1. 顶部元信息栏 (昵称、时间、模型标识、已念按钮)
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)

        # 粉丝昵称
        nick_label = QLabel(f"👤 {nickname}")
        nick_label.setStyleSheet("color: #94a3b8; font-size: 13px; font-weight: 600;")
        header_layout.addWidget(nick_label)

        # 时间标签
        time_str = datetime.datetime.now().strftime("%H:%M:%S")
        time_label = QLabel(time_str)
        time_label.setStyleSheet("color: #64748b; font-size: 11px;")
        header_layout.addWidget(time_label)

        header_layout.addStretch()

        # 来源标识 Badge
        if source == "api":
            source_badge = QLabel("⚡ AI大模型")
            source_badge.setStyleSheet(
                "background-color: #3b1d54; color: #d8b4fe; border: 1px solid #7e22ce; "
                "font-size: 11px; padding: 2px 6px; border-radius: 4px; font-weight: bold;"
            )
        else:
            source_badge = QLabel("🤖 本地智能")
            source_badge.setStyleSheet(
                "background-color: #064e3b; color: #6ee7b7; border: 1px solid #047857; "
                "font-size: 11px; padding: 2px 6px; border-radius: 4px; font-weight: bold;"
            )
        header_layout.addWidget(source_badge)

        # "已念" 标记按钮
        self.btn_mark = QPushButton("✓ 念过")
        self.btn_mark.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_mark.setStyleSheet(
            "QPushButton { background-color: #272a34; color: #94a3b8; border: 1px solid #3b4252; "
            "border-radius: 4px; padding: 2px 8px; font-size: 11px; } "
            "QPushButton:hover { background-color: #3b4252; color: #ffffff; }"
        )
        self.btn_mark.clicked.connect(self._toggle_marked)
        header_layout.addWidget(self.btn_mark)

        layout.addLayout(header_layout)

        # 2. 粉丝提问内容 (黄色高亮显眼显示)
        self.q_label = QLabel(f"❓ 粉丝问：{question}")
        self.q_label.setWordWrap(True)
        self.q_label.setStyleSheet(
            "color: #fbbf24; font-size: 15px; font-weight: bold; line-height: 1.3;"
        )
        layout.addWidget(self.q_label)

        # 3. AI 建议口播回答 (大号白字高对比度容器)
        ans_container = QFrame()
        ans_container.setStyleSheet(
            "background-color: #171922; border-left: 4px solid #10b981; border-radius: 6px; padding: 8px 10px;"
        )
        ans_layout = QVBoxLayout(ans_container)
        ans_layout.setContentsMargins(8, 6, 8, 6)
        ans_layout.setSpacing(4)

        ans_hint = QLabel("🎙️ 建议直接念：")
        ans_hint.setStyleSheet("color: #34d399; font-size: 12px; font-weight: bold;")
        ans_layout.addWidget(ans_hint)

        self.ans_text = QLabel(answer)
        self.ans_text.setWordWrap(True)
        self.ans_text.setStyleSheet(
            "color: #ffffff; font-size: 18px; font-weight: 600; line-height: 1.45;"
        )
        ans_layout.addWidget(self.ans_text)

        layout.addWidget(ans_container)

        # 设置卡片基础边框与阴影效果
        self._apply_style()

    def _apply_style(self):
        if self.is_marked:
            self.setStyleSheet(
                "QFrame#PrompterCard { background-color: #16181f; border: 1px dashed #334155; "
                "border-radius: 10px; margin-bottom: 4px; opacity: 0.6; }"
            )
            self.q_label.setStyleSheet("color: #64748b; font-size: 14px; text-decoration: line-through;")
            self.ans_text.setStyleSheet("color: #64748b; font-size: 15px;")
            self.btn_mark.setText("已读")
            self.btn_mark.setStyleSheet(
                "QPushButton { background-color: #1e293b; color: #475569; border: 1px solid #334155; "
                "border-radius: 4px; padding: 2px 8px; font-size: 11px; }"
            )
        else:
            self.setStyleSheet(
                "QFrame#PrompterCard { background-color: #1f232d; border: 1px solid #333948; "
                "border-radius: 10px; margin-bottom: 4px; }"
            )

    def _toggle_marked(self):
        self.is_marked = not self.is_marked
        self._apply_style()


# ==============================================================================
# UI 主窗口：独立置顶提词器 (TeleprompterWindow)
# ==============================================================================
class TeleprompterWindow(QMainWindow):
    """抖音直播 AI 实时提词器独立窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("抖音直播 AI 实时提词器 (Live Teleprompter Pro)")
        self.resize(540, 820)
        self.setMinimumSize(440, 560)

        # 状态统计
        self.total_danmu_count: int = 0
        self.question_count: int = 0
        self.is_auto_scroll: bool = config.AUTO_SCROLL_ENABLED
        self.is_always_on_top: bool = config.ALWAYS_ON_TOP
        self.cards: list[PrompterCard] = []

        # 置顶初始化
        if self.is_always_on_top:
            self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)

        # 初始化后台工作线程
        self.ai_worker = AIEngineWorker()
        self.danmu_thread = DanmuListenerThread()

        # 构建界面与信号槽
        self._setup_ui()
        self._connect_signals()

        # 启动后台工作线程
        self.ai_worker.start()
        self.danmu_thread.start()

    def _setup_ui(self):
        """构建整体视觉界面"""
        # 全局深色调主题配色
        self.setStyleSheet("""
            QMainWindow {
                background-color: #111216;
            }
            QWidget#CentralWidget {
                background-color: #111216;
            }
            QScrollBar:vertical {
                border: none;
                background: #181920;
                width: 8px;
                margin: 0px 0px 0px 0px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #374151;
                min-height: 25px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover {
                background: #4b5563;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }
        """)

        central_widget = QWidget()
        central_widget.setObjectName("CentralWidget")
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 8)
        main_layout.setSpacing(8)

        # ----------------------------------------------------------------------
        # 1. 顶部状态与工具栏
        # ----------------------------------------------------------------------
        top_bar = QFrame()
        top_bar.setStyleSheet("""
            QFrame {
                background-color: #1a1c23;
                border: 1px solid #282c37;
                border-radius: 8px;
                padding: 6px;
            }
        """)
        top_layout = QVBoxLayout(top_bar)
        top_layout.setContentsMargins(8, 6, 8, 6)
        top_layout.setSpacing(6)

        # 行 1: 标题与模式切换/置顶复选框
        row1_layout = QHBoxLayout()
        row1_layout.setSpacing(8)

        title_label = QLabel("⚡ 抖音 AI 实时提词器")
        title_label.setStyleSheet("color: #f1f5f9; font-size: 15px; font-weight: bold;")
        row1_layout.addWidget(title_label)

        self.lbl_mode_badge = QLabel("🟢 模拟模式")
        self.lbl_mode_badge.setStyleSheet("""
            QLabel {
                background-color: #064e3b;
                color: #a7f3d0;
                border: 1px solid #059669;
                border-radius: 4px;
                padding: 2px 6px;
                font-size: 11px;
                font-weight: bold;
            }
        """)
        row1_layout.addWidget(self.lbl_mode_badge)

        row1_layout.addStretch()

        # 置顶勾选框
        self.chk_top = QCheckBox("📌 始终置顶")
        self.chk_top.setChecked(self.is_always_on_top)
        self.chk_top.setStyleSheet("QCheckBox { color: #cbd5e1; font-size: 12px; }")
        self.chk_top.toggled.connect(self._toggle_always_on_top)
        row1_layout.addWidget(self.chk_top)

        # 暂停滚屏勾选框
        self.chk_pause_scroll = QCheckBox("⏸️ 暂停滚屏")
        self.chk_pause_scroll.setChecked(not self.is_auto_scroll)
        self.chk_pause_scroll.setStyleSheet("QCheckBox { color: #cbd5e1; font-size: 12px; }")
        self.chk_pause_scroll.toggled.connect(self._toggle_pause_scroll)
        row1_layout.addWidget(self.chk_pause_scroll)

        top_layout.addLayout(row1_layout)

        # 行 2: 操作按钮组
        row2_layout = QHBoxLayout()
        row2_layout.setSpacing(8)

        # 模式切换按钮
        self.btn_toggle_mode = QPushButton("🔄 切换为真实网页监听")
        self.btn_toggle_mode.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_toggle_mode.setStyleSheet("""
            QPushButton {
                background-color: #2563eb;
                color: #ffffff;
                border: none;
                border-radius: 4px;
                padding: 5px 12px;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #1d4ed8;
            }
        """)
        self.btn_toggle_mode.clicked.connect(self._toggle_listener_mode)
        row2_layout.addWidget(self.btn_toggle_mode)

        # 清空面板按钮
        btn_clear = QPushButton("🗑️ 清空提词卡片")
        btn_clear.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_clear.setStyleSheet("""
            QPushButton {
                background-color: #374151;
                color: #f3f4f6;
                border: none;
                border-radius: 4px;
                padding: 5px 10px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #4b5563;
            }
        """)
        btn_clear.clicked.connect(self._clear_cards)
        row2_layout.addWidget(btn_clear)

        row2_layout.addStretch()
        top_layout.addLayout(row2_layout)

        main_layout.addWidget(top_bar)

        # ----------------------------------------------------------------------
        # 1.5 动态配置区域 (直播间网址 + AI API Key + 保存生效按钮)
        # ----------------------------------------------------------------------
        settings_frame = QFrame()
        settings_frame.setObjectName("SettingsFrame")
        settings_frame.setStyleSheet("""
            QFrame#SettingsFrame {
                background-color: #171922;
                border: 1px solid #282c3a;
                border-radius: 8px;
                padding: 4px;
            }
            QLabel {
                color: #cbd5e1;
                font-size: 12px;
                font-weight: 600;
            }
            QLineEdit {
                background-color: #0d0f14;
                color: #f8fafc;
                border: 1px solid #334155;
                border-radius: 5px;
                padding: 4px 8px;
                font-size: 12px;
                selection-background-color: #2563eb;
            }
            QLineEdit:focus {
                border: 1px solid #3b82f6;
            }
        """)
        settings_layout = QVBoxLayout(settings_frame)
        settings_layout.setContentsMargins(8, 6, 8, 6)
        settings_layout.setSpacing(6)

        # 输入项 1: 直播间网址
        url_layout = QHBoxLayout()
        url_layout.setSpacing(8)
        lbl_url = QLabel("直播间网址:")
        lbl_url.setFixedWidth(78)
        self.txt_room_url = QLineEdit()
        self.txt_room_url.setPlaceholderText("例如: https://live.douyin.com/545089240259")
        current_url = getattr(config, "DOUYIN_ROOM_URL", getattr(config, "DOUYIN_LIVE_URL", ""))
        self.txt_room_url.setText(current_url)
        url_layout.addWidget(lbl_url)
        url_layout.addWidget(self.txt_room_url)
        settings_layout.addLayout(url_layout)

        # 输入项 2: AI API Key
        key_layout = QHBoxLayout()
        key_layout.setSpacing(8)
        lbl_key = QLabel("AI API Key:")
        lbl_key.setFixedWidth(78)
        self.txt_api_key = QLineEdit()
        self.txt_api_key.setPlaceholderText("输入 sk-... (留空则自动启用本地智能话术)")
        self.txt_api_key.setEchoMode(QLineEdit.EchoMode.Password)
        current_key = getattr(config, "AI_API_KEY", getattr(config, "OPENAI_API_KEY", ""))
        self.txt_api_key.setText(current_key)

        # 显示/隐藏密码按钮
        self.btn_toggle_key_vis = QPushButton("👁️")
        self.btn_toggle_key_vis.setFixedWidth(32)
        self.btn_toggle_key_vis.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_toggle_key_vis.setToolTip("显示/隐藏 API Key")
        self.btn_toggle_key_vis.setStyleSheet("""
            QPushButton {
                background-color: #242834;
                color: #cbd5e1;
                border: 1px solid #3b4252;
                border-radius: 4px;
                padding: 3px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #333a4c;
                color: #ffffff;
            }
        """)
        self.btn_toggle_key_vis.clicked.connect(self._toggle_key_visibility)

        key_layout.addWidget(lbl_key)
        key_layout.addWidget(self.txt_api_key)
        key_layout.addWidget(self.btn_toggle_key_vis)
        settings_layout.addLayout(key_layout)

        # 行 3: 保存配置并生效按钮 + 状态提示
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        self.btn_save_config = QPushButton("💾 保存配置并生效")
        self.btn_save_config.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_save_config.setStyleSheet("""
            QPushButton {
                background-color: #059669;
                color: #ffffff;
                border: none;
                border-radius: 4px;
                padding: 6px 14px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #10b981;
            }
            QPushButton:pressed {
                background-color: #047857;
            }
        """)
        self.btn_save_config.clicked.connect(self._on_save_config)
        btn_row.addWidget(self.btn_save_config)

        self.lbl_config_status = QLabel("修改后点击保存立即热生效并持久化")
        self.lbl_config_status.setStyleSheet("color: #64748b; font-size: 11px;")
        btn_row.addWidget(self.lbl_config_status)
        btn_row.addStretch()

        settings_layout.addLayout(btn_row)
        main_layout.addWidget(settings_frame)

        # ----------------------------------------------------------------------
        # 2. 公屏实时流水跑马条 (水弹幕小字闪过，证明正在监听)
        # ----------------------------------------------------------------------
        ticker_frame = QFrame()
        ticker_frame.setStyleSheet("""
            QFrame {
                background-color: #0b0c0f;
                border: 1px solid #1f232d;
                border-radius: 6px;
                padding: 4px 8px;
            }
        """)
        ticker_layout = QHBoxLayout(ticker_frame)
        ticker_layout.setContentsMargins(6, 4, 6, 4)
        ticker_layout.setSpacing(8)

        ticker_tag = QLabel("📡 公屏流水:")
        ticker_tag.setStyleSheet("color: #64748b; font-size: 11px; font-weight: bold;")
        ticker_layout.addWidget(ticker_tag)

        self.lbl_danmu_ticker = QLabel("等待接收公屏弹幕数据...")
        self.lbl_danmu_ticker.setStyleSheet("color: #94a3b8; font-size: 12px;")
        ticker_layout.addWidget(self.lbl_danmu_ticker, 1)

        main_layout.addWidget(ticker_frame)

        # ----------------------------------------------------------------------
        # 3. 主提词卡片滚动展示区域
        # ----------------------------------------------------------------------
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setStyleSheet("QScrollArea { background-color: transparent; }")

        self.card_container = QWidget()
        self.card_layout = QVBoxLayout(self.card_container)
        self.card_layout.setContentsMargins(2, 4, 4, 4)
        self.card_layout.setSpacing(10)
        self.card_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # 初始占位提示
        self.empty_placeholder = QLabel(
            "🎯 提词器正在实时监听...\n"
            "公屏产生商品/尺码/物流/优惠等提问时，AI 建议口播卡片将自动置顶呈现。"
        )
        self.empty_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_placeholder.setStyleSheet(
            "color: #475569; font-size: 14px; padding: 40px 20px; line-height: 1.6;"
        )
        self.card_layout.addWidget(self.empty_placeholder)

        self.scroll_area.setWidget(self.card_container)
        main_layout.addWidget(self.scroll_area, 1)

        # ----------------------------------------------------------------------
        # 4. 底部状态栏
        # ----------------------------------------------------------------------
        bottom_bar = QFrame()
        bottom_bar.setStyleSheet("""
            QFrame {
                background-color: #14161c;
                border-top: 1px solid #1f232d;
                padding: 4px;
            }
        """)
        bottom_layout = QHBoxLayout(bottom_bar)
        bottom_layout.setContentsMargins(6, 2, 6, 2)

        self.lbl_status_msg = QLabel("系统初始化完成")
        self.lbl_status_msg.setStyleSheet("color: #64748b; font-size: 11px;")
        bottom_layout.addWidget(self.lbl_status_msg)

        bottom_layout.addStretch()

        self.lbl_stats = QLabel("捕获流水: 0 | 提词卡片: 0")
        self.lbl_stats.setStyleSheet("color: #94a3b8; font-size: 11px; font-weight: bold;")
        bottom_layout.addWidget(self.lbl_stats)

        main_layout.addWidget(bottom_bar)

    def _connect_signals(self):
        """绑定后台线程信号与槽函数"""
        # 弹幕接收
        self.danmu_thread.danmu_received.connect(self._on_danmu_received)
        self.danmu_thread.status_updated.connect(self._on_thread_status_updated)
        self.danmu_thread.mode_changed.connect(self._on_listener_mode_changed)

        # AI 作答返回
        self.ai_worker.question_answered.connect(self._on_question_answered)
        self.ai_worker.status_updated.connect(self._on_thread_status_updated)

    # ==========================================================================
    # 核心业务槽函数
    # ==========================================================================
    @pyqtSlot(str, str)
    def _on_danmu_received(self, nickname: str, content: str):
        """处理来自监听线程的新弹幕"""
        self.total_danmu_count += 1
        time_tag = datetime.datetime.now().strftime("%H:%M:%S")

        # 1. 顶部流水条展示所有公屏（包括水弹幕），证实系统正常运转
        self.lbl_danmu_ticker.setText(f"[{time_tag}] {nickname}: {content}")
        self._update_stats_display()

        # 2. 第一级初筛：过滤水弹幕，只保留真实业务提问
        if LocalFilter.is_potential_question(content):
            # 将合格的提问异步入队给 AI 决策线程
            self.ai_worker.enqueue_question(nickname, content)

    @pyqtSlot(str, str, str, str)
    def _on_question_answered(self, nickname: str, question: str, answer: str, source: str):
        """接收 AI 决策线程返回的口播提词卡片"""
        # 隐藏初始占位提示
        if self.empty_placeholder.isVisible():
            self.empty_placeholder.hide()

        # 控制卡片总数，仅淘汰最早的提词卡片，防止内存过大
        while len(self.cards) >= config.MAX_DISPLAY_CARDS:
            old_card = self.cards.pop(0)
            self.card_layout.removeWidget(old_card)
            old_card.deleteLater()

        # 创建新卡片并加入队列
        card = PrompterCard(nickname, question, answer, source, self.card_container)
        self.card_layout.addWidget(card)
        self.cards.append(card)
        self.question_count += 1
        self._update_stats_display()

        # 自动滚动至最新提词卡片
        if self.is_auto_scroll:
            QTimer.singleShot(60, self._scroll_to_bottom)

    def _scroll_to_bottom(self):
        vbar = self.scroll_area.verticalScrollBar()
        vbar.setValue(vbar.maximum())

    def _update_stats_display(self):
        self.lbl_stats.setText(
            f"捕获流水: {self.total_danmu_count} | 提词卡片: {self.question_count}"
        )

    @pyqtSlot(str)
    def _on_thread_status_updated(self, msg: str):
        self.lbl_status_msg.setText(msg)

    # ==========================================================================
    # 工具栏控制操作
    # ==========================================================================
    def _toggle_always_on_top(self, checked: bool):
        self.is_always_on_top = checked
        if checked:
            self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        else:
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowStaysOnTopHint)
        self.show()

    def _toggle_pause_scroll(self, checked: bool):
        # 勾选 "暂停滚屏" 即关闭自动滚动
        self.is_auto_scroll = not checked

    def _toggle_listener_mode(self):
        new_mode = not self.danmu_thread.mock_mode
        self.danmu_thread.set_mock_mode(new_mode)

    @pyqtSlot(bool)
    def _on_listener_mode_changed(self, is_mock: bool):
        if is_mock:
            self.lbl_mode_badge.setText("🟢 模拟模式")
            self.lbl_mode_badge.setStyleSheet("""
                background-color: #064e3b; color: #a7f3d0; border: 1px solid #059669;
                border-radius: 4px; padding: 2px 6px; font-size: 11px; font-weight: bold;
            """)
            self.btn_toggle_mode.setText("🔄 切换为真实网页监听")
            self.btn_toggle_mode.setStyleSheet("""
                QPushButton { background-color: #2563eb; color: #ffffff; border: none; border-radius: 4px; padding: 5px 12px; font-size: 12px; font-weight: 600; }
                QPushButton:hover { background-color: #1d4ed8; }
            """)
        else:
            self.lbl_mode_badge.setText("🌐 真实监听")
            self.lbl_mode_badge.setStyleSheet("""
                background-color: #1e3a8a; color: #bfdbfe; border: 1px solid #2563eb;
                border-radius: 4px; padding: 2px 6px; font-size: 11px; font-weight: bold;
            """)
            self.btn_toggle_mode.setText("🔄 切换为模拟仿真数据")
            self.btn_toggle_mode.setStyleSheet("""
                QPushButton { background-color: #059669; color: #ffffff; border: none; border-radius: 4px; padding: 5px 12px; font-size: 12px; font-weight: 600; }
                QPushButton:hover { background-color: #047857; }
            """)

    def _clear_cards(self):
        for card in self.cards:
            self.card_layout.removeWidget(card)
            card.deleteLater()
        self.cards.clear()
        self.empty_placeholder.show()
        self.question_count = 0
        self._update_stats_display()

    def _toggle_key_visibility(self):
        """切换 API Key 的明文/密文显示状态"""
        if self.txt_api_key.echoMode() == QLineEdit.EchoMode.Password:
            self.txt_api_key.setEchoMode(QLineEdit.EchoMode.Normal)
            self.btn_toggle_key_vis.setText("🙈")
        else:
            self.txt_api_key.setEchoMode(QLineEdit.EchoMode.Password)
            self.btn_toggle_key_vis.setText("👁️")

    def _on_save_config(self):
        """保存配置并动态生效"""
        new_url = self.txt_room_url.text().strip()
        new_key = self.txt_api_key.text().strip()

        # 简单规范化 URL
        if new_url and not (new_url.startswith("http://") or new_url.startswith("https://")):
            new_url = "https://" + new_url
            self.txt_room_url.setText(new_url)

        # 1. 保存到 config.py 文件并更新当前内存变量
        save_ok = config.save_config_to_file(new_url, new_key)

        # 2. 动态通知弹幕监听线程更新直播间地址
        self.danmu_thread.update_live_url(new_url)

        # 3. 动态通知 AI 引擎线程更新 API Key
        ai_ok, ai_msg = self.ai_worker.update_api_key(new_key)

        # 4. 更新界面状态与弹窗提示
        time_tag = datetime.datetime.now().strftime("%H:%M:%S")
        self.lbl_config_status.setText(f"✓ 已于 {time_tag} 保存并实时生效")
        self.lbl_config_status.setStyleSheet("color: #34d399; font-size: 11px; font-weight: bold;")
        self.lbl_status_msg.setText("✅ 配置已保存并实时生效")

        status_desc = "大模型 API 推理模式" if new_key else "本地智能话术模式 (免 Key)"
        file_desc = "config.py 已同步持久化" if save_ok else "config.py 写入警告 (内存已更新)"
        msg_detail = (
            f"✅ 配置已成功保存并实时生效！\n\n"
            f"• 直播间网址: {new_url or '(未配置)'}\n"
            f"• AI 回复模式: {status_desc}\n"
            f"• 状态提示: {ai_msg}\n"
            f"• 配置文件: {file_desc}"
        )
        QMessageBox.information(self, "配置已保存", msg_detail)

    def closeEvent(self, event):
        """窗口关闭时安全终止后台线程"""
        self.danmu_thread.stop()
        self.ai_worker.stop()
        event.accept()


# ==============================================================================
# 程序入口
# ==============================================================================
def main():
    # 开启高 DPI 缩放适配
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # 默认全局字体
    font = QFont("PingFang SC", 10)
    font.setStyleHint(QFont.StyleHint.SansSerif)
    app.setFont(font)

    window = TeleprompterWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
