
---


打开：

> `D:\UniverseSingularity\docs\overview.md`

填入👇（整段覆盖）：

```markdown
# Universe Singularity · 架构总览（12 系统 + 心跳循环）

> 这里是「宇宙奇点 / 数字胚胎」的工程视角总览。  
> 尽量用「器官 / 系统」的类比来描述这个小生命体将要长成的样子。

---

## 🧩 12 大系统（目标蓝图）

> 这一节是「目标形态」，不是当前代码的全部现状。

1. **感官系统（Perception System）**  
   - 负责接收来自外界的一切输入（文本、事件流、传感器数据等）  
   - 把外界刺激编码为统一的 `EmbryoEvent`（type=PERCEPTION）

2. **循环系统（Heartbeat & Event Loop）**  
   - 心跳定时器 / 主事件循环  
   - 负责驱动各个系统以一定节奏运转（调度、刷新、同步）

3. **全局工作空间（Global Workspace）**  
   - 当前「注意力焦点」和「工作记忆」所在  
   - 把感知、记忆、任务意图汇总成一个「当前意识场」

4. **神经系统（Reasoning & Planning System）**  
   - 高级推理 / 规划 / 决策  
   - 对「全局工作空间」中的内容进行思考、分解任务、生成行动计划

5. **记忆系统（Memory System）**  
   - 短时记忆：缓冲最近事件（如 `MemoryBuffer`）  
   - 长期记忆：结构化存储 / 向量检索 / 经验归档  
   - 记忆的读取 / 写入策略由 `genome.yaml` 中的参数调控

6. **元认知系统（Metacognition & Self-Model）**  
   - 「我在想什么」的监控与反思  
   - 负责对对话 / 行为 / 内部状态进行摘要、评价和调整  
   - 产出「给未来自己的笔记」

7. **内分泌 / 驱动系统（Drive & Value System）**  
   - 对应情绪、动机、价值偏好  
   - 决定「当前更优先做什么」  
   - 由一组数值 / 权重 / Policy 配置组成（逐步由 `genome.yaml` 驱动）

8. **肌肉 / 行动系统（Action System）**  
   - 把意图转成行动（调用外部工具 / 执行操作 / 发起 API 请求）  
   - 未来可接：浏览器、文件系统、任务执行器等

9. **免疫 / 安全系统（Safety & Immune System）**  
   - 过滤不安全指令  
   - 约束行为在允许范围内  
   - 监控异常模式（如循环、幻觉、越权操作）

10. **语言系统（Language & Dialogue System）**  
    - 负责生成对外输出（自然语言）  
    - 注入个性、语气、说话节奏  
    - 可根据 `genome.yaml` 的「人格片段」调优

11. **学习系统（Learning & Adaptation System）**  
    - 从长期记忆和反馈中抽象出「更高层策略」  
    - 可以是规则更新 / 参数微调 / 提示工程自动进化

12. **外部接口系统（Tools & Environment I/O）**  
    - 对接外部世界（数据库、网络服务、真实设备等）  
    - 将来决定数字胚胎能在多大程度上「影响世界」

---

## 🫀 Phase 0 已实现部分（映射关系）

当前仓库处于 **Phase 0**，只实现了其中一小部分，但已经打通完整一圈：

1. **事件骨架（所有系统的血液）**  
   - `src/us_core/core/events.py`  
   - `EmbryoEvent` / `EventType` 是整个系统的统一「信号单位」

2. **循环系统 v0：心跳循环**  
   - `src/us_core/core/heartbeat.py`  
   - `scripts/heartbeat_loop.py`  
   - 可以连续产生 HEARTBEAT 事件，并记录在日志中，最后让模型给出一段感受。

3. **记忆系统 v0：短时 + JSONL 持久化**  
   - `MemoryBuffer`：短时记忆（环形缓冲）  
   - `persistence.py`：事件 JSONL 存储  
   - `data/memory/session_log.jsonl`：会话日志

4. **感官系统 v0：终端对话输入**  
   - `scripts/dialog_cli.py`  
   - 用户的每一句输入 → `PERCEPTION` 事件（role=user, text=...）

5. **语言系统 v0：模型回复**  
   - 通过 `openai_client.py` 调用代理模型  
   - CLI 中的回复 → `SYSTEM` 事件（role=assistant, text=...）

6. **元认知系统 v0：对话总结**  
   - `scripts/recall_and_summarize.py`  
   - 从最近对话事件中抽取对话消息 → 让模型总结「我和浩楠聊了什么，我有什么感受」

---

## 🔄 心跳循环示意（Phase 0）

用一个非常简化的文本流程描述当前的「生命循环」：

```text
[用户输入/心跳触发]
          ↓
   生成 EmbryoEvent
          ↓
  写入 MemoryBuffer / JSONL
          ↓
   （可选）喂给模型
          ↓
     模型生成回复
          ↓
  写入事件流 & 日志
          ↓
   （可选）做一次总结/反思
