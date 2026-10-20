# 抖音直播 AI 实时提词器 (Live Teleprompter Pro)

专为主播设计的单向只读 AI 实时口播提词器桌面客户端。  
通过监听直播间粉丝公屏弹幕，自动过滤低价值水弹幕，结合电商背景知识库通过 AI 秒级生成 45 字以内的自然口播台词，以大字号高对比度置顶悬浮窗供主播看着念。

> **纯只读安全承诺**：本工具绝不包含任何自动发评论、模拟点击、账号登录或公屏回发互动功能，完全单向只读。

---

## 🌟 核心特性
1. **双模式弹幕源**：
   - **模拟模式（默认开启）**：每隔 2.5~4 秒自动生成仿真水弹幕与真实商品疑问，零成本本地调试。
   - **真实模式（Playwright 无头监听）**：实时抓取指定抖音直播间网页公屏聊天区 DOM 数据。
2. **二级初筛与智能问答**：
   - **第一级（本地规则）**：毫秒级过滤纯数字、少于3字及无效水弹幕，大幅降低 Token 消耗。
   - **第二级（AI 决策）**：基于注入的知识库生成主播口播回答；若非问题自动忽略。
   - **无 Key 智能降级**：未配置 API Key 时自动启用内置规则引擎，自动识别尺码/身高/体重/物流/运费险。
3. **专业主播 UI（PyQt6）**：
   - 深色高对比度（深黑底色 + 黄色高亮粉丝提问 + 大号白色口播台词）。
   - 窗口始终置顶、暂停自动滚动、一键模式切换、已念标记划线等。

---

## 🚀 快速启动指南

### 1. 环境准备
推荐使用 Python 3.10 ~ 3.13。

```bash
# 1. 创建虚拟环境 (可选)
python -m venv .venv

# 2. 激活虚拟环境
# macOS / Linux:
source .venv/bin/activate
# Windows:
.venv\Scripts\activate

# 3. 安装项目依赖
pip install -r requirements.txt

# 4. (如需真实网页监听模式) 安装 Playwright 浏览器内核
playwright install chromium
```

### 2. 运行程序
- **方式一（快捷脚本）**：在 Windows 上直接双击 `启动提词器.bat`（无需终端黑窗口，静默启动）。
- **方式二（命令行启动）**：
```bash
python main.py
```

### 3. 一键打包为 Windows 独立 EXE 程序
在 Windows 上解压后，**直接双击运行项目根目录下的 `build_exe.bat`**：
1. 脚本将自动安装 `pyinstaller` 打包工具；
2. 自动编译生成 `dist\抖音直播AI提词器\抖音直播AI提词器.exe`；
3. 将该文件夹放在任意位置，后续主播每次**直接双击 exe 即可秒开提词器**！

---

## ⚙️ 核心配置说明 (`config.py`)

在提词器界面顶部已支持**可视化修改并实时保存生效**；亦可在 `config.py` 中直接编辑：
- `MOCK_MODE`: 默认 `True`（模拟仿真），设为 `False` 即为真实监听。
- `DOUYIN_ROOM_URL`: 要监听的抖音直播间网址。
- `AI_API_KEY`: 大模型 API Key（留空则自动启用本地智能话术兜底）。
- `OPENAI_BASE_URL`: API 地址（支持 DeepSeek / 通义千问 / 月之暗面等兼容接口）。
- `SYSTEM_KNOWLEDGE_BASE`: 直播间知识库（商品卖点、面料工艺、尺码推荐对照表、物流发货时效、售后优惠等）。

---

## 📁 文件结构
```text
Live_Teleprompter_Pro/
├── README.md              # 项目说明文档
├── build_exe.bat          # Windows 一键打包 EXE 脚本
├── 启动提词器.bat          # Windows 一键静默启动快捷脚本
├── 一键安装环境并启动.bat  # Windows 首次一键安装依赖并运行
├── requirements.txt       # 依赖声明
├── config.py              # 全局配置与背景知识库 (支持动态持久化)
├── danmu_listener.py      # QThread 双模式弹幕监听器
├── ai_brain.py            # 本地规则初筛 + 大模型问答 + 本地降级
└── main.py                # PyQt6 独立置顶提词器界面
```
