"""数据库模型与初始化。
SQLite 本地数据库，使用逻辑删除。
层级: 国家(countries) -> 公司(companies) -> 网站/应用(websites) -> 账号(accounts)
新增: 启动时同步基础种子数据。
"""

import os
import sqlite3
from datetime import datetime

from .config import DB_PATH
from .seed_data import COMPANY_SEED_ROWS, COUNTRY_SEED_ROWS


def get_db():
    """获取数据库连接。"""
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def sync_countries(conn):
    """将国家种子同步到数据库。"""
    cursor = conn.cursor()

    for order, (name, code) in enumerate(COUNTRY_SEED_ROWS, start=1):
        cursor.execute(
            """INSERT OR IGNORE INTO countries (name, code, sort_order, created_at, updated_at)
               VALUES (?, ?, ?, datetime('now','localtime'), datetime('now','localtime'))""",
            (name, code, order),
        )
        cursor.execute(
            """UPDATE countries
               SET name = ?, sort_order = ?, is_deleted = 0, updated_at = datetime('now','localtime')
               WHERE code = ?""",
            (name, order, code),
        )


def init_db():
    """初始化数据库，并同步基础种子数据。"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    print("[DB] 正在初始化数据库...")

    if os.path.exists(DB_PATH):
        try:
            test_conn = sqlite3.connect(DB_PATH)
            test_conn.execute("SELECT count(*) FROM sqlite_master")
            test_conn.close()
        except Exception:
            import logging
            logging.warning("数据库文件损坏，正在重建...")
            try:
                os.remove(DB_PATH)
            except Exception:
                pass

    conn = get_db()
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS countries (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL,
            code        TEXT NOT NULL UNIQUE,
            sort_order  INTEGER DEFAULT 0,
            is_deleted  INTEGER DEFAULT 0,
            created_at  TEXT DEFAULT (datetime('now','localtime')),
            updated_at  TEXT DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS companies (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            name                TEXT NOT NULL,
            country_id          INTEGER NOT NULL,
            description         TEXT DEFAULT '',
            icon                TEXT DEFAULT '',
            is_template         INTEGER DEFAULT 0,
            sort_order          INTEGER DEFAULT 0,
            is_hidden           INTEGER DEFAULT 0,
            is_deleted          INTEGER DEFAULT 0,
            created_at          TEXT DEFAULT (datetime('now','localtime')),
            updated_at          TEXT DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (country_id) REFERENCES countries(id)
        );

        CREATE TABLE IF NOT EXISTS websites (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            name                TEXT NOT NULL,
            url                 TEXT DEFAULT '',
            company_id          INTEGER NOT NULL,
            type                TEXT NOT NULL DEFAULT 'web',
            description         TEXT DEFAULT '',
            icon                TEXT DEFAULT '',
            is_template         INTEGER DEFAULT 0,
            sort_order          INTEGER DEFAULT 0,
            is_hidden           INTEGER DEFAULT 0,
            is_deleted          INTEGER DEFAULT 0,
            created_at          TEXT DEFAULT (datetime('now','localtime')),
            updated_at          TEXT DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (company_id) REFERENCES companies(id)
        );

        CREATE TABLE IF NOT EXISTS accounts (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            website_id      INTEGER NOT NULL,
            account_name    TEXT NOT NULL,
            password_enc    TEXT NOT NULL,
            password_salt   TEXT NOT NULL,
            status          TEXT NOT NULL DEFAULT 'active',
            phone           TEXT DEFAULT '',
            email           TEXT DEFAULT '',
            description     TEXT DEFAULT '',
            registered_at   TEXT DEFAULT '',
            is_deleted      INTEGER DEFAULT 0,
            created_at      TEXT DEFAULT (datetime('now','localtime')),
            updated_at      TEXT DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (website_id) REFERENCES websites(id)
        );

        CREATE TABLE IF NOT EXISTS master_key (
            id          INTEGER PRIMARY KEY CHECK (id = 1),
            key_hash    TEXT NOT NULL,
            created_at  TEXT DEFAULT (datetime('now','localtime')),
            updated_at  TEXT DEFAULT (datetime('now','localtime'))
        );
    """)

    sync_countries(conn)

    conn.commit()
    conn.close()
    print("[DB] 数据库初始化完成。")

    seed_companies()


def seed_companies():
    """同步初始公司数据，并合并旧库里同名同国家的重复公司。"""
    if not COMPANY_SEED_ROWS:
        print("  [SEED] 未配置公司种子数据")
        return

    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()

        now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        country_ids = {
            row["code"]: row["id"]
            for row in cursor.execute(
                "SELECT id, code FROM countries WHERE is_deleted = 0"
            ).fetchall()
        }

        inserted = 0
        updated = 0
        merged = 0

        print(f"  [SEED] 正在同步 {len(COMPANY_SEED_ROWS)} 条公司种子数据...")
        for order, row in enumerate(COMPANY_SEED_ROWS, start=1):
            country_id = country_ids.get(row.get("country_code"))
            if not country_id:
                raise RuntimeError(
                    f"公司种子中的国家代码无效: {row.get('country_code')!r}"
                )

            seed_id = row.get("id")
            seed_name = row.get("name", "") or ""
            seed_description = row.get("description", "") or ""
            seed_icon = row.get("icon", "") or ""

            exact_match = cursor.execute(
                "SELECT id FROM companies WHERE id = ?",
                (seed_id,),
            ).fetchone()
            candidate_rows = cursor.execute(
                """SELECT id
                   FROM companies
                   WHERE country_id = ?
                     AND LOWER(TRIM(name)) = LOWER(TRIM(?))
                   ORDER BY is_deleted ASC, is_template ASC, id ASC""",
                (country_id, seed_name),
            ).fetchall()

            target_id = None
            if exact_match:
                target_id = exact_match["id"]
            elif candidate_rows:
                target_id = candidate_rows[0]["id"]

            if target_id is None:
                cursor.execute(
                    """INSERT INTO companies (
                        id, name, country_id, description, icon,
                        is_template, sort_order, is_hidden, is_deleted, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, 0, ?, 0, 0, ?, ?)""",
                    (
                        seed_id,
                        seed_name,
                        country_id,
                        seed_description,
                        seed_icon,
                        order,
                        row.get("created_at") or now_str,
                        row.get("updated_at") or now_str,
                    ),
                )
                inserted += 1
                continue

            duplicate_ids = [r["id"] for r in candidate_rows if r["id"] != target_id]
            if duplicate_ids:
                placeholders = ",".join("?" for _ in duplicate_ids)
                cursor.execute(
                    f"""UPDATE websites
                        SET company_id = ?
                        WHERE company_id IN ({placeholders})
                          AND is_template = 0""",
                    (target_id, *duplicate_ids),
                )
                cursor.execute(
                    f"""UPDATE companies
                        SET is_deleted = 1,
                            is_hidden = 1,
                            updated_at = datetime('now','localtime')
                        WHERE id IN ({placeholders})""",
                    tuple(duplicate_ids),
                )
                merged += len(duplicate_ids)

            cursor.execute(
                """UPDATE companies
                   SET name = ?,
                       country_id = ?,
                       description = ?,
                       icon = ?,
                       is_template = 0,
                       sort_order = ?,
                       is_hidden = 0,
                       is_deleted = 0,
                       updated_at = datetime('now','localtime')
                   WHERE id = ?""",
                (seed_name, country_id, seed_description, seed_icon, order, target_id),
            )
            updated += 1

        conn.commit()

        active_company_count = cursor.execute(
            "SELECT COUNT(*) FROM companies WHERE is_template = 0 AND is_deleted = 0 AND is_hidden = 0"
        ).fetchone()[0]
        website_count = cursor.execute(
            "SELECT COUNT(*) FROM websites WHERE is_deleted = 0"
        ).fetchone()[0]
        print(f"  [SEED] 新增公司: {inserted}, 已同步: {updated}, 合并重复: {merged}")
        print(f"  [SEED] 当前有效公司数: {active_company_count}")
        print(f"  [SEED] 当前 websites 表行数: {website_count}")
    except Exception as e:
        if conn is not None:
            try:
                conn.rollback()
            except Exception:
                pass
        print(f"  [SEED] 公司种子同步失败: {e}")
        raise
    finally:
        if conn is not None:
            conn.close()



# ============ 数据操作函数 ============

# ---- 国家 ----

def get_countries():
    """获取所有未删除的国家列表。"""
    conn = get_db()
    rows = conn.execute(
        "SELECT id, name, code, sort_order FROM countries WHERE is_deleted = 0 ORDER BY sort_order, id"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_country(name, code, sort_order=0):
    """添加国家。"""
    conn = get_db()
    cursor = conn.execute(
        """INSERT OR IGNORE INTO countries (name, code, sort_order, created_at, updated_at)
           VALUES (?, ?, ?, datetime('now','localtime'), datetime('now','localtime'))""",
        (name, code, sort_order)
    )
    conn.commit()
    cid = cursor.lastrowid
    conn.close()
    return cid


# ---- 公司 ----

def get_companies_by_country(country_id=None):
    """获取公司列表，可按国家筛选（排除隐藏项）"""
    conn = get_db()
    sql = """
        SELECT co.id, co.name, co.country_id, co.icon,
               co.created_at, co.updated_at,
               c.name as country_name,
               (SELECT COUNT(*) FROM websites w WHERE w.company_id = co.id AND w.is_deleted = 0 AND w.is_hidden = 0) as website_count
        FROM companies co
        LEFT JOIN countries c ON co.country_id = c.id
        WHERE co.is_deleted = 0 AND co.is_hidden = 0 AND co.is_template = 0
    """
    params = []
    if country_id:
        sql += " AND co.country_id = ?"
        params.append(country_id)
    sql += " ORDER BY c.sort_order, co.name"
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_all_companies_by_country(country_id=None):
    """获取公司列表（包含隐藏项，用于管理）"""
    conn = get_db()
    sql = """
        SELECT co.id, co.name, co.country_id, co.icon,
               co.is_hidden, co.created_at, co.updated_at,
               c.name as country_name
        FROM companies co
        LEFT JOIN countries c ON co.country_id = c.id
        WHERE co.is_deleted = 0 AND co.is_template = 0
    """
    params = []
    if country_id:
        sql += " AND co.country_id = ?"
        params.append(country_id)
    sql += " ORDER BY c.sort_order, co.name"
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_company(company_id):
    """获取单个公司信息。"""
    conn = get_db()
    row = conn.execute(
        """SELECT co.id, co.name, co.country_id, co.description, co.icon,
                  co.created_at, co.updated_at, c.name as country_name
           FROM companies co
           LEFT JOIN countries c ON co.country_id = c.id
           WHERE co.id = ? AND co.is_deleted = 0 AND co.is_template = 0""",
        (company_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def create_company(data):
    """创建公司。"""
    conn = get_db()
    cursor = conn.execute(
        """INSERT INTO companies (name, country_id, icon, is_template, is_hidden, is_deleted, created_at, updated_at)
           VALUES (?, ?, ?, 0, 0, 0, datetime('now','localtime'), datetime('now','localtime'))""",
        (data['name'], data['country_id'], data.get('icon', ''))
    )
    conn.commit()
    cid = cursor.lastrowid
    conn.close()
    return cid


def update_company(company_id, data):
    """更新公司。"""
    conn = get_db()
    conn.execute(
        """UPDATE companies SET name=?, country_id=?, icon=?,
           updated_at=datetime('now','localtime') WHERE id=? AND is_deleted=0""",
        (data['name'], data['country_id'], data.get('icon', ''), company_id)
    )
    conn.commit()
    conn.close()


def delete_company(company_id):
    """逻辑删除公司及其下所有网站和账号。"""
    conn = get_db()
    conn.execute(
        "UPDATE companies SET is_deleted=1, updated_at=datetime('now','localtime') WHERE id=?",
        (company_id,)
    )
    conn.execute(
        "UPDATE websites SET is_deleted=1, updated_at=datetime('now','localtime') WHERE company_id=?",
        (company_id,)
    )
    conn.execute(
        """UPDATE accounts SET is_deleted=1, updated_at=datetime('now','localtime')
           WHERE website_id IN (SELECT id FROM websites WHERE company_id=?)""",
        (company_id,)
    )
    conn.commit()
    conn.close()


# ---- 网站/应用 ----

def get_websites_by_company(company_id=None, wtype=None):
    """获取网站/应用列表（排除隐藏项）。"""
    conn = get_db()
    sql = """
        SELECT w.id, w.name, w.url, w.company_id, w.type, w.icon,
               w.created_at, w.updated_at,
               co.name as company_name, co.country_id,
               c.name as country_name
        FROM websites w
        LEFT JOIN companies co ON w.company_id = co.id
        LEFT JOIN countries c ON co.country_id = c.id
        WHERE w.is_deleted = 0 AND w.is_hidden = 0 AND w.is_template = 0
          AND co.is_template = 0
    """
    params = []
    if company_id:
        sql += " AND w.company_id = ?"
        params.append(company_id)
    if wtype:
        sql += " AND w.type = ?"
        params.append(wtype)
    sql += " ORDER BY c.sort_order, co.name, w.name"
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_website(website_id):
    """获取单个网站信息。"""
    conn = get_db()
    row = conn.execute(
        """SELECT w.*, co.name as company_name, co.country_id,
                  c.name as country_name
           FROM websites w
           LEFT JOIN companies co ON w.company_id = co.id
           LEFT JOIN countries c ON co.country_id = c.id
           WHERE w.id = ? AND w.is_deleted = 0 AND w.is_template = 0""",
        (website_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def create_website(data):
    """创建网站。"""
    conn = get_db()
    cursor = conn.execute(
        """INSERT INTO websites (name, url, company_id, type, icon, is_template, is_hidden, is_deleted, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, 0, 0, 0, datetime('now','localtime'), datetime('now','localtime'))""",
        (data['name'], data.get('url', ''), data['company_id'],
         data.get('type', 'web'), data.get('icon', ''))
    )
    conn.commit()
    wid = cursor.lastrowid
    conn.close()
    return wid


def update_website(website_id, data):
    """更新网站。"""
    conn = get_db()
    conn.execute(
        """UPDATE websites SET name=?, url=?, company_id=?, type=?, icon=?,
           updated_at=datetime('now','localtime') WHERE id=? AND is_deleted=0""",
        (data['name'], data.get('url', ''), data['company_id'],
         data.get('type', 'web'), data.get('icon', ''), website_id)
    )
    conn.commit()
    conn.close()


def delete_website(website_id):
    """逻辑删除网站及其下所有账号。"""
    conn = get_db()
    conn.execute(
        "UPDATE websites SET is_deleted=1, updated_at=datetime('now','localtime') WHERE id=?",
        (website_id,)
    )
    conn.execute(
        "UPDATE accounts SET is_deleted=1, updated_at=datetime('now','localtime') WHERE website_id=?",
        (website_id,)
    )
    conn.commit()
    conn.close()


# ---- 账号 ----

def get_all_accounts():
    """获取所有未删除且未隐藏的账号（含库一致性过滤）。"""
    conn = get_db()
    rows = conn.execute(
        """SELECT a.id, a.website_id, a.account_name, a.status, a.phone, a.email, a.description, a.is_deleted,
                  a.registered_at, a.created_at, a.updated_at
           FROM accounts a
           JOIN websites w ON a.website_id = w.id
           JOIN companies co ON w.company_id = co.id
           WHERE w.is_deleted = 0 AND w.is_hidden = 0 AND w.is_template = 0
            AND co.is_deleted = 0 AND co.is_hidden = 0 AND co.is_template = 0
           ORDER BY a.created_at"""
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_accounts_by_website(website_id):
    """获取某个网站下所有未删除的账号。"""
    conn = get_db()
    rows = conn.execute(
        """SELECT id, website_id, account_name, password_enc, password_salt,
                  status, phone, email, description, is_deleted, registered_at, created_at, updated_at
           FROM accounts
           WHERE website_id = ?
           ORDER BY created_at""",
        (website_id,)
    ).fetchall()
    conn.close()
    result = []
    for r in rows:
        d = dict(r)
        d['has_password'] = bool(d.pop('password_enc'))
        d.pop('password_salt', None)
        result.append(d)
    return result


def get_account(account_id):
    """获取单个账号信息（含加密数据）。"""
    conn = get_db()
    row = conn.execute(
        """SELECT id, website_id, account_name, password_enc, password_salt,
                  status, phone, email, description, registered_at, created_at, updated_at
           FROM accounts WHERE id = ? AND is_deleted = 0""",
        (account_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def create_account(data):
    """创建账号。"""
    conn = get_db()
    cursor = conn.execute(
        """INSERT INTO accounts (website_id, account_name, password_enc, password_salt,
           status, phone, email, description, registered_at, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now','localtime'), datetime('now','localtime'))""",
        (data['website_id'], data['account_name'], data['password_enc'],
         data['password_salt'], data.get('status', 'active'),
         data.get('phone', ''), data.get('email', ''),
         data.get('description', ''), data.get('registered_at', ''))
    )
    conn.commit()
    aid = cursor.lastrowid
    conn.close()
    return aid


def update_account(account_id, data):
    """更新账号。"""
    conn = get_db()
    sets = []
    vals = []
    for field in ['account_name', 'status', 'phone', 'email', 'description', 'registered_at']:
        if field in data:
            sets.append(f"{field}=?")
            vals.append(data[field])
    if 'password_enc' in data and 'password_salt' in data:
        sets.append("password_enc=?")
        vals.append(data['password_enc'])
        sets.append("password_salt=?")
        vals.append(data['password_salt'])
    if sets:
        sets.append("updated_at=datetime('now','localtime')")
        vals.append(account_id)
        conn.execute(
            f"UPDATE accounts SET {', '.join(sets)} WHERE id=? AND is_deleted=0",
            vals
        )
        conn.commit()
    conn.close()


def restore_account(account_id):
    conn = get_db()
    conn.execute("UPDATE accounts SET is_deleted=0, status='active', updated_at=datetime('now','localtime') WHERE id=?", (account_id,))
    conn.commit()
    conn.close()

def delete_account(account_id):
    """逻辑删除账号。"""
    conn = get_db()
    conn.execute(
        "UPDATE accounts SET is_deleted=1, updated_at=datetime('now','localtime') WHERE id=?",
        (account_id,)
    )
    conn.commit()
    conn.close()


# ---- 搜索 ----

def search_accounts(keyword):
    """搜索账号，排除隐藏项并保持与库逻辑一致。"""
    conn = get_db()
    kw = f"%{keyword}%"
    rows = conn.execute(
        """SELECT a.id, a.website_id, a.account_name, a.status, a.phone, a.email, a.description, a.is_deleted,
                  a.registered_at, a.created_at, a.updated_at,
                  w.name as website_name, w.url as website_url, w.type as website_type,
                  co.name as company_name,
                  c.name as country_name
           FROM accounts a
           JOIN websites w ON a.website_id = w.id
           LEFT JOIN companies co ON w.company_id = co.id
           LEFT JOIN countries c ON co.country_id = c.id
           WHERE w.is_deleted = 0 AND w.is_hidden = 0 AND w.is_template = 0
             AND co.is_deleted = 0 AND co.is_hidden = 0 AND co.is_template = 0
             AND (co.name LIKE ? OR w.name LIKE ? OR a.account_name LIKE ? OR a.email LIKE ?
                  OR a.phone LIKE ? OR a.description LIKE ?)
           ORDER BY c.sort_order, co.name, w.name, a.created_at""",
        (kw, kw, kw, kw, kw, kw)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ---- 主密码 ----
def has_master_key():

    """判断是否已设置主密码。"""
    conn = get_db()
    row = conn.execute("SELECT key_hash FROM master_key WHERE id = 1").fetchone()
    conn.close()
    return row is not None

def set_master_key(key_hash):

    """设置主密码哈希。"""
    conn = get_db()
    conn.execute(
        """INSERT OR REPLACE INTO master_key (id, key_hash, created_at, updated_at)
           VALUES (1, ?, datetime('now','localtime'), datetime('now','localtime'))""",
        (key_hash,)
    )
    conn.commit()
    conn.close()

def get_master_key_hash():

    """获取主密码哈希。"""
    conn = get_db()
    row = conn.execute("SELECT key_hash FROM master_key WHERE id = 1").fetchone()
    conn.close()
    return row['key_hash'] if row else None


# ---- 预设数据 ----


def get_preset_data(country_code=None):
    conn = get_db()
    sql = (
        "SELECT co.id, co.name, c.code AS country_code, co.description, co.icon, "
        "CASE WHEN co.is_hidden = 0 THEN 1 ELSE 0 END AS is_visible, co.sort_order, "
        "co.is_deleted, co.created_at, co.updated_at "
        "FROM companies co "
        "JOIN countries c ON co.country_id = c.id "
        "WHERE co.is_template = 0 AND co.is_deleted = 0"
    )
    params = []
    if country_code:
        sql += " AND c.code = ?"
        params.append(country_code)
    sql += " ORDER BY c.code, co.sort_order, co.name"
    companies = conn.execute(sql, params).fetchall()

    result = []
    for co in companies:
        websites = conn.execute(
            "SELECT w.id, w.name, w.url, w.type, w.company_id, w.description, w.icon, "
            "CASE WHEN w.is_hidden = 0 THEN 1 ELSE 0 END AS is_visible, w.sort_order, w.is_deleted, "
            "w.created_at, w.updated_at "
            "FROM websites w WHERE w.company_id = ? AND w.is_template = 0 AND w.is_deleted = 0 "
            "ORDER BY w.sort_order, w.name",
            (co['id'],),
        ).fetchall()
        co_dict = dict(co)
        co_dict['websites'] = [dict(w) for w in websites]
        result.append(co_dict)

    conn.close()
    return result


def toggle_preset_company(preset_company_id, is_visible):
    conn = get_db()
    cursor = conn.cursor()

    company = conn.execute(
        "SELECT id, name, country_id, description, icon, sort_order, is_hidden FROM companies "
        "WHERE id = ? AND is_template = 0 AND is_deleted = 0",
        (preset_company_id,),
    ).fetchone()
    if not company:
        conn.close()
        return

    cursor.execute(
        "UPDATE companies SET is_hidden = ?, updated_at = datetime('now','localtime') "
        "WHERE id = ? AND is_template = 0",
        (0 if is_visible else 1, preset_company_id),
    )
    cursor.execute(
        "UPDATE websites SET is_hidden = ?, updated_at = datetime('now','localtime') "
        "WHERE company_id = ? AND is_template = 0 AND is_deleted = 0",
        (0 if is_visible else 1, preset_company_id),
    )

    conn.commit()
    conn.close()


def toggle_preset_website(preset_website_id, is_visible):
    conn = get_db()
    cursor = conn.cursor()

    website = conn.execute(
        "SELECT id, name, url, type, company_id, description, icon, sort_order, is_hidden FROM websites "
        "WHERE id = ? AND is_template = 0 AND is_deleted = 0",
        (preset_website_id,),
    ).fetchone()
    if not website:
        conn.close()
        return

    cursor.execute(
        "UPDATE websites SET is_hidden = ?, updated_at = datetime('now','localtime') "
        "WHERE id = ? AND is_template = 0",
        (0 if is_visible else 1, preset_website_id),
    )

    if is_visible:
        parent = conn.execute(
            "SELECT id, is_hidden FROM companies WHERE id = ? AND is_template = 0 AND is_deleted = 0",
            (website['company_id'],),
        ).fetchone()
        if parent and parent['is_hidden']:
            cursor.execute(
                "UPDATE companies SET is_hidden = 0, updated_at = datetime('now','localtime') WHERE id = ?",
                (parent['id'],),
            )

    conn.commit()
    conn.close()


def create_preset_company(name, country_code, description=''):
    conn = get_db()
    country = conn.execute(
        "SELECT id FROM countries WHERE code = ? AND is_deleted = 0",
        (country_code,),
    ).fetchone()
    if not country:
        conn.close()
        raise ValueError(f"Unknown country code: {country_code!r}")

    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO companies (name, country_id, description, icon, is_template, "
        "sort_order, is_hidden, is_deleted, created_at, updated_at) VALUES (?, ?, ?, '', 0, 0, 0, 0, "
        "datetime('now','localtime'), datetime('now','localtime'))",
        (name, country['id'], description or ''),
    )
    preset_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return preset_id


def update_preset_company(preset_id, data):
    conn = get_db()
    country = conn.execute(
        "SELECT id FROM countries WHERE code = ? AND is_deleted = 0",
        (data.get('country_code', ''),),
    ).fetchone()
    if not country:
        conn.close()
        raise ValueError(f"Unknown country code: {data.get('country_code', '')!r}")

    conn.execute(
        "UPDATE companies SET name = ?, country_id = ?, description = ?, updated_at = datetime('now','localtime') "
        "WHERE id = ? AND is_template = 0",
        (data.get('name', ''), country['id'], data.get('description', '') or '', preset_id),
    )
    conn.commit()
    conn.close()


def delete_preset_company(preset_id):
    conn = get_db()
    conn.execute(
        "UPDATE websites SET is_deleted = 1, is_hidden = 1, updated_at = datetime('now','localtime') "
        "WHERE company_id = ? AND is_template = 0",
        (preset_id,),
    )
    conn.execute(
        "UPDATE companies SET is_deleted = 1, is_hidden = 1, updated_at = datetime('now','localtime') "
        "WHERE id = ? AND is_template = 0",
        (preset_id,),
    )
    conn.execute(
        """UPDATE accounts SET is_deleted = 1, updated_at = datetime('now','localtime')
           WHERE website_id IN (
               SELECT id FROM websites WHERE company_id = ?
           )""",
        (preset_id,),
    )
    conn.commit()
    conn.close()


def create_preset_website(name, url, wtype, company_id):
    conn = get_db()
    parent = conn.execute(
        "SELECT id, is_hidden FROM companies WHERE id = ? AND is_template = 0 AND is_deleted = 0",
        (company_id,),
    ).fetchone()
    if not parent:
        conn.close()
        raise ValueError(f"Unknown company id: {company_id!r}")

    is_hidden = 1 if parent["is_hidden"] else 0
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO websites (name, url, company_id, type, description, icon, is_template, "
        "sort_order, is_hidden, is_deleted, created_at, updated_at) VALUES (?, ?, ?, ?, '', '', 0, 0, ?, 0, "
        "datetime('now','localtime'), datetime('now','localtime'))",
        (name, url, company_id, wtype, is_hidden),
    )
    preset_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return preset_id


def update_preset_website(preset_id, data):
    conn = get_db()
    conn.execute(
        "UPDATE websites SET name = ?, url = ?, type = ?, updated_at = datetime('now','localtime') "
        "WHERE id = ? AND is_template = 0",
        (data.get('name', ''), data.get('url', ''), data.get('type', 'web'), preset_id),
    )
    conn.commit()
    conn.close()


def delete_preset_website(preset_id):
    conn = get_db()
    conn.execute(
        "UPDATE websites SET is_deleted = 1, is_hidden = 1, updated_at = datetime('now','localtime') "
        "WHERE id = ? AND is_template = 0",
        (preset_id,),
    )
    conn.execute(
        "UPDATE accounts SET is_deleted = 1, updated_at = datetime('now','localtime') WHERE website_id = ?",
        (preset_id,),
    )
    conn.commit()
    conn.close()

