#!/usr/bin/env python3
import re, json, math, os, subprocess, sys

# 改进后的回测参数
BUY_COST = 0.0003    # 买入佣金
SELL_COST = 0.0013   # 卖出佣金+印花税
ROLLING_WINDOW = 250 # 滚动窗口天数
BUY_THRESHOLD = 95   # 百分位>95%买入
SELL_THRESHOLD = 40  # 百分位<40%卖出
INITIAL_CAPITAL = 100000

NEW_STOCKS = [
    ("002959", "小熊电器", "sz", "tech",      3.26, 10, 50, 2.0, 8.0, 0.15, "小家电"),
    ("000726", "鲁泰A",    "sz", "staples",   10.1,  8, 30, 1.0, 4.0, 0.10, "纺织服装"),
    ("600738", "丽尚国潮", "sh", "soe",       4.12,  6, 30, 0.8, 3.0, 0.12, "商业零售"),
    ("600617", "国新能源", "sh", "soe",       7.52,  6, 30, 0.8, 3.0, 0.08, "新能源"),
    ("600989", "宝丰能源", "sh", "cyclical",  30.8,  5, 25, 0.8, 3.5, 0.20, "煤化工"),
    ("600595", "中孚实业", "sh", "cyclical",  28.5,  5, 25, 0.8, 3.0, 0.15, "铝业"),
    ("600861", "北京人力", "sh", "soe",       3.18, 10, 40, 1.0, 4.0, 0.12, "人力资源"),
    ("000807", "云铝股份", "sz", "cyclical",  22.1,  5, 25, 0.8, 3.0, 0.18, "铝业"),
]

EXISTING_STOCKS = [
    ("301087", "可孚医疗", "sz"),
    ("002461", "珠江啤酒", "sz"),
    ("002768", "国恩股份", "sz"),
    ("688236", "春立医疗", "sh"),
    ("300030", "阳普医疗", "sz"),
    ("601022", "宁波远洋", "sh"),
    ("688016", "心脉医疗", "sh"),
    ("301507", "民生健康", "sz"),
    ("601808", "中海油服", "sh"),
    ("601899", "紫金矿业", "sh"),
]

def generate_report(code, name, exchange, total_shares, pe_min, pe_max, pb_min, pb_max, eps_growth, industry, model_type):
    fname = f"{name}{code}-valuation.html"
    if os.path.exists(f"tbea-valuation/{fname}"):
        print(f"  跳过: {fname} 已存在")
        return fname
    
    cmd = [
        "python3", "../app/data/report_generator.py",
        code, name, exchange, str(total_shares),
        str(pe_min), str(pe_max), str(pb_min), str(pb_max),
        str(eps_growth), "0", "0", "0", "0", industry, "test", model_type
    ]
    print(f"  生成: {name}{code}...")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            print(f"    失败: {result.stderr[:200]}")
            return None
        print(f"    成功")
        return fname
    except Exception as e:
        print(f"    异常: {e}")
        return None

def backtest_from_report(fname):
    path = f"tbea-valuation/{fname}"
    if not os.path.exists(path):
        return None
    
    try:
        with open(path) as f:
            content = f.read()
        
        match = re.search(r'var VALUATION_DATA\s*=\s*({.*?});', content, re.DOTALL)
        if not match:
            return None
        
        jdata = json.loads(match.group(1))
        data = jdata.get("data", [])
        if len(data) < 100:
            return None
        
        capital = INITIAL_CAPITAL
        shares = 0
        in_position = False
        trades = []
        equity_curve = []
        
        for i, d in enumerate(data):
            window_start = max(0, i - ROLLING_WINDOW + 1)
            hist_scores = [x["score"] for x in data[window_start:i+1]]
            if len(hist_scores) < 30:
                pct_rank = 50
            else:
                pct_rank = sum(1 for s in hist_scores if s <= d["score"]) / len(hist_scores) * 100
            
            close = d["close"]
            
            if not in_position and pct_rank > BUY_THRESHOLD:
                shares = capital * (1 - BUY_COST) / close
                capital = 0
                in_position = True
                trades.append({"date": d["date"], "type": "买入", "price": close, "pct": pct_rank})
            
            elif in_position and pct_rank < SELL_THRESHOLD:
                capital = shares * close * (1 - SELL_COST)
                shares = 0
                in_position = False
                trades.append({"date": d["date"], "type": "卖出", "price": close, "pct": pct_rank})
            
            if in_position:
                equity = shares * close
            else:
                equity = capital
            equity_curve.append({"date": d["date"], "equity": equity})
        
        if in_position:
            capital = shares * data[-1]["close"]
        
        total_return = (capital - INITIAL_CAPITAL) / INITIAL_CAPITAL * 100
        days = len(data) - 1
        years = days / 365
        annual_return = ((capital / INITIAL_CAPITAL) ** (1/years) - 1) * 100 if years > 0 else 0
        
        max_equity = INITIAL_CAPITAL
        max_drawdown = 0
        for ec in equity_curve:
            if ec["equity"] > max_equity:
                max_equity = ec["equity"]
            dd = (max_equity - ec["equity"]) / max_equity * 100
            if dd > max_drawdown:
                max_drawdown = dd
        
        winning_trades = 0
        losing_trades = 0
        for i in range(0, len(trades)-1, 2):
            buy = trades[i]
            sell = trades[i+1]
            if sell["price"] > buy["price"]:
                winning_trades += 1
            else:
                losing_trades += 1
        win_rate = winning_trades / (winning_trades + losing_trades) * 100 if (winning_trades + losing_trades) > 0 else 0
        
        return {
            "name": fname.replace("-valuation.html", ""),
            "days": days,
            "years": years,
            "initial": INITIAL_CAPITAL,
            "final": capital,
            "total_return": total_return,
            "annual_return": annual_return,
            "trades": len(trades),
            "buy_signals": sum(1 for t in trades if t["type"] == "买入"),
            "max_drawdown": max_drawdown,
            "win_rate": win_rate,
            "latest_score": data[-1]["score"],
            "latest_pct": sum(1 for s in [x["score"] for x in data] if s <= data[-1]["score"]) / len(data) * 100,
            "latest_price": data[-1]["close"],
            "trades_detail": trades,
        }
    except Exception as e:
        print(f"  回测失败: {e}")
        return None

def main():
    print("="*70)
    print("批量回测系统 v2.0（含交易成本、滚动窗口）")
    print("="*70)
    
    print("\n【步骤1】为新标的生成估值报告...")
    for code, name, exchange, model_type, total_shares, pe_min, pe_max, pb_min, pb_max, eps_growth, industry in NEW_STOCKS:
        generate_report(code, name, exchange, total_shares, pe_min, pe_max, pb_min, pb_max, eps_growth, industry, model_type)
    
    print("\n【步骤2】执行回测...")
    results = []
    
    for code, name, exchange in EXISTING_STOCKS:
        fname = f"{name}{code}-valuation.html"
        print(f"\n  回测: {name}{code}")
        result = backtest_from_report(fname)
        if result:
            results.append(result)
            print(f"    总收益: {result['total_return']:.1f}% | 年化: {result['annual_return']:.1f}% | 最大回撤: {result['max_drawdown']:.1f}% | 交易: {result['trades']}次")
        else:
            print(f"    失败: 未找到报告")
    
    for code, name, exchange, _, _, _, _, _, _, _, _ in NEW_STOCKS:
        fname = f"{name}{code}-valuation.html"
        print(f"\n  回测: {name}{code}")
        result = backtest_from_report(fname)
        if result:
            results.append(result)
            print(f"    总收益: {result['total_return']:.1f}% | 年化: {result['annual_return']:.1f}% | 最大回撤: {result['max_drawdown']:.1f}% | 交易: {result['trades']}次")
        else:
            print(f"    失败: 未找到报告")
    
    print("\n" + "="*70)
    print("【汇总结果】")
    print("="*70)
    print(f"\n{'股票':<15} {'天数':>6} {'年数':>5} {'总收益':>8} {'年化':>7} {'回撤':>7} {'交易':>6} {'胜率':>6} {'最新价':>8} {'估值分':>6} {'百分位':>7}")
    print("-" * 100)
    
    total_return_sum = 0
    positive_count = 0
    for r in sorted(results, key=lambda x: x["total_return"], reverse=True):
        sign = "+" if r["total_return"] > 0 else ""
        if r["total_return"] > 0:
            positive_count += 1
        total_return_sum += r["total_return"]
        print(f"{r['name']:<15} {r['days']:>6} {r['years']:>4.1f}年 {sign}{r['total_return']:>7.1f}% {sign}{r['annual_return']:>6.1f}% {r['max_drawdown']:>6.1f}% {r['trades']:>6} {r['win_rate']:>5.0f}% {r['latest_price']:>8} {r['latest_score']:>6.1f} {r['latest_pct']:>6.1f}%")
    
    print("-" * 100)
    avg_return = total_return_sum / len(results) if results else 0
    print(f"{'合计':<15} {'':>6} {'':>5} {'':>8} {'':>7} {'':>7} {'':>6} {'':>6} {'':>8} {'':>6} {'':>7}")
    print(f"{'统计':<15} {'':>6} {'':>5} {f'平均{avg_return:.1f}%':>8} {'':>7} {'':>7} {f'{positive_count}/{len(results)}正收益':>12}")
    
    print("\n" + "="*70)
    print("策略参数:")
    print(f"  买入阈值: 百分位 > {BUY_THRESHOLD}%")
    print(f"  卖出阈值: 百分位 < {SELL_THRESHOLD}%")
    print(f"  滚动窗口: {ROLLING_WINDOW}天")
    print(f"  交易成本: 买入{BUY_COST*100:.2f}% / 卖出{SELL_COST*100:.2f}%")
    print(f"  初始资金: {INITIAL_CAPITAL:,}元")
    print("="*70)

if __name__ == "__main__":
    main()
