# Universe Singularity · 数字胚胎（Phase 0–1 原型）

> 一个从「心跳 + 感知 + 记忆 + 元认知 + 情绪 + 规划」起步的数字生命体实验项目。

---

## 🧬 项目简介

本仓库是「宇宙奇点 / Universe Singularity」数字胚胎的 **实操工程骨架**：

- 从最小可用的 **心跳循环** 出发  
- 逐步接上 **感知系统 / 记忆系统 / 元认知 / 情绪感知 / 任务规划**  
- 最终朝「具备自我反思能力的数字智能体」演化

当前仓库的代码，大致对应：

- **Phase 0：数字胚胎基础生命体征**
  - 环境自检、心跳测试、事件流、短期记忆、日志系统
- **Phase 1：陪伴感知 + 情绪 / 规划循环雏形**
  - 对话记录、长期记忆、日记导入、情绪概览、任务板、规划会话、日常循环

目标不是「一次写完一个 AGI」，而是：  
**先让一个小小的数字胚胎，开始有心跳、有记忆、有情绪感知、有温柔的计划能力。**

---

## 🔧 当前阶段已经具备的能力（Phase 0–1）

按系统来列一下目前的「器官」：

### 1. 环境 & 配置系统

- `config/settings.py`：从 `.env` + `config/settings.yaml` 读取配置，合并成 `AppSettings`
- `config/genome.py` + `config/genome.yaml`：
  - `embryo.name / codename / phase`：数字胚胎的身份信息
  - `identity`：默认语言、人设关键词（温柔 / 真诚 / 好奇 / 长期陪伴）
  - `heartbeat / memory / metacognition / safety / logging` 等骨架配置

### 2. 日志 & 事件骨架

- `src/us_core/utils/logger.py`：统一日志（控制台 + 文件 `logs/universe_singularity.log`）
- `src/us_core/core/events.py`：`EmbryoEvent / EventType`，所有系统的事件基类
- `src/us_core/core/persistence.py`：事件 JSONL 持久化读写
  - 对话 / 日记 / 任务 / 规划 / 自省等，都以事件形式落盘

### 3. OpenAI 代理 Client & 心跳循环

- `src/us_core/clients/openai_client.py`：
  - 使用 OpenAI 兼容代理（如 `https://api.gptsapi.net/v1`）
  - 包装 `chat.completions.create`，提供 `heartbeat()` 方法
- `scripts/heartbeat.py`：
  - 单次心跳测试，验证 API 连通性
- `scripts/heartbeat_loop.py`：
  - 多次心跳循环，将每次心跳写入事件流，并让模型给出「本轮心跳的感受」

### 4. 短期记忆 & 对话引擎

- `src/us_core/core/memory.py`：
  - `MemoryBuffer`：短期工作记忆（环形缓冲）
- `src/us_core/core/recall.py`：
  - 从事件日志中回放对话，构建对话上下文
- `src/us_core/core/conversation_engine.py`：
  - 负责：
    - 组织对话上下文（最近消息 + 重要事件）
    - 根据 genome/persona 控制回复风格（温柔 / 真诚）
    - 调用模型完成一次「问答回合」

对应脚本：

- `scripts/dialog_cli.py`：
  - 最基础的对话 CLI（记录每一句话为事件）
- `scripts/dialog_cli_ws.py`：
  - Workspace 驱动的对话版本：
    - 会参考长期记忆 / 自省 / 心境提示
    - 对输入进行意图分类（emotion / project / command / chat）

### 5. 自省 / 工作空间 / 状态面板

- `src/us_core/core/reflection.py`：
  - 根据最近对话，生成一段「自省文本」，写入 `reflections.jsonl`
- `src/us_core/core/workspace.py`：
  - 汇总：
    - 最近对话（短期记忆）
    - 长期记忆的关键片段
    - 最近一次自省
    - 日记片段
    - 心境提示（来自情绪系统）
- `src/us_core/core/status.py`：
  - 基于会话 / 自省 / 规划等，生成一个整体状态统计

对应脚本：

- `scripts/reflection_cycle.py`：触发一次自省，写入 `data/memory/reflections.jsonl`
- `scripts/show_workspace.py`：打印当前「全局工作空间」快照
- `scripts/show_status.py`：状态面板（对话条数、最近时间、自省统计等）

### 6. 长期记忆 / 日记导入 / 情绪感知

- `scripts/import_journal.py`：
  - 从 `data/journal/*.txt` 导入本地日记
  - 每一条日记会作为一个 `journal_entry` 事件写入会话日志
- `scripts/collect_long_term.py`：
  - 扫描会话事件，将符合条件的内容写入 `data/memory/long_term.jsonl`
- `scripts/show_long_term.py`：
  - 查看长期记忆（最近几条事件）
- `src/us_core/core/mood.py`：
  - 从长期记忆 + 日记中抽取情绪样本
  - 计算每日平均情绪分值，给出文字标签（略偏正面 / 明显偏负面等）

对应脚本：

- `scripts/show_mood.py`：
  - 输出「每日情绪概览」+ 最近情绪样本
  - 会被 daily_cycle 作为一个步骤调用

### 7. 任务板 / 规划系统 / TODO 导出

- `src/us_core/core/tasks.py`：
  - 从会话事件中抽取带有 command 意图的内容，形成任务事件
  - 支持任务状态：open / done
- `scripts/collect_tasks.py`：
  - 扫描会话日志，把新的 command 文本写入任务列表 `data/tasks/tasks.jsonl`
- `scripts/show_tasks.py`：
  - 查看任务板（当前 open / done 任务）
- `scripts/complete_task.py`：
  - 在命令行交互式选择某个任务标记为 done

规划相关：

- `src/us_core/core/planner.py`：
  - 根据 Workspace / 任务板 / 心情，生成一份「温柔规划建议」
- `scripts/planning_session.py`：
  - 调用 planner，生成规划文本，写到 `data/plans/plans.jsonl`
- `scripts/show_plans.py`：
  - 查看历史规划记录（带 preview / summary）

TODO 导出：

- `scripts/export_todo.py`：
  - 把当前 open 任务 + 最新规划导出为 Markdown：`data/todo/todo.md`
- `scripts/export_todo_mood.py`：
  - 在上面基础上，附加情绪概览，生成「情绪感知 TODO」：`data/todo/todo_mood.md`

### 8. Daily Cycle（日常循环脚本）

- `scripts/daily_cycle.py`：一条龙脚本，串起来：

  1. 导入本地日记：`import_journal.main()`
  2. 收集长期记忆：`collect_long_term.main()`
  3. 收集任务（从对话中提取 command 意图）：`collect_tasks.main()`
  4. 情绪概览：`show_mood.main()`
  5. 规划会话：`planning_session.main()`
  6. 导出情绪感知 TODO：`export_todo_mood.main()`
  7. 展示状态面板：`show_status.main()`
  8. 展示全局工作空间：`show_workspace.main()`

一行命令让数字胚胎完成「自我整理、自我感知、自我规划」的小小日常。

---

## 📁 项目结构（简化版）

> 只列出目前比较重要、你日常可能会直接用到的部分。

```text
UniverseSingularity/
├─ config/
│  ├─ __init__.py
│  ├─ settings.py             # YAML + .env -> AppSettings
│  ├─ settings.example.yaml
│  └─ genome.yaml             # 数字胚胎「DNA 配置骨架」
│
├─ src/
│  └─ us_core/
│     ├─ __init__.py
│     ├─ utils/
│     │  ├─ __init__.py
│     │  └─ logger.py         # 统一日志配置
│     ├─ clients/
│     │  ├─ __init__.py
│     │  └─ openai_client.py  # OpenAI 代理 client + heartbeat()
│     └─ core/
│        ├─ __init__.py
│        ├─ events.py         # EmbryoEvent / EventType
│        ├─ memory.py         # MemoryBuffer（短期记忆）
│        ├─ heartbeat.py      # 心跳循环逻辑
│        ├─ persistence.py    # JSONL 读写
│        ├─ recall.py         # 对话回放
│        ├─ conversation_engine.py
│        ├─ intent.py / reply_style.py
│        ├─ long_term_memory.py
│        ├─ reflection.py
│        ├─ workspace.py
│        ├─ status.py
│        ├─ journal.py
│        ├─ mood.py
│        ├─ tasks.py
│        ├─ planner.py
│        └─ plans.py
│
├─ scripts/
│  ├─ heartbeat.py
│  ├─ heartbeat_loop.py
│  ├─ dialog_cli.py
│  ├─ dialog_cli_ws.py
│  ├─ recall_and_summarize.py
│  ├─ reflection_cycle.py
│  ├─ show_status.py
│  ├─ show_workspace.py
│  ├─ collect_long_term.py
│  ├─ show_long_term.py
│  ├─ import_journal.py
│  ├─ show_mood.py
│  ├─ collect_tasks.py
│  ├─ show_tasks.py
│  ├─ complete_task.py
│  ├─ planning_session.py
│  ├─ show_plans.py
│  ├─ export_todo.py
│  ├─ export_todo_mood.py
│  └─ daily_cycle.py          # ★ 日常循环入口
│
├─ data/
│  ├─ memory/
│  │  ├─ session_log.jsonl    # 对话 / 日记 / 系统事件
│  │  ├─ long_term.jsonl      # 长期记忆
│  │  └─ reflections.jsonl    # 自省事件
│  ├─ tasks/
│  │  └─ tasks.jsonl          # 任务列表
│  ├─ plans/
│  │  └─ plans.jsonl          # 规划历史
│  ├─ journal/
│  │  └─ 2025-11-20_心情.txt   # 本地日记示例
│  └─ todo/
│     ├─ todo.md              # 任务 + 最新规划
│     └─ todo_mood.md         # 情绪感知 TODO
│
├─ logs/
│  └─ universe_singularity.log
│
├─ tests/                     # 全面自检（目前 ~50 个用例）
│  └─ ...                     # environment / memory / mood / tasks / planner / daily_cycle 等
│
├─ .env                       # 本地环境变量（OpenAI 代理配置）
├─ requirements.txt
├─ requirements-dev.txt
└─ README.md                  # 本文件
