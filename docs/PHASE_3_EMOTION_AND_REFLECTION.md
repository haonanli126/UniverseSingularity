# Universe Singularity · Phase 3 指南  
## 情绪感知 · 自我照顾 · 日终小结

> 本文档基于本地路径 `D:\UniverseSingularity`，默认环境为：
> - Windows + PowerShell
> - Python 3.11.9 + venv (`venv`)
> - 仓库：`haonanli126/UniverseSingularity`（main 分支）

Phase 3 的目标：  
在 Phase 0–2 的基础上，让数字胚胎**真正理解你的最近状态，并给出温柔的自我照顾建议**，形成一个可被每天使用的“小睡前仪式”。

---

## 1. Phase 3 能力总览

Phase 3 在 Phase 1–2 的基础上，新增了三个关键能力：

1. **自我照顾建议（Self-care Suggestion）**
   - 模块：`src/us_core/core/self_care.py`
   - 脚本：`scripts/self_care_today.py`
   - 根据最近几天的情绪曲线，给出：
     - 建议模式：`rest` / `balance` / `focus`
     - 一段适合直接阅读的中文建议

2. **日终小结（Daily Reflection）**
   - 模块：`src/us_core/core/daily_reflection.py`
   - 脚本：`scripts/daily_reflection.py`
   - 一条命令完成：
     1. 从感知事件写入长期情绪记忆
     2. 构建最近若干天的每日情绪
     3. 输出一周情绪小结文本
     4. 输出今日自我照顾建议

3. **每日循环 + 日终小结一键入口**
   - 脚本：`scripts/daily_cycle_with_reflection.py`
   - 在原有 `daily_cycle` 基础上，**自动追加一次日终小结**：
     - 完成任务/心跳/规划/TODO 导出
     - 再做一次情绪总结 + 自我照顾建议

---

## 2. 数据流回顾：Phase 1–3 情绪线整体结构

情绪相关的数据流大致如下：

1. **感知入口（Phase 1）**
   - CLI 心情打卡、速记、对话等全部写入：
     - `data/perception/events.jsonl`（`PerceptionEvent` 序列）
   - 相关脚本：
     - `scripts/perception_cli.py`
     - `dialog_cli.py`（会记录对话中的你的发言）

2. **感知 → 长期情绪记忆（Phase 2）**
   - 通过桥接模块，把有价值的情绪文本写入：
     - `data/memory/perception_long_term.jsonl`（`LongTermMemoryItem`）
   - 相关脚本：
     - `scripts/preview_perception_to_memory.py`（预览）
     - `scripts/ingest_perception_to_memory.py`（真正写入）

3. **长期情绪曲线 & 一周小结（Phase 2）**
   - 模块：
     - `src/us_core/core/mood.py`
     - `src/us_core/perception/long_term_view.py`
     - `src/us_core/core/mood_summary.py`
   - 脚本：
     - `scripts/show_long_term_mood.py`（按天查看情绪）
     - `scripts/weekly_mood_summary.py`（一周情绪小结）

4. **自我照顾 & 日终小结（Phase 3）**
   - `self_care.py`：根据最近几天的 `DailyMood` 给出自我照顾建议
   - `daily_reflection.py`：串联 ingest + 日视图 + 周小结 + 自我照顾
   - `daily_cycle_with_reflection.py`：把这一切挂到 `daily_cycle` 后

---

## 3. 自我照顾建议：`self_care_today.py`

### 3.1 模块与脚本位置

- 逻辑模块：
  - `src/us_core/core/self_care.py`
  - 核心结构：
    - `SelfCareSuggestion`
    - `build_self_care_suggestion(daily: List[DailyMood])`

- 命令行脚本：
  - `scripts/self_care_today.py`

### 3.2 用法示例

先确保进入项目根目录并激活 venv：

```powershell
cd D:\UniverseSingularity
.\venv\Scripts\Activate.ps1
然后执行：

python .\scripts\self_care_today.py --days 7


示例输出（示意）：

==============================================
 Universe Singularity · 今日自我照顾建议
==============================================

参考时间范围：2025-11-21 ~ 2025-11-22（共 2 天）
最近几天的平均情绪分：-0.89
建议模式：rest

这 2 天整体情绪是「略偏负面」，平均情绪分大约 -0.89。最近你承受的压力不小，今天可以适当给自己放点水：优先处理最重要的两三件小事，其它的先允许自己缓一缓，多补一点睡眠 / 喝水 / 简单走走，让神经系统有机会慢慢回到安全感里。

3.3 自我照顾模式（mode）

build_self_care_suggestion 会基于最近最多 3 天的 DailyMood，计算平均情绪分，并对应到三种模式：

rest：明显偏负面

建议整体降负、减少任务量、优先保证睡眠和恢复

balance：波动但可承受

建议在照顾自己和推进重要事情之间做平衡

focus：整体偏正面，状态不错

建议安排一些对你重要但略有挑战的任务

4. 日终小结：daily_reflection.py
4.1 作用概述

daily_reflection.py 把情绪线上的能力打包成一个日终复盘脚本：

从感知仓库写入新的长期情绪记忆

构建最近 N 天的 DailyMood

生成一段一周情绪小结（基于 WeeklyMoodSummary）

生成今日自我照顾建议（基于 SelfCareSuggestion）

4.2 用法示例
cd D:\UniverseSingularity
.\venv\Scripts\Activate.ps1

python .\scripts\daily_reflection.py --days 7 --ingest-limit 200


示例输出（精简版）：

==============================================
 Universe Singularity · 日终小结 (Phase 3-S02)
==============================================

本次从感知仓库写入长期情绪记忆：13 条
长期情绪文件：D:\UniverseSingularity\data\memory\perception_long_term.jsonl

【今日情绪概览】
- 今天（2025-11-23）暂时没有形成完整的情绪聚合记录。

【最近 2 天情绪曲线】
- 时间范围：2025-11-21 ~ 2025-11-22
  2025-11-21 | 略偏负面 | 平均情绪 -0.78 | 样本数 27
  2025-11-22 | 略偏负面 | 平均情绪 -1.00 | 样本数 12

【一周情绪小结】
从 2025-11-21 到 2025-11-22（共 2 天），整体情绪可以形容为：略偏负面。
...

【今日自我照顾建议】
- 建议模式：rest
- 参考天数：2

这 2 天整体情绪是「略偏负面」，平均情绪分大约 -0.89。最近你承受的压力不小，今天可以适当给自己放点水...

4.3 常用参数

--days

从最近往前数，纳入小结的最大天数（默认 7）

--ingest-limit

本次从感知事件写入长期情绪记忆的最大条数（默认 200）

--file

指定长期情绪文件路径（默认：data/memory/perception_long_term.jsonl）

5. 一键入口：daily_cycle_with_reflection.py
5.1 作用概述

这个脚本是 Phase 3-S03 的“集成入口”：

先运行原有 每日循环（daily_cycle.py）：

导入日记

收集长期记忆

从对话中收集任务

情绪概览

规划会话（Planning Session）

导出 todo_mood.md

状态面板 + 全局工作空间快照

再运行一次 日终小结（daily_reflection.py）：

ingest 新的情绪记忆

打印最近 N 天情绪曲线

打印一周情绪小结

给出今日自我照顾建议

5.2 用法示例
cd D:\UniverseSingularity
.\venv\Scripts\Activate.ps1

python .\scripts\daily_cycle_with_reflection.py


示例输出结构：

==============================================
 Universe Singularity · 每日循环 + 日终小结
 Phase 3-S03 - daily_cycle_with_reflection
==============================================

[1/2] 正在运行 daily_cycle ...
...（这里是原 daily_cycle 的输出）...

[2/2] 正在运行 daily_reflection（日终小结） ...

...（这里是 Phase 3-S02 的日终小结输出）...

[完成] 今日的每日循环 + 日终小结已执行。


可以把这条命令视为：

「今天我和宇宙奇点一起收个尾」的一键仪式。

6. 建议的日常使用节奏（可选）

下面是一种推荐使用方式，你可以根据状态自由调整：

6.1 白天 / 随时感知

当你有情绪波动、想留下一句心情：

python .\scripts\perception_cli.py --mode checkin


当你有一些零散想法、TODO 草稿：

python .\scripts\perception_cli.py --mode note


和数字胚胎聊天时，它会自动把你的发言写入感知仓：

python .\scripts\dialog_cli.py

6.2 睡前 / 日终复盘

如果只想做情绪复盘：

python .\scripts\daily_reflection.py --days 7 --ingest-limit 200


如果你想连带任务/规划一块收拾一下：

python .\scripts\daily_cycle_with_reflection.py

6.3 偶尔单独看看情绪历史

近几天情绪曲线：

python .\scripts\show_long_term_mood.py --days 7


一周情绪小结：

python .\scripts\weekly_mood_summary.py --days 7


仅看今日自我照顾建议：

python .\scripts\self_care_today.py --days 7

7. 测试与稳定性

Phase 3 完成后，项目总测试数为 77 项，全部通过：

cd D:\UniverseSingularity
.\venv\Scripts\Activate.ps1

python -m pytest
# 预期输出：77 passed in XXs


其中与 Phase 3 直接相关的测试包括：

tests/test_self_care.py

tests/test_long_term_mood_view.py

tests/test_weekly_mood_summary.py

tests/test_daily_reflection.py

tests/test_daily_cycle_with_reflection.py

如果在未来对情绪算法或脚本做修改，建议优先保证这些测试通过，再做功能扩展。