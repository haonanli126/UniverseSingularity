# Grid World 环境指南（SimpleGridWorld v0）

## 状态空间

- 网格大小：10 × 10
- 每个格子一个整数编码：
  - 0: 空地
  - 1: 墙壁
  - 2: 钥匙（未拾取）
  - 3: 关闭的门
  - 4: 打开的门
  - 5: 目标点
  - 6: agent 当前位置
- 整个网格展平成一个长度为 100 的向量，dtype=float32。

## 动作空间

共 6 个离散动作（见 `GridAction` 枚举）：

0. UP：向上移动一格  
1. DOWN：向下移动一格  
2. LEFT：向左移动一格  
3. RIGHT：向右移动一格  
4. PICK_KEY：在钥匙格子时拾取钥匙  
5. OPEN_DOOR：在门相邻格子且已持有钥匙时开门  

## 奖励函数（v0）

- 每一步基础惩罚：-0.01
- 撞墙 / 关门：额外 -0.04
- 拾取钥匙成功：+0.5
- 开门成功：+0.5
- 到达目标：+1.0，并结束 episode
- 超过 max_steps 未完成：直接终止，标记为 truncated。

## 接口

环境遵守 `Environment` 接口：

- `reset() -> np.ndarray`
- `step(action: int) -> (next_state, reward, done, info)`
- `render(mode="ascii" | "pygame") -> None`
