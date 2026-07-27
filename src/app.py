"""
EasyPass - 密码管理器 Flask 主应用
层级: 国家 → 公司 → 网站/应用 → 账号
新增: 预设数据管理 API
"""

from pathlib import Path
import os
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
LIBS_DIR = ROOT_DIR / 'libs'
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
if LIBS_DIR.exists():
    sys.path.insert(0, str(LIBS_DIR))

from flask import Flask, jsonify, request, render_template
from flask_cors import CORS

from src import models, crypto_utils
from src.config import SECRET_KEY

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = SECRET_KEY
CORS(app)

# 启动时初始化数据库并同步基础种子数据
models.init_db()


# ============ 页面路由 ============

@app.route('/')
def index():
    return render_template('index.html', country_options=models.get_countries())


# ============ 主密码 API ============

@app.route('/api/master-key/status', methods=['GET'])
def master_key_status():
    return jsonify({'has_key': models.has_master_key()})


@app.route('/api/master-key/setup', methods=['POST'])
def setup_master_key():
    if models.has_master_key():
        return jsonify({'error': '主密码已设置，不能重复设置'}), 400
    data = request.json
    password = data.get('password', '')
    if len(password) < 6:
        return jsonify({'error': '主密码至少6位'}), 400
    key_hash = crypto_utils.hash_master_password(password)
    models.set_master_key(key_hash)
    return jsonify({'success': True})


@app.route('/api/master-key/verify', methods=['POST'])
def verify_master_key():
    data = request.json
    password = data.get('password', '')
    stored_hash = models.get_master_key_hash()
    if not stored_hash:
        return jsonify({'valid': False, 'error': '未设置主密码'}), 400
    valid = crypto_utils.verify_master_password(stored_hash, password)
    return jsonify({'valid': valid})


# ============ 国家 API ============

@app.route('/api/countries', methods=['GET'])
def list_countries():
    try:
        countries = models.get_countries()
        return jsonify(countries)
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/countries', methods=['POST'])
def add_country():
    try:
        data = request.json
        cid = models.add_country(data['name'], data['code'], data.get('sort_order', 0))
        return jsonify({'id': cid}), 201
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ============ 公司 API ============
@app.route('/api/companies', methods=['GET'])
def list_companies():
    try:
        country_id = request.args.get('country_id', type=int)
        companies = models.get_companies_by_country(country_id)
        return jsonify(companies)
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/companies', methods=['POST'])
def create_company():
    data = request.json
    if not data.get('name'):
        return jsonify({'error': '请输入公司名称'}), 400
    if not data.get('country_id'):
        return jsonify({'error': '请选择国家'}), 400
    try:
        cid = models.create_company(data)
        return jsonify({'id': cid}), 201
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/companies/<int:cid>', methods=['GET'])
def get_company(cid):
    try:
        co = models.get_company(cid)
        if not co:
            return jsonify({'error': '公司不存在'}), 404
        return jsonify(co)
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/companies/<int:cid>', methods=['PUT'])
def update_company(cid):
    try:
        data = request.json
        models.update_company(cid, data)
        return jsonify({'success': True})
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/companies/<int:cid>', methods=['DELETE'])
def delete_company(cid):
    try:
        models.delete_company(cid)
        return jsonify({'success': True})
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ============ 网站 API ============

@app.route('/api/websites', methods=['GET'])
def list_websites():
    try:
        company_id = request.args.get('company_id', type=int)
        websites = models.get_websites_by_company(company_id)
        return jsonify(websites)
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/websites', methods=['POST'])
def create_website():
    try:
        data = request.json
        wid = models.create_website(data)
        return jsonify({'id': wid}), 201
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/websites/<int:wid>', methods=['GET'])
def get_website(wid):
    try:
        w = models.get_website(wid)
        if not w:
            return jsonify({'error': '网站不存在'}), 404
        return jsonify(w)
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/websites/<int:wid>', methods=['PUT'])
def update_website(wid):
    try:
        data = request.json
        models.update_website(wid, data)
        return jsonify({'success': True})
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/websites/<int:wid>', methods=['DELETE'])
def delete_website(wid):
    try:
        models.delete_website(wid)
        return jsonify({'success': True})
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ============ 账号 API ============

@app.route('/api/accounts', methods=['GET'])
def list_all_accounts():
    """获取所有账号（用于卡片视图批量加载）"""
    try:
        accounts = models.get_all_accounts()
        return jsonify(accounts)
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/websites/<int:wid>/accounts', methods=['GET'])
def list_accounts(wid):
    try:
        accounts = models.get_accounts_by_website(wid)
        return jsonify(accounts)
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/accounts/<int:aid>', methods=['GET'])
def get_account(aid):
    try:
        account = models.get_account(aid)
        if not account:
            return jsonify({'error': '账号不存在'}), 404
        return jsonify(account)
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/websites/<int:wid>/accounts', methods=['POST'])
def create_account(wid):
    try:
        data = request.json
        master_pwd = data.pop('master_password', '')
        plain_password = data.pop('plain_password', '')

        enc = crypto_utils.encrypt_password(plain_password, master_pwd)
        data['password_enc'] = enc['ciphertext']
        data['password_salt'] = enc['salt']
        data['website_id'] = wid

        aid = models.create_account(data)
        return jsonify({'id': aid}), 201
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/accounts/<int:aid>', methods=['PUT'])
def update_account(aid):
    try:
        data = request.json
        master_pwd = data.pop('master_password', '')
        plain_password = data.pop('plain_password', None)

        if plain_password is not None:
            enc = crypto_utils.encrypt_password(plain_password, master_pwd)
            data['password_enc'] = enc['ciphertext']
            data['password_salt'] = enc['salt']

        models.update_account(aid, data)
        return jsonify({'success': True})
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/accounts/<int:aid>/decrypt', methods=['POST'])
def decrypt_account_password(aid):
    try:
        account = models.get_account(aid)
        if not account:
            return jsonify({'error': '账号不存在'}), 404
        master_pwd = request.json.get('master_password', '')
        try:
            plain = crypto_utils.decrypt_password(
                {'ciphertext': account['password_enc'], 'salt': account['password_salt']},
                master_pwd
            )
            return jsonify({'password': plain})
        except Exception:
            return jsonify({'error': '解密失败，主密码可能不正确'}), 403
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'error': str(e)}), 500



@app.route('/api/accounts/<int:aid>/restore', methods=['PUT'])
def restore_account(aid):
    try:
        models.restore_account(aid)
        return jsonify({'success': True})
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/accounts/<int:aid>', methods=['DELETE'])
def delete_account(aid):
    try:
        models.delete_account(aid)
        return jsonify({'success': True})
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ============ 搜索 API ============

@app.route('/api/search', methods=['GET'])
def search():
    try:
        keyword = request.args.get('q', '')
        if not keyword:
            return jsonify([])
        results = models.search_accounts(keyword)
        return jsonify(results)
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ============ 统计 API ============

@app.route('/api/stats', methods=['GET'])
def stats():
    try:
        conn = models.get_db()
        total_websites = conn.execute(
            "SELECT COUNT(*) FROM websites WHERE is_deleted=0 AND is_hidden=0 AND is_template=0"
        ).fetchone()[0]
        total_accounts = conn.execute(
            "SELECT COUNT(*) FROM accounts WHERE is_deleted=0"
        ).fetchone()[0]
        total_companies = conn.execute(
            "SELECT COUNT(*) FROM companies WHERE is_deleted=0 AND is_hidden=0 AND is_template=0"
        ).fetchone()[0]
        total_countries = conn.execute(
            """SELECT COUNT(DISTINCT co.country_id) FROM companies co
               WHERE co.is_deleted=0 AND co.is_hidden=0 AND co.is_template=0 AND co.country_id IS NOT NULL"""
        ).fetchone()[0]
        conn.close()
        return jsonify({
            'websites': total_websites,
            'accounts': total_accounts,
            'companies': total_companies,
            'countries': total_countries,
        })
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ============ 预设数据 API ============

@app.route('/api/preset', methods=['GET'])
def get_preset_data():
    """获取预设数据（按国家分组）"""
    try:
        country_code = request.args.get('country_code')
        data = models.get_preset_data(country_code)
    except Exception as e:
        print(f"[API] /api/preset error: {e}")
        data = []

    # 按国家分组
    grouped = {}
    for item in data:
        cc = item.get('country_code', '')
        if cc not in grouped:
            grouped[cc] = []
        grouped[cc].append(item)

    # 转为列表
    # 从数据库动态获取国家名称映射
    try:
        all_countries = models.get_countries()
        countries_map = {c['code']: c['name'] for c in all_countries}
    except:
        countries_map = {}
    result = []
    for code, companies in grouped.items():
        result.append({
            'code': code,
            'name': countries_map.get(code, code),
            'companies': companies
        })

    return jsonify(result)


@app.route('/api/preset/companies/<int:preset_id>/toggle', methods=['PUT'])
def toggle_preset_company(preset_id):
    """切换预设公司显示状态"""
    try:
        data = request.json
        is_visible = data.get('is_visible', False)
        models.toggle_preset_company(preset_id, is_visible)
        return jsonify({'success': True})
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/preset/websites/<int:preset_id>/toggle', methods=['PUT'])
def toggle_preset_website(preset_id):
    """切换预设网站显示状态"""
    try:
        data = request.json
        is_visible = data.get('is_visible', False)
        models.toggle_preset_website(preset_id, is_visible)
        return jsonify({'success': True})
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ---- 预设数据 CRUD API ----

@app.route('/api/preset/companies', methods=['POST'])
def create_preset_company():
    """创建预设公司"""
    try:
        data = request.json
        if not data.get('name'):
            return jsonify({'error': '请输入公司名称'}), 400
        if not data.get('country_code'):
            return jsonify({'error': '请选择国家'}), 400
        preset_id = models.create_preset_company(
            data['name'],
            data['country_code'],
            data.get('description', ''),
        )
        return jsonify({'id': preset_id}), 201
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/preset/companies/<int:preset_id>', methods=['PUT'])
def update_preset_company(preset_id):
    """更新预设公司"""
    try:
        data = request.json
        if not data.get('name'):
            return jsonify({'error': '请输入公司名称'}), 400
        models.update_preset_company(preset_id, data)
        return jsonify({'success': True})
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/preset/companies/<int:preset_id>', methods=['DELETE'])
def delete_preset_company(preset_id):
    """删除预设公司"""
    try:
        models.delete_preset_company(preset_id)
        return jsonify({'success': True})
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/preset/websites', methods=['POST'])
def create_preset_website():
    """创建预设网站"""
    try:
        data = request.json
        if not data.get('name'):
            return jsonify({'error': '请输入名称'}), 400
        company_id = data.get('company_id')
        if not company_id:
            return jsonify({'error': '请选择所属公司'}), 400
        preset_id = models.create_preset_website(
            data['name'], data.get('url', ''), data.get('type', 'web'), company_id
        )
        return jsonify({'id': preset_id}), 201
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/preset/websites/<int:preset_id>', methods=['PUT'])
def update_preset_website(preset_id):
    """更新预设网站"""
    try:
        data = request.json
        if not data.get('name'):
            return jsonify({'error': '请输入名称'}), 400
        models.update_preset_website(preset_id, data)
        return jsonify({'success': True})
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/preset/websites/<int:preset_id>', methods=['DELETE'])
def delete_preset_website(preset_id):
    """删除预设网站"""
    try:
        models.delete_preset_website(preset_id)
        return jsonify({'success': True})
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ============ 诊断 API ============

@app.route('/api/health', methods=['GET'])
def health_check():
    """数据库健康检查 - 返回表结构和数据状态"""
    result = {'tables': {}, 'data_check': {}, 'errors': []}
    try:
        conn = models.get_db()
        tables = ['countries', 'companies', 'websites', 'accounts', 'master_key']
        for tbl in tables:
            try:
                cols = [r[1] for r in conn.execute(f"PRAGMA table_info({tbl})").fetchall()]
                count = conn.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
                null_info = {}
                for col in ['is_deleted', 'is_hidden', 'created_at', 'updated_at']:
                    if col in cols:
                        null_count = conn.execute(f"SELECT COUNT(*) FROM {tbl} WHERE {col} IS NULL").fetchone()[0]
                        if null_count > 0:
                            null_info[col] = f"{null_count} NULL"
                result['tables'][tbl] = {
                    'columns': cols,
                    'count': count,
                    'nulls': null_info if null_info else 'OK'
                }
            except Exception as e:
                result['errors'].append(f"{tbl}: {e}")

        # 公司数据一致性检查
        try:
            # 侧栏可见的公司（is_deleted=0 AND is_hidden=0）
            visible = conn.execute(
                "SELECT id, name, country_id FROM companies WHERE is_deleted=0 AND is_hidden=0 AND is_template=0 ORDER BY id"
            ).fetchall()
            result['data_check']['visible_companies'] = [dict(r) for r in visible]

            # 被隐藏的公司
            hidden = conn.execute(
                "SELECT id, name, country_id FROM companies WHERE is_deleted=0 AND is_hidden=1 AND is_template=0 ORDER BY id"
            ).fetchall()
            result['data_check']['hidden_companies'] = [dict(r) for r in hidden]

            # 被逻辑删除的公司
            deleted = conn.execute(
                "SELECT id, name, country_id FROM companies WHERE is_deleted=1 AND is_template=0 ORDER BY id"
            ).fetchall()
            result['data_check']['deleted_companies'] = [dict(r) for r in deleted]

            # is_hidden 为 NULL 的公司（异常）
            null_hidden = conn.execute(
                "SELECT id, name, country_id FROM companies WHERE is_deleted=0 AND is_hidden IS NULL AND is_template=0"
            ).fetchall()
            result['data_check']['null_is_hidden_companies'] = [dict(r) for r in null_hidden]

            # 可见但没有任何网站的预设公司
            preset_visible = conn.execute(
                """SELECT co.id, co.name, co.country_id
                   FROM companies co
                   WHERE co.is_deleted=0 AND co.is_hidden=0 AND co.is_template=0
                     AND NOT EXISTS (
                         SELECT 1 FROM websites w
                         WHERE w.company_id = co.id AND w.is_deleted = 0 AND w.is_template = 0
                     )"""
            ).fetchall()
            result['data_check']['preset_visible_no_websites'] = [dict(r) for r in preset_visible]

            # 异常公司：country_id 无法在 countries 表中找到
            orphan = conn.execute(
                """SELECT co.id, co.name, co.country_id
                   FROM companies co
                   WHERE co.is_deleted=0 AND co.is_hidden=0 AND co.is_template=0
                     AND co.country_id NOT IN (
                         SELECT id FROM countries WHERE is_deleted = 0
                     )"""
            ).fetchall()
            result['data_check']['orphan_companies'] = [dict(r) for r in orphan]

        except Exception as e:
            result['errors'].append(f"data_check: {e}")

        conn.close()
    except Exception as e:
        result['errors'].append(f"connection: {e}")
    return jsonify(result)


# ============ 数据库表查看 API ============

DB_TABLE_DESCRIPTIONS = {
    'countries': '国家基础数据，保存国家名称、代码和基础信息。',
    'companies': '公司数据表，包含预设公司和实际公司记录。',
    'websites': '网站数据表，保存公司下的网站、链接和类型信息。',
    'accounts': '账号数据表，保存账号、联系方式和描述信息。',
    'master_key': '系统主密钥配置表，用于应用解锁。',
}


def describe_db_table(table_name):
    return DB_TABLE_DESCRIPTIONS.get(table_name, '')


@app.route('/api/db/tables', methods=['GET'])
def db_list_tables():
    conn = models.get_db()
    try:
        tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'").fetchall()
        return jsonify([
            {'name': row['name'], 'description': describe_db_table(row['name'])}
            for row in tables
        ])
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@app.route('/api/db/table/<table_name>', methods=['GET'])
def db_get_table_data(table_name):
    conn = models.get_db()
    try:
        # 验证表名以防止 SQL 注入
        valid_tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'").fetchall()
        valid_table_names = [row['name'] for row in valid_tables]
        if table_name not in valid_table_names:
            return jsonify({'error': 'Invalid table name'}), 400

        # 获取字段名 (columns)
        columns_info = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
        columns = [row['name'] for row in columns_info]

        # 获取所有数据行 (rows)
        rows = conn.execute(f"SELECT * FROM {table_name}").fetchall()
        data = [dict(r) for r in rows]

        return jsonify({
            'columns': columns,
            'rows': data
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


# ============ 启动 ============

if __name__ == '__main__':
    debug_mode = os.environ.get('FLASK_DEBUG', '').lower() in {'1', 'true', 'yes', 'on'}
    print("=" * 50)
    print("  EasyPass 密码管理器")
    print("  http://localhost:5000")
    print("=" * 50)
    app.run(host='127.0.0.1', port=5000, debug=debug_mode, use_reloader=debug_mode)
