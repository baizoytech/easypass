from pathlib import Path
import sqlite3

ROOT_DIR = Path(__file__).resolve().parents[2]
DB_PATH = ROOT_DIR / 'data' / 'passwords.db'
MODELS_PATH = ROOT_DIR / 'src' / 'models.py'

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = cursor.fetchall()

print("=== 数据库中所有表 ===")
for t in tables:
    name = t[0]
    cursor.execute(f"SELECT COUNT(*) FROM [{name}]")
    count = cursor.fetchone()[0]
    cursor.execute(f"PRAGMA table_info([{name}])")
    cols = [c[1] for c in cursor.fetchall()]
    print(f"  {name}: {count} 行 | 字段: {', '.join(cols)}")

# Check which tables are used in src/models.py
print("\n=== src/models.py 中引用的表 ===")
with open(MODELS_PATH, 'r', encoding='utf-8') as f:
    models = f.read()

for t in tables:
    name = t[0]
    used = name in models
    print(f"  {name}: {'使用中' if used else '未使用'}")

conn.close()
