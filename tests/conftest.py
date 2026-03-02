import sys
from pathlib import Path

# 專案根目錄
_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))