#!/usr/bin/env python3
"""将已有HTML估值报告中的数据迁移到统一数据库"""
import re, json, os, sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scripts'))
from db_manager import ensure_db, save_valuation_history, save_stock_info, get_valuation_history

def migrate():
    ensure_db()
    reports_dir = "tbea-valuation"
    if not os.path.exists(reports_dir):
        print("tbea-valuation 目录不存在")
        return
    
    html_files = sorted([f for f in os.listdir(reports_dir) if f.endswith("-valuation.html")])
    print(f"发现 {len(html_files)} 个估值报告")
    
    migrated = 0
    skipped = 0
    
    for fname in html_files:
        path = os.path.join(reports_dir, fname)
        with open(path) as f:
            content = f.read()
        
        match = re.search(r'var VALUATION_DATA\s*=\s*({.*?});', content, re.DOTALL)
        if not match:
            print(f"  跳过: {fname} (无VALUATION_DATA)")
            skipped += 1
            continue
        
        jdata = json.loads(match.group(1))
        meta = jdata.get('meta', {})
        data = jdata.get('data', [])
        
        if len(data) < 10:
            print(f"  跳过: {fname} (数据太少)")
            skipped += 1
            continue
        
        code = meta.get('code', fname[:6])
        name = meta.get('stock', '').split('(')[0] or code
        exchange = meta.get('exchange', 'sh')
        industry = meta.get('description', '')
        model_type = meta.get('model_type', 'cyclical')
        
        # 检查是否已有数据
        existing = get_valuation_history(code)
        if existing and len(existing) >= len(data):
            print(f"  跳过: {name}({code}) 已有{len(existing)}条数据")
            skipped += 1
            continue
        
        # 保存估值历史
        save_valuation_history(code, data)
        
        # 保存股票基本信息
        save_stock_info(
            code, name, exchange,
            meta.get('total_shares', 0),
            industry, model_type,
            meta.get('pe_min', 5), meta.get('pe_max', 30),
            meta.get('pb_min', 0.8), meta.get('pb_max', 4.0),
            meta.get('eps_growth', 0.1),
            '', '', '', '', '',
            '{}'
        )
        
        print(f"  迁移: {name}({code}) {len(data)}条")
        migrated += 1
    
    print(f"\n迁移完成: 成功{migrated} 跳过{skipped}")

if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    migrate()
