# -*- coding: utf-8 -*-
"""将国家种子同步到本地数据库。"""

from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT_DIR))

from src import models
from src.config import DB_PATH

if DB_PATH.exists():
    conn = models.get_db()
    try:
        models.sync_countries(conn)
        conn.commit()
    finally:
        conn.close()
    print("国家种子同步完成。")
else:
    print("未找到数据库：", DB_PATH)
