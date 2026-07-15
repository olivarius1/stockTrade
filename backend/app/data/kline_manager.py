#!/usr/bin/env python3
"""
A股估值数据库管理模块
SQLite存储K线数据，支持增量更新
"""
import sqlite3
import json
import os
import sys
import urllib.request

# 统一使用后端数据库
_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_BACKEND_DB = os.path.join(_BACKEND_DIR, 'data', 'valuation.db')
DB_PATH = os.environ.get('VALUATION_DB', _BACKEND_DB)

def get_db_path():
    """获取数据库路径，支持通过环境变量覆盖"""
    return os.environ.get('VALUATION_DB', DB_PATH)

def ensure_db():
    """确保数据库和表存在"""
    db_path = get_db_path()
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS stocks (
        code TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        exchange TEXT NOT NULL,
        total_shares REAL,
        industry TEXT,
        model_type TEXT DEFAULT 'cyclical',
        pe_min REAL DEFAULT 6,
        pe_max REAL DEFAULT 20,
        pb_min REAL DEFAULT 1.0,
        pb_max REAL DEFAULT 4.0,
        eps_growth REAL DEFAULT 0.10,
        revenue TEXT,
        net_profit TEXT,
        gross_margin TEXT,
        market_cap TEXT,
        subtitle TEXT,
        extra_factors TEXT DEFAULT '{}',
        last_pe REAL DEFAULT 0,
        last_pb REAL DEFAULT 0,
        last_price REAL DEFAULT 0,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS kline_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        stock_code TEXT NOT NULL,
        date TEXT NOT NULL,
        open REAL,
        high REAL,
        low REAL,
        close REAL,
        volume REAL,
        amount REAL,
        UNIQUE(stock_code, date)
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS valuation_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        stock_code TEXT NOT NULL,
        date TEXT NOT NULL,
        score REAL,
        pe_score REAL,
        pb_score REAL,
        peg_score REAL,
        ma_score REAL,
        volatility_score REAL,
        volume_score REAL,
        roe_score REAL,
        dividend_score REAL,
        ai_score REAL,
        pe REAL,
        pb REAL,
        price REAL,
        UNIQUE(stock_code, date)
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS reports_meta (
        code TEXT PRIMARY KEY,
        report_file TEXT,
        generated_at TEXT,
        params TEXT
    )''')
    
    # 索引
    c.execute('CREATE INDEX IF NOT EXISTS idx_kline_code ON kline_data(stock_code, date)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_valuation_code ON valuation_history(stock_code, date)')
    
    conn.commit()
    conn.close()
    return db_path

def fetch_kline_from_api(code_full, start_date, end_date):
    """从腾讯API获取K线数据
    code_full: e.g. 'sh600938' or 'sz000807'
    返回: list of dict
    """
    url = (f"http://web.ifzq.gtimg.cn/appstock/app/fqkline/get"
           f"?param={code_full},day,{start_date},{end_date},500,qfq")
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode('utf-8'))
    # 安全获取K线数据（某些股票上市前可能无qfqday字段）
    stock_data = data.get('data', {}).get(code_full, {})
    kdata = stock_data.get('qfqday', [])
    qt = stock_data.get('qt', {}).get(code_full, [])
    rows = []
    for r in kdata:
        rows.append({
            'date': r[0],
            'open': float(r[1]),
            'close': float(r[2]),
            'high': float(r[3]),
            'low': float(r[4]),
            'volume': float(r[5])
        })
    latest = {
        'price': float(qt[3]) if len(qt) > 3 and qt[3] else 0,
        'pe': float(qt[39]) if len(qt) > 39 and qt[39] else 0,
        'pb': float(qt[46]) if len(qt) > 46 and qt[46] else 0,
        'volume': float(qt[6]) if len(qt) > 6 and qt[6] else 0,
        'date': qt[30] if len(qt) > 30 and qt[30] else '',
    }
    return rows, latest

def update_kline(code, name=None, exchange=None):
    """增量更新K线数据到数据库
    返回: (新增天数, 总天数, latest_info)
    """
    ensure_db()
    conn = sqlite3.connect(get_db_path())
    c = conn.cursor()
    
    # 查找最新日期
    c.execute('SELECT MAX(date) FROM kline_data WHERE stock_code = ?', (code,))
    row = c.fetchone()
    last_date = row[0] if row and row[0] else '2020-01-01'
    
    # 确定交易所
    if not exchange:
        if code.startswith('6') or code.startswith('9'):
            exchange = 'sh'
        else:
            exchange = 'sz'
    code_full = exchange + code
    
    # 从最新日期的下一天开始获取（多取几天确保不遗漏）
    start_parts = last_date.split('-')
    from datetime import datetime, timedelta
    last_dt = datetime(int(start_parts[0]), int(start_parts[1]), int(start_parts[2]))
    start_dt = last_dt + timedelta(days=1)
    end_dt = datetime.now() + timedelta(days=1)
    
    all_rows = []
    latest_info = None
    last_error = None
    first_batch = True
    
    # 分批获取（每批最多500天，实际约365个交易日）
    batch_start = start_dt
    while batch_start < end_dt:
        batch_end = min(batch_start + timedelta(days=550), end_dt)
        try:
            rows, latest = fetch_kline_from_api(
                code_full,
                batch_start.strftime('%Y-%m-%d'),
                batch_end.strftime('%Y-%m-%d')
            )
            if first_batch:
                latest_info = latest  # 保留第一批的qt行情（含实时价格/日期）
                first_batch = False
            if not rows:
                # 该批次无数据（可能是上市前的空区间），跳到下一批继续
                batch_start = batch_end
                continue
            all_rows.extend(rows)
            latest_info = latest
            # 用实际返回的最后一条日期作为下一批起点
            last_fetched_dt = datetime.strptime(rows[-1]['date'], '%Y-%m-%d')
            if last_fetched_dt >= end_dt - timedelta(days=1):
                break
            batch_start = last_fetched_dt + timedelta(days=1)
        except Exception as e:
            print(f"  获取数据失败: {e}")
            break
    
    # 写入数据库（INSERT OR REPLACE 处理重复）
    if all_rows:
        c.executemany(
            'INSERT OR REPLACE INTO kline_data (stock_code, date, open, high, low, close, volume) VALUES (?, ?, ?, ?, ?, ?, ?)',
            [(code, r['date'], r['open'], r['high'], r['low'], r['close'], r['volume']) for r in all_rows]
        )
        conn.commit()
    
    # 总天数
    c.execute('SELECT COUNT(*) FROM kline_data WHERE stock_code = ?', (code,))
    total = c.fetchone()[0]
    
    # 如果没有获取到最新行情（增量0天），从数据库最新K线获取
    if not latest_info and total > 0:
        c.execute('SELECT close FROM kline_data WHERE stock_code = ? ORDER BY date DESC LIMIT 1', (code,))
        last_close = c.fetchone()
        latest_info = {'price': last_close[0] if last_close else 0, 'pe': 0, 'pb': 0}
    
    # 保存最后一次成功的PE/PB/价格到stocks表（供增量0天时恢复）
    if latest_info and (latest_info.get('pe', 0) > 0 or latest_info.get('pb', 0) > 0):
        try:
            c.execute('''UPDATE stocks SET last_pe=?, last_pb=?, last_price=? WHERE code=?''',
                (latest_info.get('pe', 0), latest_info.get('pb', 0), latest_info.get('price', 0), code))
            conn.commit()
        except:
            pass
    
    conn.close()
    return len(all_rows), total, latest_info

def get_kline(code):
    """从数据库读取全部K线数据，按日期排序
    返回: list of dict
    """
    ensure_db()
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT date, open, close, high, low, volume FROM kline_data WHERE stock_code = ? ORDER BY date', (code,))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows

def save_stock_info(code, name, exchange, total_shares, industry, model_type,
                    pe_min, pe_max, pb_min, pb_max, eps_growth,
                    revenue, net_profit, gross_margin, market_cap, subtitle,
                    extra_factors='{}'):
    """保存/更新股票基本信息"""
    ensure_db()
    conn = sqlite3.connect(get_db_path())
    c = conn.cursor()
    c.execute('''INSERT INTO stocks 
        (code, name, exchange, total_shares, industry, model_type,
         pe_min, pe_max, pb_min, pb_max, eps_growth,
         revenue, net_profit, gross_margin, market_cap, subtitle, extra_factors, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(code) DO UPDATE SET
         name=excluded.name, exchange=excluded.exchange, total_shares=excluded.total_shares,
         industry=excluded.industry, model_type=excluded.model_type,
         pe_min=excluded.pe_min, pe_max=excluded.pe_max, pb_min=excluded.pb_min, pb_max=excluded.pb_max,
         eps_growth=excluded.eps_growth, revenue=excluded.revenue, net_profit=excluded.net_profit,
         gross_margin=excluded.gross_margin, market_cap=excluded.market_cap,
         subtitle=excluded.subtitle, extra_factors=excluded.extra_factors,
         updated_at=CURRENT_TIMESTAMP''',
        (code, name, exchange, total_shares, industry, model_type,
         pe_min, pe_max, pb_min, pb_max, eps_growth,
         revenue, net_profit, gross_margin, market_cap, subtitle, extra_factors))
    conn.commit()
    conn.close()

def get_stock_info(code):
    """读取股票基本信息"""
    ensure_db()
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM stocks WHERE code = ?', (code,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None

def list_stocks():
    """列出所有已存储的股票"""
    ensure_db()
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT code, name, exchange, industry, model_type, updated_at FROM stocks ORDER BY code')
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows

def save_report_meta(code, report_file, params=''):
    """记录报告生成信息"""
    ensure_db()
    conn = sqlite3.connect(get_db_path())
    c = conn.cursor()
    c.execute('''INSERT OR REPLACE INTO reports_meta (code, report_file, generated_at, params)
        VALUES (?, ?, CURRENT_TIMESTAMP, ?)''', (code, report_file, params))
    conn.commit()
    conn.close()

def get_report_meta(code):
    """读取报告生成信息"""
    ensure_db()
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM reports_meta WHERE code = ?', (code,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None

def db_stats():
    """数据库统计信息"""
    ensure_db()
    conn = sqlite3.connect(get_db_path())
    c = conn.cursor()
    c.execute('SELECT COUNT(DISTINCT stock_code) FROM kline_data')
    stock_count = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM kline_data')
    total_rows = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM valuation_history')
    val_rows = c.fetchone()[0]
    db_size = os.path.getsize(get_db_path()) / 1024
    conn.close()
    return {'stocks': stock_count, 'kline_rows': total_rows, 'valuation_rows': val_rows, 'db_size_kb': round(db_size, 1)}

def save_valuation_history(stock_code, results):
    """批量保存估值评分历史到数据库
    results: list of dict, 每条含 date, close, score, pe_ttm, pb 等字段
    """
    ensure_db()
    conn = sqlite3.connect(get_db_path())
    c = conn.cursor()
    for r in results:
        c.execute('''INSERT OR REPLACE INTO valuation_history 
            (stock_code, date, score, pe, pb, price, pe_score, pb_score, peg_score, 
             ma_score, volatility_score, volume_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (stock_code, r['date'], r.get('score', 0),
             r.get('pe_ttm', 0), r.get('pb', 0), r.get('close', 0),
             r.get('s_pe', 0), r.get('s_pb', 0), r.get('s_peg', 0),
             r.get('s_ma', 0), r.get('s_vola', 0), r.get('s_vol', 0)))
    conn.commit()
    conn.close()

def get_valuation_history(stock_code):
    """从数据库读取估值评分历史
    返回: list of dict, 含 date, close, score, pe, pb 等
    """
    ensure_db()
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('''SELECT date, score, pe, pb, price FROM valuation_history 
                 WHERE stock_code = ? ORDER BY date''', (stock_code,))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows

def list_valuation_stocks():
    """列出数据库中有估值历史的所有股票"""
    ensure_db()
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('''SELECT DISTINCT vh.stock_code, s.name, s.industry, s.model_type,
                 COUNT(vh.date) as days, MAX(vh.date) as latest_date,
                 (SELECT score FROM valuation_history WHERE stock_code = vh.stock_code ORDER BY date DESC LIMIT 1) as latest_score
                 FROM valuation_history vh
                 LEFT JOIN stocks s ON vh.stock_code = s.code
                 GROUP BY vh.stock_code
                 ORDER BY vh.stock_code''')
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows

# ===== CLI 接口 =====
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法:")
        print("  python3 db_manager.py update <代码> [名称] [交易所]")
        print("  python3 db_manager.py list")
        print("  python3 db_manager.py stats")
        print("  python3 db_manager.py info <代码>")
        print("  python3 db_manager.py init  # 仅初始化数据库")
        sys.exit(0)
    
    cmd = sys.argv[1]
    
    if cmd == 'init':
        path = ensure_db()
        print(f"数据库已初始化: {path}")
    
    elif cmd == 'update':
        if len(sys.argv) < 3:
            print("需要股票代码")
            sys.exit(1)
        code = sys.argv[2]
        name = sys.argv[3] if len(sys.argv) > 3 else None
        exchange = sys.argv[4] if len(sys.argv) > 4 else None
        added, total, latest = update_kline(code, name, exchange)
        print(f"新增 {added} 天，共 {total} 天")
        if latest:
            print(f"最新: 价格={latest['price']:.2f} PE={latest['pe']:.1f} PB={latest['pb']:.2f}")
    
    elif cmd == 'list':
        stocks = list_stocks()
        for s in stocks:
            c.execute = None  # suppress
            print(f"  {s['code']} {s['name']} ({s['exchange']}) {s['industry']} [{s['model_type']}]")
        if not stocks:
            print("  (空)")
    
    elif cmd == 'stats':
        stats = db_stats()
        print(f"股票数: {stats['stocks']}")
        print(f"K线条数: {stats['kline_rows']}")
        print(f"数据库大小: {stats['db_size_kb']} KB")
    
    elif cmd == 'info':
        if len(sys.argv) < 3:
            print("需要股票代码")
            sys.exit(1)
        info = get_stock_info(sys.argv[2])
        if info:
            for k, v in info.items():
                print(f"  {k}: {v}")
        else:
            print("  未找到")
