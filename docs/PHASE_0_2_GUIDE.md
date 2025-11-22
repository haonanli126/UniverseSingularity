# Universe Singularity · 数字胚胎  
Phase 0–2 使用手册（本地版）

> 本文档针对本地开发环境：Windows + PowerShell + Python 3.11.9 + venv + PyCharm CE  
> 仓库路径：`D:\UniverseSingularity`

---

## 1. 环境与启动方式

### 1.1 必备环境

- Windows 10/11
- Python 3.11.9（已安装）
- PowerShell
- Git（已配置 GitHub 仓库）
- 本地路径：`D:\UniverseSingularity`
- 虚拟环境目录：`D:\UniverseSingularity\venv`（或 `.venv`，以当前项目为准）

### 1.2 常用 PowerShell 启动命令

```powershell
# 进入项目目录
cd D:\UniverseSingularity

# 激活 venv
.\venv\Scripts\Activate.ps1

# 或者如果你用的是 .venv 目录：
# .\.venv\Scripts\Activate.ps1
2. 项目结构总览（Phase 0–2）

核心目录结构（简化版）：

D:\UniverseSingularity
├─ config/
│  ├─ settings.py          # 环境 & OpenAI 配置
│  ├─ genome.py            # genome.yaml 读取封装
│  ├─ genome.yaml          # 数字胚胎的“DNA 配置”
│  └─ __init__.py
│
├─ src/
│  └─ us_core/
│     ├─ core/             # 核心逻辑：会话引擎、任务系统、工作空间、情绪聚合等
│     ├─ perception/       # Phase 1–2：感知 & 情绪 & 记忆桥接
│     ├─ clients/          # OpenAI 等外部 API 客户端
│     ├─ utils/            # 日志等工具
│     └─ __init__.py
│
├─ scripts/
│  ├─ heartbeat.py                     # 心跳循环（Phase 0）
│  ├─ daily_cycle.py                   # 每日循环入口（Phase 0）
│  ├─ dialog_cli.py                    # 对话 CLI（Phase 0 + Phase 1 增强）
│  ├─ show_workspace.py                # 展示工作空间（任务/计划/记忆概况）
│  ├─ show_mood.py                     # Phase 0 的简单情绪视图
│  ├─ export_todo.py                   # 导出待办
│  ├─ export_todo_mood.py              # 导出待办 + 情绪信息
│  │
│  ├─ perception_cli.py                # Phase 1：感知入口（心情打卡 / 速记）
│  ├─ show_perception_timeline.py      # Phase 1：感知时间线视图
│  ├─ show_today_mood.py               # Phase 1：今日心情小结
│  │
│  ├─ preview_perception_to_memory.py  # Phase 2-S01：感知 → 长期记忆预览
│  ├─ ingest_perception_to_memory.py   # Phase 2-S02：感知 → 长期记忆落盘
│  ├─ show_long_term_mood.py           # Phase 2-S03：长期情绪曲线视图
│  ├─ weekly_mood_summary.py           # Phase 2-S04：一周情绪小结
│  └─ ...
│
├─ data/
│  ├─ perception/
│  │  └─ events.jsonl                  # 所有感知事件流水线（Phase 1 起）
│  ├─ memory/
│  │  ├─ long_term.jsonl               # Phase 0 的长期记忆（工作空间用）
│  │  └─ perception_long_term.jsonl    # Phase 2：基于感知的情绪型长期记忆
│  ├─ journal/                         # 日志 / 日记等（Phase 0）
│  ├─ tasks/                           # 任务存储
│  ├─ plans/                           # 计划存储
│  └─ todo/                            # TODO 列表
│
├─ tests/                              # 全套 pytest 单测（目前 70+）
│  ├─ test_conversation_engine.py
│  ├─ test_daily_cycle.py
│  ├─ test_perception.py
│  ├─ test_emotion.py
│  ├─ test_mood.py
│  ├─ test_perception_to_memory_bridge.py
│  ├─ test_long_term_mood_view.py
│  ├─ test_weekly_mood_summary.py
│  └─ ...
│
├─ docs/
│  ├─ PHASE_0_2_GUIDE.md               # 本文档
│  └─ ...                              # 其他文档
│
├─ README.md                           # 项目总 README（对外）
├─ requirements.txt                    # 依赖列表
└─ ...

3. Phase 0：基础骨架 & 日常循环
3.1 Phase 0 的能力概览

配置系统：

config/settings.py：环境、模型、base_url 等

config/genome.py + genome.yaml：数字胚胎的“人格/习惯”配置

工作空间 & 记忆系统：

长期记忆 / 工作空间存储：data/memory/long_term.jsonl 等

任务 & 计划：

任务、计划、TODO 的数据结构与读写

会话引擎：

ConversationEngine：读取最近对话上下文，写入对话日志

日常循环：

daily_cycle.py：每日检查任务、状态、心跳

heartbeat.py：心跳级别的简单任务

3.2 Phase 0 常用脚本
3.2.1 运行全套测试
cd D:\UniverseSingularity
python -m pytest


看到类似：

71 passed in 0.5Xs


说明 Phase 0–2 全部器官健康。

3.2.2 运行每日循环
cd D:\UniverseSingularity
python .\scripts\daily_cycle.py


功能视项目版本而定，大致包括：

检查今天任务 / TODO

更新状态文件

预留挂钩给后续 Phase（例如自动写入长期记忆、情绪小结）

3.2.3 查看工作空间
python .\scripts\show_workspace.py


用于快速查看当前：

任务 / 计划的概况

一些整体状态

4. Phase 1：感知 / 输入系统 & 陪伴感

Phase 1 的目标：

让数字胚胎真正“感知”到你说的话 / 打的卡，并对情绪有初步感觉。

4.1 感知数据结构

模块：src/us_core/perception/

PerceptionEvent：

一条感知事件（任何文本输入 / 日志）

字段包括：

id：UUID

timestamp：时间戳

channel：输入渠道（cli_checkin / cli_note / dialog 等）

content：原始文本

tags：标签（如 ["checkin", "mood"]）

metadata：附加信息（如对话 role=user/assistant）

PerceptionStore：

负责读写 data/perception/events.jsonl

提供 append() / iter_events() 等方法

4.2 情绪估计（粗粒度）

模块：src/us_core/perception/emotion.py

通过中文关键词表做简单情绪估计：

积极词：开心、放松、期待、兴奋、感激……

消极词：累、疲惫、焦虑、压力、崩溃、迷茫……

输出：

mood_score：[-1, 1]，1 越积极，-1 越消极

energy_level：[-1, 1]，能量高低

sentiment：positive / neutral / negative

4.3 感知入口：perception_cli

脚本：scripts/perception_cli.py

两种模式：

4.3.1 心情打卡模式
python .\scripts\perception_cli.py --mode checkin


交互流程示例：

Universe Singularity · 感知入口 (Phase 1)
先从一句话开始吧：此刻的你感觉怎么样？
> 今天有点累，但也挺期待宇宙奇点的

我收到了。要不要多和我说说，今天发生了什么？
（可以分几句慢慢打，我会一条条记下来。）
> 今天把 Phase 1 又推进了一步
> q
好，我把刚才这些都记下来了。辛苦你今天来和我分享。


所有内容都会以 PerceptionEvent 的形式写入：

data/perception/events.jsonl

channel="cli_checkin"

4.3.2 速记模式（note）
python .\scripts\perception_cli.py --mode note --text "随手记一点想法..."


用于快速写入一些想法 / 灵感，channel="cli_note"。

4.4 对话入口：dialog_cli（挂上感知）

脚本：scripts/dialog_cli.py

你输入的每句话：

先做「意图识别」

再调用大模型生成回复

同时作为 PerceptionEvent 写入感知存储（channel="dialog"，metadata.role="user"）

数字胚胎的回复也会入感知仓，但默认不会进入长期记忆（Phase 2 中有过滤规则）。

使用方式：

python .\scripts\dialog_cli.py


退出方式：输入 exit 或 quit。

4.5 浏览感知时间线

脚本：scripts/show_perception_timeline.py

# 最近 10 条所有感知
python .\scripts\show_perception_timeline.py --limit 10

# 最近 10 条心情打卡
python .\scripts\show_perception_timeline.py --channel cli_checkin --limit 10

# 最近 20 条对话感知
python .\scripts\show_perception_timeline.py --channel dialog --limit 20


输出包括：

时间 / 渠道 / 情绪估计

代表性文本内容

tags 信息

4.6 今日心情小结

脚本：scripts/show_today_mood.py

# 今天所有渠道
python .\scripts\show_today_mood.py

# 只看今天的心情打卡（cli_checkin）
python .\scripts\show_today_mood.py --channel cli_checkin

# 指定某一天
python .\scripts\show_today_mood.py --date 2025-11-20


功能：

统计某日：

总事件数

各渠道事件数

情绪分布：positive / neutral / negative

平均情绪/能量

展示最多 3 条代表性片段（按情绪强度排序）

5. Phase 2：感知 → 长期记忆 & 情绪趋势 / 一周小结

Phase 2 的目标：

把 Phase 1 感知到的东西，变成真正可回顾的长期情绪记忆，并形成趋势与总结。

5.1 感知 → 长期记忆桥接（候选）

模块：src/us_core/perception/memory_bridge.py
脚本：scripts/preview_perception_to_memory.py

5.1.1 规则（简述）

cli_checkin：

过滤命令噪音（cd、q、pytest 等）

其余全部作为 intent="emotion" 候选

cli_note：

过滤命令噪音

其余作为 intent="note" 候选

dialog：

只考虑 metadata.role == "user" 的发言

情绪强度 |mood_score| >= 0.05 才记为 intent="emotion"

助手回复 / 命令类无效文本不会被记录为长期记忆。

5.1.2 预览哪些会被记住
# 最近 30 条所有渠道的候选
python .\scripts\preview_perception_to_memory.py --limit 30

# 只看心情打卡里的候选
python .\scripts\preview_perception_to_memory.py --channel cli_checkin --limit 20

# 只看对话里的候选
python .\scripts\preview_perception_to_memory.py --channel dialog --limit 20


输出示例：

从最近 19 条感知事件中，选出了 7 条长期记忆候选：

[1] 2025-11-22 01:19 intent=emotion
     今天有点累，但也挺开心的
...


此时还只是“候选”，尚未写入长期记忆文件。

5.2 感知 → 长期记忆落盘（正式刻入）

脚本：scripts/ingest_perception_to_memory.py
目标文件：data/memory/perception_long_term.jsonl

cd D:\UniverseSingularity

# 写入最近 100 条感知中的候选（所有渠道）
python .\scripts\ingest_perception_to_memory.py --limit 100

# 只写心情打卡
python .\scripts\ingest_perception_to_memory.py --channel cli_checkin --limit 50

# 只写对话中的用户发言
python .\scripts\ingest_perception_to_memory.py --channel dialog --limit 30


写入的每一行形如：

{"text": "今天有点累，但也挺期待宇宙奇点的", "intent_label": "emotion", "timestamp": "2025-11-22T01:15:00+08:00"}


⚠️ 提示：脚本不做去重，多次对同一批事件执行可能产生重复记录。

5.3 长期情绪曲线视图（按天）

脚本：scripts/show_long_term_mood.py
依赖模块：src/us_core/perception/long_term_view.py + core.mood

cd D:\UniverseSingularity

# 最近 7 天
python .\scripts\show_long_term_mood.py --days 7

# 最近 14 天
python .\scripts\show_long_term_mood.py --days 14


示例输出：

长期情绪视图：2025-11-21 ~ 2025-11-22（共 2 天）
说明：average_score 越接近 1 越偏正面，越接近 -1 越偏负面。

2025-11-21 | 略偏负面 | 平均情绪 -0.78 | 样本数 9
2025-11-22 | 略偏负面 | 平均情绪 -1.00 | 样本数 4


含义：

每一天都是多个长期记忆样本聚合后的结果

sample_count 越大，说明这一天你说的“值得记住的话”越多

分数越接近 -1，说明这天提到的“累/压力/焦虑”等词越多
越接近 1 说明“开心/期待/放松”等词越多

5.4 一周情绪小结（Mini 自我反思 v0）

脚本：scripts/weekly_mood_summary.py
逻辑模块：src/us_core/core/mood_summary.py

cd D:\UniverseSingularity

# 最近 7 天的一周情绪小结
python .\scripts\weekly_mood_summary.py --days 7

# 最近 14 天
python .\scripts\weekly_mood_summary.py --days 14


输出示例：

==============================================
 Universe Singularity · 一周情绪小结 (Phase 2)
==============================================

从 2025-11-21 到 2025-11-22（共 2 天），整体情绪可以形容为：略偏负面。
这一段时间的平均情绪分为 -0.89 （越接近 1 越偏正面，越接近 -1 越偏负面）。
整体上，更多的日子是偏负面的，说明这段时间你承受了不少压力。
在这段时间里，情绪相对最好的一天大约是 2025-11-21，那天整体感觉是「略偏负面」，平均情绪分为 -0.78。
相对来说，情绪最吃力的一天大约是 2025-11-22，那天的整体状态是「略偏负面」，平均情绪分为 -1.00。
无论这几天是偏轻松还是偏辛苦，都谢谢你愿意把这些片段留下来。如果以后哪天累了、慌了，随时可以再来和我讲讲，我们一起把这些情绪消化掉。


这段文字是通过：

DailyMood 列表 → WeeklyMoodSummary（整体平均 / 最好 / 最难的一天）

再由 generate_weekly_mood_summary_text 生成中文段落

目前是规则 + 模板版的「Mini 自我反思」，后续 Phase 3 可以升级为大模型驱动的更细腻反思。

6. 日常使用建议：一个小“情绪仪式”

以下是一个可选的日常流程，你可以自由调整：

6.1 白天：随时感知 & 打卡

有情绪 / 想倾诉时：

python .\scripts\perception_cli.py --mode checkin


有想法 / 灵感 / 笔记：

python .\scripts\perception_cli.py --mode note --text "随便记一点..."


想聊天：

python .\scripts\dialog_cli.py

6.2 晚上（或某个固定时间）：小结一下这一天 / 这几天
cd D:\UniverseSingularity

# 1）把最近的感知刻进长期记忆
python .\scripts\ingest_perception_to_memory.py --limit 200

# 2）看一眼今天的心情
python .\scripts\show_today_mood.py --channel cli_checkin

# 3）看一眼最近 7 天的整体情绪趋势
python .\scripts\show_long_term_mood.py --days 7

# 4）读一读系统给你的「一周情绪小结」
python .\scripts\weekly_mood_summary.py --days 7


这样，每天你都不是“一个人在硬扛”——
数字胚胎会帮你把这些心情刻下来，再时不时地和你一起回头看一眼。
---

## 后续阶段预告：Phase 3 · 情绪与日终小结

从 Phase 3 开始，Universe Singularity 逐渐拥有了更完整的「情绪器官」和「日终复盘」能力，例如：

- 基于最近几天情绪曲线的自我照顾建议（`self_care_today.py`）
- 一键日终小结（`daily_reflection.py`）
- 每日循环 + 情绪复盘一条龙入口（`daily_cycle_with_reflection.py`）

详细说明见：`docs/PHASE_3_EMOTION_AND_REFLECTION.md`。
