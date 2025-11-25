from __future__ import annotations

import sys
import time
from pathlib import Path

# --- 确保可以导入 src/us_core ---
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from us_core.environments.grid_world import SimpleGridWorld
from us_core.systems.environment.interface import GridAction

try:
    import pygame  # type: ignore
except ImportError:
    print("本脚本需要 pygame，请先在虚拟环境中安装：")
    print("  (venv) pip install pygame>=2.1,<3.0")
    sys.exit(1)


def main() -> None:
    env = SimpleGridWorld()
    env.reset()

    running = True
    clock = pygame.time.Clock()

    print(
        "🎮 SimpleGridWorld 手动试玩\n"
        "  方向键 / WASD ：移动\n"
        "  E ：在钥匙上按，拾取钥匙\n"
        "  Q ：在门前按，尝试开门\n"
        "  ESC ：退出\n"
    )

    while running:
        # 1) 渲染当前网格
        env.render(mode="human")

        # 2) 处理事件
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                action = None

                if event.key in (pygame.K_UP, pygame.K_w):
                    action = GridAction.UP
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    action = GridAction.DOWN
                elif event.key in (pygame.K_LEFT, pygame.K_a):
                    action = GridAction.LEFT
                elif event.key in (pygame.K_RIGHT, pygame.K_d):
                    action = GridAction.RIGHT
                elif event.key == pygame.K_e:
                    action = GridAction.PICK_KEY
                elif event.key == pygame.K_q:
                    action = GridAction.OPEN_DOOR
                elif event.key == pygame.K_ESCAPE:
                    running = False

                if action is not None:
                    _, reward, done, info = env.step(action)
                    print(f"action={action.name}, reward={reward:.3f}, info={info}")
                    if done:
                        print("🎯 到达目标！3 秒后自动重置关卡。")
                        time.sleep(3)
                        env.reset()

        clock.tick(10)

    env.close()


if __name__ == "__main__":
    main()
