from __future__ import annotations

import sys
from pathlib import Path

# 确保 src/ 在 sys.path 里，这样 `import us_core` 才能工作
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
