import sys
from pathlib import Path
import pytest

# 專案根目錄
_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

# 匯入 app
from app import app  # noqa: E402


@pytest.fixture
def client():
    app.config.update({"TESTING": True, "SECRET_KEY": "test-secret-key"})
    with app.test_client() as client:
        yield client
