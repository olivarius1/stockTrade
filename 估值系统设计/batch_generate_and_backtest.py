#!/usr/bin/env python3
"""批量生成估值报告并回测"""
import subprocess, os, json, time

STOCKS = [
    # (code, name, exchange, total_shares, pe_min, pe_max, pb_min, pb_max, eps_growth, revenue, net_profit, gross_margin, market_cap, industry, model_type)
    ("601668", "中国建筑", "sh", 100, 5, 30, 0.8, 4.0, 0.15, 0, 0, 0, 1938, "建筑装饰", "soe"),
    ("601390", "中国中铁", "sh", 100, 5, 30, 0.8, 4.0, 0.15, 0, 0, 0, 880, "建筑装饰", "soe"),
    ("600019", "宝钢股份", "sh", 100, 5, 30, 0.8, 4.0, 0.15, 0, 0, 0, 1199, "钢铁", "cyclical"),
    ("601898", "中煤能源", "sh", 100, 5, 30, 0.8, 4.0, 0.15, 0, 0, 0, 1213, "采掘", "cyclical"),
    ("601186", "中国铁建", "sh", 100, 5, 30, 0.8, 4.0, 0.15, 0, 0, 0, 718, "建筑装饰", "soe"),
    ("601857", "中国石油", "sh", 100, 5, 30, 0.8, 4.0, 0.15, 0, 0, 0, 16192, "采掘", "soe"),
    ("601600", "中国铝业", "sh", 100, 5, 30, 0.8, 4.0, 0.15, 0, 0, 0, 1170, "有色金属", "cyclical"),
    ("601088", "中国神华", "sh", 100, 5, 30, 0.8, 4.0, 0.15, 0, 0, 0, 7160, "采掘", "soe"),
    ("601225", "陕西煤业", "sh", 100, 5, 30, 0.8, 4.0, 0.15, 0, 0, 0, 2380, "采掘", "cyclical"),
    ("600219", "南山铝业", "sh", 100, 5, 30, 0.8, 4.0, 0.15, 0, 0, 0, 478, "有色金属", "cyclical"),
    ("000933", "神火股份", "sz", 100, 5, 30, 0.8, 4.0, 0.15, 0, 0, 0, 555, "有色金属", "cyclical"),
    ("600096", "云天化", "sh", 100, 5, 30, 0.8, 4.0, 0.15, 0, 0, 0, 506, "化工", "cyclical"),
    ("600309", "万华化学", "sh", 100, 5, 30, 0.8, 4.0, 0.15, 0, 0, 0, 2179, "化工", "cyclical"),
    ("601618", "中国中冶", "sh", 100, 5, 30, 0.8, 4.0, 0.15, 0, 0, 0, 461, "建筑装饰", "soe"),
    ("600036", "招商银行", "sh", 100, 5, 30, 0.8, 4.0, 0.15, 0, 0, 0, 7670, "银行", "bank"),
    ("601318", "中国平安", "sh", 100, 5, 30, 0.8, 4.0, 0.15, 0, 0, 0, 5287, "保险", "bank"),
    ("601398", "工商银行", "sh", 100, 5, 30, 0.8, 4.0, 0.15, 0, 0, 0, 20221, "银行", "bank"),
    ("000001", "平安银行", "sz", 100, 5, 30, 0.8, 4.0, 0.15, 0, 0, 0, 2074, "银行", "bank"),
    ("601919", "中远海控", "sh", 100, 5, 30, 0.8, 4.0, 0.15, 0, 0, 0, 1809, "航运", "cyclical"),
    ("601988", "中国银行", "sh", 100, 5, 30, 0.8, 4.0, 0.15, 0, 0, 0, 12372, "银行", "bank"),
]

def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    print("="*60)
    print("批量生成估值报告")
    print("="*60)
    
    success = 0
    skip = 0
    fail = 0
    
    for s in STOCKS:
        code, name = s[0], s[1]
        fname = f"tbea-valuation/{name}{code}-valuation.html"
        
        if os.path.exists(fname):
            print(f"  跳过: {name}{code} (已存在)")
            skip += 1
            continue
        
        cmd = [
            "python3", "scripts/build_report.py",
            code, name, s[2], str(s[3]),
            str(s[4]), str(s[5]), str(s[6]), str(s[7]), str(s[8]),
            str(s[9]), str(s[10]), str(s[11]), str(s[12]),
            s[13], "批量筛选", s[14]
        ]
        
        print(f"  生成: {name}{code}...", end="", flush=True)
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if result.returncode == 0:
                print(" ✓")
                success += 1
            else:
                print(f" ✗ ({result.stderr[:100]})")
                fail += 1
        except Exception as e:
            print(f" ✗ ({e})")
            fail += 1
    
    print(f"\n生成完成: 成功{success} 跳过{skip} 失败{fail}")
    
    print("\n" + "="*60)
    print("运行回测")
    print("="*60)
    
    result = subprocess.run(
        ["python3", "generate_backtest_report.py"],
        capture_output=True, text=True, timeout=300
    )
    print(result.stdout)
    if result.stderr:
        print(result.stderr)

if __name__ == "__main__":
    main()
