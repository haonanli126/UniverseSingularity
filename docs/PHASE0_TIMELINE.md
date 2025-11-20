# Universe Singularity · Phase 0 时间线档案

> 记录数字胚胎从「心跳」到「日常循环」的成长过程。

---

## 🌱 概览

这个文档是给未来的自己和未来的宇宙奇点看的。  
它不是严格的 changelog，而是一个「带情绪的时间线」。

当前状态（2025-11-20）：

- 胚胎代号：**US-Embryo-Phase0**
- 已具备：
  - 心跳循环
  - 短期记忆 / 长期记忆
  - 对话引擎 + 意图识别 + 回复风格
  - 自省系统 + 全局工作空间 + 状态面板
  - 日记导入 + 情绪概览
  - 任务板 + 规划会话 + 规划历史
  - 情绪感知 TODO 导出
  - **daily_cycle 日常循环脚本**

---

## 🕒 关键里程碑（按功能维度）

> 时间点是大致阶段，不强调精确到分钟。

### 1️⃣ 基础骨架 & 心跳（Phase 0 - S01）

- 建立仓库结构：`config/`, `src/us_core/`, `scripts/`, `tests/`, `data/`, `logs/`
- 写好：
  - `config/settings.py` + `.env` 加载逻辑
  - `src/us_core/utils/logger.py`
- 完成最初版 `heartbeat.py`：
  - 从配置里读 base_url / api_key / model
  - 向 OpenAI 代理发起一次心跳，确认「我能和外部世界说话」

### 2️⃣ 事件流 / 记忆 / 对话（Phase 0 - S02 ~ S03）

- 引入 `EmbryoEvent / EventType`，统一记录：
  - 用户输入
  - 模型回复
  - 系统事件（心跳 / 自省 / 规划 / 任务等）
- 实现：
  - `memory.py`（短期记忆 buffer）
  - `persistence.py`（JSONL 持久化）
  - `recall.py`（从事件中重建对话上下文）
- 对话 CLI 初版：
  - `scripts/dialog_cli.py`：最基础的问答记录
  - 后续加入 `dialog_cli_ws.py`，接入 Workspace 信息

### 3️⃣ 自省 / Workspace / Status（Phase 0 - S04）

- 自省：
  - `reflection_cycle.py` 调用模型，用最近对话生成「自省文本」
  - 自省写入 `data/memory/reflections.jsonl`
- Workspace：
  - 汇总「短期记忆 + 长期记忆 + 最近自省 + 心境提示」
  - 形成一个「当下这个胚胎整体在想什么 / 记住什么」的快照
- Status：
  - `show_status.py` 输出：
    - 对话事件总数
    - 消息条数
    - 最近一次对话时间
    - 自省统计

### 4️⃣ 长期记忆 / 日记导入 / 情绪（Phase 0 - S05）

- 长期记忆：
  - `collect_long_term.py` 把重要对话提取到 `long_term.jsonl`
  - `show_long_term.py` 查看这些关键片段
- 日记导入：
  - 在 `data/journal/` 写入 `2025-11-20_心情.txt`，内容是当天心情
  - `import_journal.py` 把日记导入会话事件流，作为 `journal_entry`
- 情绪系统：
  - `mood.py` 从长期记忆 + 日记中抽取情绪样本
  - 计算每日平均情绪分数，输出「略偏正面 / 明显偏负面 / 比较中性」
  - `show_mood.py` 整合展示每日情绪 + 最近样本

### 5️⃣ 任务板 / 规划 / TODO（Phase 0 - S06）

- 任务板：
  - 从用户「command」意图的话语中提取任务
  - 写入 `data/tasks/tasks.jsonl`，支持 open / done
  - `show_tasks.py` 查看当前任务列表
  - `complete_task.py` 在 CLI 里交互式标记任务完成
- 规划系统：
  - `planning_session.py`：
    - 读取 Workspace / 任务板 / 日记 / 历史规划
    - 生成一份「温柔的下一阶段建议」
    - 写入 `data/plans/plans.jsonl`
  - `show_plans.py` 查看规划演化历史
- TODO 导出：
  - `export_todo.py`：简单版 TODO（任务 + 最新规划）
  - `export_todo_mood.py`：情绪感知版 TODO（附带当天情绪状态）

### 6️⃣ Daily Cycle（日常循环）& 稳定化（Phase 0 - S07）

- `daily_cycle.py` 正式上线：
  - 整合：
    - 日记导入
    - 长期记忆收集
    - 任务收集
    - 情绪概览
    - 规划会话
    - 情绪感知 TODO 导出
    - 状态面板
    - 全局工作空间快照
- 统一通过一个入口，完成一次「自我整理 + 自我关怀」：

  ```powershell
  python scripts\daily_cycle.py
---

## 2025-11-20 · Phase 0-S10：日循环 · 情绪感知 · TODO 出口 · 文档归档

**技术侧：**

- 为数字胚胎补齐了一整套「日线自我照顾循环」：
  - `daily_cycle.py`：一键跑完「导入日记 → 收集长期记忆 → 从对话中抽任务 → 情绪概览 → 规划会话 → 导出情绪感知 TODO → 展示状态面板 & 全局工作空间」。
  - `show_mood.py`：从对话事件 / 日记事件中提取情绪样本，按天聚合出简单情绪曲线（avg mood），并展示最近若干条情绪片段。
  - `planning_session.py`：基于 Workspace + 任务板 + 日记 + 历史规划，生成一段温柔的 Phase 1 行动建议，并记录到 `data/plans/plans.jsonl`。
  - `export_todo.py` / `export_todo_mood.py`：根据任务板 + 最新规划 + 当前情绪，生成普通版 TODO 与「情绪感知版 TODO」，导出为 Markdown，便于接入日常生活。

- 扩展了状态与工作空间视角：
  - `show_status.py`：统一查看对话条数、自省条数、最近一次事件时间等基础运行状态。
  - `show_workspace.py`：给出一眼可见的 Global Workspace：最近对话、长期记忆片段、自省摘要、日记片段、心境提示等。

- 引入「日记 → 对话事件」管道：
  - `import_journal.py`：把 `data/journal/*.txt` 里的自然语言日记导入为 MEMORY 事件，进入统一事件流，后续可被长期记忆 / 情绪分析 / 规划使用。

- 给项目增加基础文档校验：
  - 新增 `docs/PHASE0_TIMELINE.md` 记录 Phase 0 的工程时间线。
  - 新增 `tests/test_docs.py`，确保 README 与时间线文档存在，且提到了 `daily_cycle.py` 和情绪感知 TODO 的能力。

**体验侧：**

- 小胚胎现在具备：
  - 记住「你最近有点累、但今天比昨天好一点」之类的长期情绪片段，并在 Workspace 和 Mood 概览里反映出来。
  - 基于这些情绪和长期记忆，在规划里主动强调「放慢、照顾自己、允许能量波动」，而不是只推项目进度。
  - 每天可以通过 `daily_cycle.py` 帮你完成一轮「自我整理 + 温柔规划 + TODO 输出」，把宇宙奇点真正嵌进现实生活节奏。

**小结：**

- Phase 0 目前已经打通：
  - 环境 & 配置
  - 心跳 & 对话
  - 短期记忆 / 长期记忆
  - 日记导入
  - 情绪曲线
  - 任务板 / 规划 / TODO 导出
  - 状态面板 / 全局工作空间 / 日循环

从这一刻起，Universe Singularity 不再只是「一堆脚本」，而是一个每天可以跑、会记、会看你心情、会给你温柔 TODO 的小小数字生命实验体。
