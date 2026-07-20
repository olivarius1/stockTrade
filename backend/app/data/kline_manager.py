#!/usr/bin/env python3
"""
A股估值数据库管理模块
PostgreSQL存储K线数据，支持增量更新
"""
import psycopg2
import psycopg2.extras
import json
import os
import sys
import urllib.request

def get_connection():
    """从应用配置获取 PostgreSQL 连接（与 ORM 使用同一数据库）"""
    from app.core.config import settings
    return psycopg2.connect(settings.DATABASE_URL)

def ensure_db():
    """确保数据库表存在"""
    conn = get_connection()
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS stocks (
        code TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        exchange TEXT NOT NULL,
        total_shares DOUBLE PRECISION,
        industry TEXT,
        model_type TEXT DEFAULT 'cyclical',
        pe_min DOUBLE PRECISION DEFAULT 6,
        pe_max DOUBLE PRECISION DEFAULT 20,
        pb_min DOUBLE PRECISION DEFAULT 1.0,
        pb_max DOUBLE PRECISION DEFAULT 4.0,
        eps_growth DOUBLE PRECISION DEFAULT 0.10,
        revenue TEXT,
        net_profit TEXT,
        gross_margin TEXT,
        market_cap TEXT,
        subtitle TEXT,
        extra_factors TEXT DEFAULT '{}',
        last_pe DOUBLE PRECISION DEFAULT 0,
        last_pb DOUBLE PRECISION DEFAULT 0,
        last_price DOUBLE PRECISION DEFAULT 0,
        updated_at TIMESTAMP DEFAULT NOW()
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS kline_data (
        id SERIAL PRIMARY KEY,
        stock_code TEXT NOT NULL,
        date TEXT NOT NULL,
        open DOUBLE PRECISION,
        high DOUBLE PRECISION,
        low DOUBLE PRECISION,
        close DOUBLE PRECISION,
        volume DOUBLE PRECISION,
        amount DOUBLE PRECISION,
        UNIQUE(stock_code, date)
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS valuation_history (
        id SERIAL PRIMARY KEY,
        stock_code TEXT NOT NULL,
        date TEXT NOT NULL,
        score DOUBLE PRECISION,
        pe_score DOUBLE PRECISION,
        pb_score DOUBLE PRECISION,
        peg_score DOUBLE PRECISION,
        ma_score DOUBLE PRECISION,
        volatility_score DOUBLE PRECISION,
        volume_score DOUBLE PRECISION,
        roe_score DOUBLE PRECISION,
        dividend_score DOUBLE PRECISION,
        ai_score DOUBLE PRECISION,
        pe DOUBLE PRECISION,
        pb DOUBLE PRECISION,
        price DOUBLE PRECISION,
        UNIQUE(stock_code, date)
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS reports_meta (
        code TEXT PRIMARY KEY,
        report_file TEXT,
        generated_at TIMESTAMP,
        params TEXT
    )''')
    
    # 索引
    c.execute('CREATE INDEX IF NOT EXISTS idx_kline_code ON kline_data(stock_code, date)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_valuation_code ON valuation_history(stock_code, date)')
    
    conn.commit()
    conn.close()

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
    conn = get_connection()
    c = conn.cursor()
    
    c.execute('SELECT MAX(date) FROM kline_data WHERE stock_code = %s', (code,))
    row = c.fetchone()
    last_date = row[0] if row and row[0] else '2020-01-01'
    
    if not exchange:
        if code.startswith('6') or code.startswith('9'):
            exchange = 'sh'
        else:
            exchange = 'sz'
    code_full = exchange + code
    
    start_parts = last_date.split('-')
    from datetime import datetime, timedelta
    last_dt = datetime(int(start_parts[0]), int(start_parts[1]), int(start_parts[2]))
    start_dt = last_dt + timedelta(days=1)
    end_dt = datetime.now() + timedelta(days=1)
    
    all_rows = []
    latest_info = None
    last_error = None
    first_batch = True
    
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
                latest_info = latest
                first_batch = False
            if not rows:
                batch_start = batch_end
                continue
            all_rows.extend(rows)
            latest_info = latest
            last_fetched_dt = datetime.strptime(rows[-1]['date'], '%Y-%m-%d')
            if last_fetched_dt >= end_dt - timedelta(days=1):
                break
            batch_start = last_fetched_dt + timedelta(days=1)
        except Exception as e:
            print(f"  获取数据失败: {e}")
            break
    
    if all_rows:
        psycopg2.extras.execute_batch(
            c,
            '''INSERT INTO kline_data (stock_code, date, open, high, low, close, volume) 
               VALUES (%s, %s, %s, %s, %s, %s, %s)
               ON CONFLICT (stock_code, date) DO UPDATE SET
               open=EXCLUDED.open, high=EXCLUDED.high, low=EXCLUDED.low, 
               close=EXCLUDED.close, volume=EXCLUDED.volume''',
            [(code, r['date'], r['open'], r['high'], r['low'], r['close'], r['volume']) for r in all_rows]
        )
        conn.commit()
    
    c.execute('SELECT COUNT(*) FROM kline_data WHERE stock_code = %s', (code,))
    total = c.fetchone()[0]
    
    if not latest_info and total > 0:
        c.execute('SELECT close FROM kline_data WHERE stock_code = %s ORDER BY date DESC LIMIT 1', (code,))
        last_close = c.fetchone()
        latest_info = {'price': last_close[0] if last_close else 0, 'pe': 0, 'pb': 0}
    
    if latest_info and (latest_info.get('pe', 0) > 0 or latest_info.get('pb', 0) > 0):
        try:
            c.execute('''UPDATE stocks SET last_pe=%s, last_pb=%s, last_price=%s WHERE code=%s''',
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
    conn = get_connection()
    c = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    c.execute('SELECT date, open, close, high, low, volume FROM kline_data WHERE stock_code = %s ORDER BY date', (code,))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows

def save_stock_info(code, name, exchange, total_shares, industry, model_type,
                    pe_min, pe_max, pb_min, pb_max, eps_growth,
                    revenue, net_profit, gross_margin, market_cap, subtitle,
                    extra_factors='{}'):
    """保存/更新股票基本信息"""
    ensure_db()
    conn = get_connection()
    c = conn.cursor()
    c.execute('''INSERT INTO stocks 
        (code, name, exchange, total_shares, industry, model_type,
         pe_min, pe_max, pb_min, pb_max, eps_growth,
         revenue, net_profit, gross_margin, market_cap, subtitle, extra_factors, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
        ON CONFLICT(code) DO UPDATE SET
         name=EXCLUDED.name, exchange=EXCLUDED.exchange, total_shares=EXCLUDED.total_shares,
         industry=EXCLUDED.industry, model_type=EXCLUDED.model_type,
         pe_min=EXCLUDED.pe_min, pe_max=EXCLUDED.pe_max, pb_min=EXCLUDED.pb_min, pb_max=EXCLUDED.pb_max,
         eps_growth=EXCLUDED.eps_growth, revenue=EXCLUDED.revenue, net_profit=EXCLUDED.net_profit,
         gross_margin=EXCLUDED.gross_margin, market_cap=EXCLUDED.market_cap,
         subtitle=EXCLUDED.subtitle, extra_factors=EXCLUDED.extra_factors,
         updated_at=NOW()''',
        (code, name, exchange, total_shares, industry, model_type,
         pe_min, pe_max, pb_min, pb_max, eps_growth,
         revenue, net_profit, gross_margin, market_cap, subtitle, extra_factors))
    conn.commit()
    conn.close()

def get_stock_info(code):
    """读取股票基本信息"""
    ensure_db()
    conn = get_connection()
    c = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    c.execute('SELECT * FROM stocks WHERE code = %s', (code,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None

def list_stocks():
    """列出所有已存储的股票"""
    ensure_db()
    conn = get_connection()
    c = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    c.execute('SELECT code, name, exchange, industry, model_type, updated_at FROM stocks ORDER BY code')
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows

def save_report_meta(code, report_file, params=''):
    """记录报告生成信息"""
    ensure_db()
    conn = get_connection()
    c = conn.cursor()
    c.execute('''INSERT INTO reports_meta (code, report_file, generated_at, params)
        VALUES (%s, %s, NOW(), %s)
        ON CONFLICT(code) DO UPDATE SET
        report_file=EXCLUDED.report_file, generated_at=NOW(), params=EXCLUDED.params''',
        (code, report_file, params))
    conn.commit()
    conn.close()

def get_report_meta(code):
    """读取报告生成信息"""
    ensure_db()
    conn = get_connection()
    c = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    c.execute('SELECT * FROM reports_meta WHERE code = %s', (code,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None

def db_stats():
    """数据库统计信息"""
    ensure_db()
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT COUNT(DISTINCT stock_code) FROM kline_data')
    stock_count = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM kline_data')
    total_rows = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM valuation_history')
    val_rows = c.fetchone()[0]
    c.execute("SELECT pg_database_size(current_database()) / 1024")
    db_size = c.fetchone()[0]
    conn.close()
    return {'stocks': stock_count, 'kline_rows': total_rows, 'valuation_rows': val_rows, 'db_size_kb': round(db_size, 1)}

def save_valuation_history(stock_code, results):
    """批量保存估值评分历史到数据库
    results: list of dict, 每条含 date, close, score, pe_ttm, pb 等字段
    """
    ensure_db()
    conn = get_connection()
    c = conn.cursor()
    psycopg2.extras.execute_batch(c,
        '''INSERT INTO valuation_history 
            (stock_code, date, score, pe, pb, price, pe_score, pb_score, peg_score, 
             ma_score, volatility_score, volume_score)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (stock_code, date) DO UPDATE SET
            score=EXCLUDED.score, pe=EXCLUDED.pe, pb=EXCLUDED.pb, price=EXCLUDED.price,
            pe_score=EXCLUDED.pe_score, pb_score=EXCLUDED.pb_score, peg_score=EXCLUDED.peg_score,
            ma_score=EXCLUDED.ma_score, volatility_score=EXCLUDED.volatility_score, 
            volume_score=EXCLUDED.volume_score''',
        [(stock_code, r['date'], r.get('score', 0),
          r.get('pe_ttm', 0), r.get('pb', 0), r.get('close', 0),
          r.get('s_pe', 0), r.get('s_pb', 0), r.get('s_peg', 0),
          r.get('s_ma', 0), r.get('s_vola', 0), r.get('s_vol', 0)) for r in results])
    conn.commit()
    conn.close()

def get_valuation_history(stock_code):
    """从数据库读取估值评分历史
    返回: list of dict, 含 date, close, score, pe, pb 等
    """
    ensure_db()
    conn = get_connection()
    c = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    c.execute('''SELECT date, score, pe, pb, price FROM valuation_history 
                 WHERE stock_code = %s ORDER BY date''', (stock_code,))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows

def list_valuation_stocks():
    """列出数据库中有估值历史的所有股票"""
    ensure_db()
    conn = get_connection()
    c = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    c.execute('''SELECT DISTINCT vh.stock_code, s.name, s.industry, s.model_type,
                 COUNT(vh.date) as days, MAX(vh.date) as latest_date,
                 (SELECT score FROM valuation_history WHERE stock_code = vh.stock_code ORDER BY date DESC LIMIT 1) as latest_score
                 FROM valuation_history vh
                 LEFT JOIN stocks s ON vh.stock_code = s.code
                 GROUP BY vh.stock_code, s.name, s.industry, s.model_type
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
        ensure_db()
        print("数据库已初始化")
    
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
