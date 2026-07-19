#!/usr/bin/env python3
"""
SQLite → PostgreSQL 数据迁移脚本

用法:
  1. 确保 PostgreSQL 已启动且表已创建（init_db.py 已执行）
  2. 将 SQLite 数据库文件放到可访问的路径
  3. 执行: python scripts/migrate_sqlite_to_pg.py [sqlite_db_path]
  
  Docker 环境中:
    docker-compose exec backend python scripts/migrate_sqlite_to_pg.py /app/data/valuation.db
"""
import sqlite3
import psycopg2
import psycopg2.extras
import os
import sys
from datetime import datetime

# SQLite 数据库路径（默认值）
DEFAULT_SQLITE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'data', 'valuation.db'
)

def get_pg_connection():
    """获取 PostgreSQL 连接"""
    db_url = os.environ.get('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/valuation')
    return psycopg2.connect(db_url)

def get_sqlite_connection(db_path):
    """获取 SQLite 连接"""
    if not os.path.exists(db_path):
        print(f"错误: SQLite 数据库文件不存在: {db_path}")
        sys.exit(1)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def get_sqlite_tables(sqlite_conn):
    """获取 SQLite 中的所有用户表"""
    c = sqlite_conn.cursor()
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    return [row[0] for row in c.fetchall()]

def migrate_stocks(sqlite_conn, pg_conn):
    """迁移 stocks 表"""
    print("  迁移 stocks 表...")
    sc = sqlite_conn.cursor()
    sc.execute("SELECT * FROM stocks")
    rows = sc.fetchall()
    if not rows:
        print("    无数据")
        return 0
    
    pc = pg_conn.cursor()
    count = 0
    for row in rows:
        d = dict(row)
        pc.execute('''
            INSERT INTO stocks (code, name, exchange, total_shares, industry, model_type,
                pe_min, pe_max, pb_min, pb_max, eps_growth, revenue, net_profit,
                gross_margin, market_cap, subtitle, extra_factors,
                last_pe, last_pb, last_price, updated_at)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (code) DO NOTHING
        ''', (
            d['code'], d['name'], d['exchange'], d['total_shares'], d['industry'],
            d['model_type'], d['pe_min'], d['pe_max'], d['pb_min'], d['pb_max'],
            d['eps_growth'], d['revenue'], d['net_profit'], d['gross_margin'],
            d['market_cap'], d['subtitle'], d['extra_factors'],
            d['last_pe'], d['last_pb'], d['last_price'], d['updated_at']
        ))
        count += 1
    pg_conn.commit()
    print(f"    迁移 {count} 条")
    return count

def migrate_kline_data(sqlite_conn, pg_conn):
    """迁移 kline_data 表（批量插入优化）"""
    print("  迁移 kline_data 表...")
    sc = sqlite_conn.cursor()
    sc.execute("SELECT stock_code, date, open, high, low, close, volume, amount FROM kline_data")
    rows = sc.fetchall()
    if not rows:
        print("    无数据")
        return 0
    
    pc = pg_conn.cursor()
    batch = [(r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7]) for r in rows]
    psycopg2.extras.execute_batch(pc,
        '''INSERT INTO kline_data (stock_code, date, open, high, low, close, volume, amount)
           VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
           ON CONFLICT (stock_code, date) DO NOTHING''',
        batch, page_size=5000
    )
    pg_conn.commit()
    count = len(batch)
    print(f"    迁移 {count} 条")
    return count

def migrate_valuation_history(sqlite_conn, pg_conn):
    """迁移 valuation_history 表"""
    print("  迁移 valuation_history 表...")
    sc = sqlite_conn.cursor()
    sc.execute('''SELECT stock_code, date, score, pe_score, pb_score, peg_score,
                  ma_score, volatility_score, volume_score, roe_score, dividend_score,
                  ai_score, pe, pb, price FROM valuation_history''')
    rows = sc.fetchall()
    if not rows:
        print("    无数据")
        return 0
    
    pc = pg_conn.cursor()
    batch = [tuple(r) for r in rows]
    psycopg2.extras.execute_batch(pc,
        '''INSERT INTO valuation_history (stock_code, date, score, pe_score, pb_score, peg_score,
           ma_score, volatility_score, volume_score, roe_score, dividend_score,
           ai_score, pe, pb, price)
           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
           ON CONFLICT (stock_code, date) DO NOTHING''',
        batch, page_size=5000
    )
    pg_conn.commit()
    count = len(batch)
    print(f"    迁移 {count} 条")
    return count

def migrate_reports_meta(sqlite_conn, pg_conn):
    """迁移 reports_meta 表"""
    print("  迁移 reports_meta 表...")
    sc = sqlite_conn.cursor()
    sc.execute("SELECT code, report_file, generated_at, params FROM reports_meta")
    rows = sc.fetchall()
    if not rows:
        print("    无数据")
        return 0
    
    pc = pg_conn.cursor()
    count = 0
    for row in rows:
        d = dict(row)
        pc.execute('''
            INSERT INTO reports_meta (code, report_file, generated_at, params)
            VALUES (%s,%s,%s,%s)
            ON CONFLICT (code) DO NOTHING
        ''', (d['code'], d['report_file'], d['generated_at'], d['params']))
        count += 1
    pg_conn.commit()
    print(f"    迁移 {count} 条")
    return count

def migrate_sqlalchemy_table(sqlite_conn, pg_conn, table_name, columns, conflict_col, bool_columns=None):
    """通用迁移函数：迁移 SQLAlchemy 管理的表"""
    print(f"  迁移 {table_name} 表...")
    sc = sqlite_conn.cursor()
    
    # 检查表是否存在于 SQLite
    sc.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
    if not sc.fetchone():
        print(f"    表不存在，跳过")
        return 0
    
    col_list = ', '.join(columns)
    placeholders = ', '.join(['%s'] * len(columns))
    
    sc.execute(f"SELECT {col_list} FROM {table_name}")
    rows = sc.fetchall()
    if not rows:
        print("    无数据")
        return 0
    
    # 转换 boolean 列（SQLite 存 0/1，PG 需要 True/False）
    bool_indices = []
    if bool_columns:
        for bc in bool_columns:
            if bc in columns:
                bool_indices.append(columns.index(bc))
    
    converted_rows = []
    for row in rows:
        r = list(row)
        for idx in bool_indices:
            r[idx] = bool(r[idx]) if r[idx] is not None else None
        converted_rows.append(tuple(r))
    
    pc = pg_conn.cursor()
    
    if conflict_col:
        sql = f'''INSERT INTO {table_name} ({col_list}) VALUES ({placeholders})
                  ON CONFLICT ({conflict_col}) DO NOTHING'''
    else:
        sql = f'''INSERT INTO {table_name} ({col_list}) VALUES ({placeholders})'''
    
    psycopg2.extras.execute_batch(pc, sql, converted_rows, page_size=1000)
    pg_conn.commit()
    count = len(converted_rows)
    print(f"    迁移 {count} 条")
    return count

def main():
    sqlite_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_SQLITE_PATH
    
    print(f"=" * 60)
    print(f"SQLite → PostgreSQL 数据迁移")
    print(f"=" * 60)
    print(f"SQLite 路径: {sqlite_path}")
    print(f"PostgreSQL: {os.environ.get('DATABASE_URL', 'postgresql://...')}")
    print()
    
    # 连接数据库
    sqlite_conn = get_sqlite_connection(sqlite_path)
    pg_conn = get_pg_connection()
    
    # 确保 kline_manager 管理的表存在（stocks, reports_meta 等不在 SQLAlchemy 模型中）
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'app', 'data'))
    from kline_manager import ensure_db
    ensure_db()
    print("PostgreSQL 表已就绪")
    print()
    # 显示 SQLite 中的表
    sqlite_tables = get_sqlite_tables(sqlite_conn)
    print(f"SQLite 中的表: {', '.join(sqlite_tables)}")
    print()
    
    # 开始迁移
    stats = {}
    start_time = datetime.now()
    
    print("开始迁移:")
    
    # 迁移 kline_manager 管理的表
    if 'stocks' in sqlite_tables:
        stats['stocks'] = migrate_stocks(sqlite_conn, pg_conn)
    if 'kline_data' in sqlite_tables:
        stats['kline_data'] = migrate_kline_data(sqlite_conn, pg_conn)
    if 'valuation_history' in sqlite_tables:
        stats['valuation_history'] = migrate_valuation_history(sqlite_conn, pg_conn)
    if 'reports_meta' in sqlite_tables:
        stats['reports_meta'] = migrate_reports_meta(sqlite_conn, pg_conn)
    
    # 迁移 SQLAlchemy 管理的表
    sqlalchemy_tables = {
        'watchlist': {
            'columns': ['stock_code', 'stock_name', 'industry', 'model_type', 'ai_enabled', 'created_at', 'updated_at'],
            'conflict_col': 'stock_code',
            'bool_columns': ['ai_enabled']
        },
        'scheduler_config': {
            'columns': ['schedule_type', 'cron_expression', 'enabled', 'include_ai', 'financial_update_frequency', 'updated_at'],
            'conflict_col': None,
            'bool_columns': ['enabled', 'include_ai']
        },
        'model_config': {
            'columns': ['model_code', 'model_name', 'factors', 'weights', 'params', 'enabled', 'updated_at'],
            'conflict_col': 'model_code',
            'bool_columns': ['enabled']
        },
        'users': {
            'columns': ['username', 'hashed_password', 'created_at'],
            'conflict_col': 'username'
        },
        'financial_data': {
            'columns': ['stock_code', 'report_date', 'eps', 'revenue', 'net_profit', 'roe', 'gross_margin', 'dividend_rate', 'updated_at'],
            'conflict_col': None
        },
    }
    
    for table_name, config in sqlalchemy_tables.items():
        if table_name in sqlite_tables:
            stats[table_name] = migrate_sqlalchemy_table(
                sqlite_conn, pg_conn, table_name,
                config['columns'], config['conflict_col'],
                config.get('bool_columns')
            )
    
    elapsed = (datetime.now() - start_time).total_seconds()
    
    # 输出统计
    print()
    print(f"=" * 60)
    print(f"迁移完成! 耗时 {elapsed:.1f} 秒")
    print(f"=" * 60)
    total = sum(stats.values())
    for table, count in stats.items():
        print(f"  {table}: {count} 条")
    print(f"  总计: {total} 条")
    
    # 验证 PostgreSQL 数据
    print()
    print("PostgreSQL 数据统计:")
    pc = pg_conn.cursor()
    for table in stats:
        pc.execute(f"SELECT COUNT(*) FROM {table}")
        pg_count = pc.fetchone()[0]
        print(f"  {table}: {pg_count} 条")
    
    sqlite_conn.close()
    pg_conn.close()
    print()
    print("迁移完成!")

if __name__ == '__main__':
    main()
