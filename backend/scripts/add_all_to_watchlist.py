#!/usr/bin/env python3
"""
批量将数据库中所有有估值历史的股票加入自选股
"""
import sqlite3
import os

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_BACKEND_DIR = os.path.dirname(_SCRIPT_DIR)
DB_PATH = os.path.join(_BACKEND_DIR, 'data', 'valuation.db')

def get_stocks_with_valuation():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    c.execute('''
        SELECT DISTINCT vh.stock_code, s.name, s.industry, s.model_type
        FROM valuation_history vh
        LEFT JOIN stocks s ON vh.stock_code = s.code
        ORDER BY vh.stock_code
    ''')
    stocks = [dict(r) for r in c.fetchall()]
    conn.close()
    return stocks

def get_existing_watchlist():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT stock_code FROM watchlist')
    existing = {r['stock_code'] for r in c.fetchall()}
    conn.close()
    return existing

def add_to_watchlist(stock_code, stock_name, industry, model_type):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    try:
        c.execute('''
            INSERT INTO watchlist (stock_code, stock_name, industry, model_type, ai_enabled, created_at)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (stock_code, stock_name, industry or '', model_type or 'cyclical', False))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False

def main():
    stocks = get_stocks_with_valuation()
    existing = get_existing_watchlist()
    
    print(f"数据库中有估值历史的股票: {len(stocks)} 只")
    print(f"已有自选股: {len(existing)} 只")
    
    added = 0
    skipped = 0
    
    for stock in stocks:
        code = stock['stock_code']
        name = stock['name'] or '未知名称'
        industry = stock['industry'] or '未知行业'
        model_type = stock['model_type'] or 'cyclical'
        
        if code in existing:
            print(f"  跳过: {code} {name} (已在自选股中)")
            skipped += 1
        else:
            success = add_to_watchlist(code, name, industry, model_type)
            if success:
                print(f"  添加: {code} {name} [{model_type}]")
                added += 1
            else:
                print(f"  失败: {code} {name}")
                skipped += 1
    
    print(f"\n完成! 新增 {added} 只，跳过 {skipped} 只")

if __name__ == '__main__':
    main()
