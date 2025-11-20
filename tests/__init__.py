"""
让 pytest 在运行时能找到项目根目录下的包（config、src 等）。
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
