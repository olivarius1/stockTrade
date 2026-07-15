#!/usr/bin/env python3
import re, json, math, os, sys
from datetime import datetime

BUY_COST = 0.0003
SELL_COST = 0.0013
ROLLING_WINDOW = 250
BUY_THRESHOLD = 95
SELL_THRESHOLD = 40
STOP_LOSS = 0.30  # 止损线30%
INITIAL_CAPITAL = 100000

# 统一使用数据库
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scripts'))
from db_manager import get_valuation_history, list_valuation_stocks, ensure_db

def backtest_from_db(stock_code, stock_name=None):
    """从数据库读取估值历史进行回测"""
    data = get_valuation_history(stock_code)
    if len(data) < 100:
        return None
    
    # 转换字段名（数据库 price 即 close）
    for d in data:
        d['close'] = d.get('price', 0)
    
    capital = INITIAL_CAPITAL
    shares = 0
    in_position = False
    trades = []
    equity_curve = []
    buy_date = None
    buy_price = 0
    stop_loss_count = 0
    hold_days_list = []
    
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
            buy_date = d["date"]
            buy_price = close
            trades.append({
                "date": d["date"], "type": "买入", "price": close, "pct": pct_rank,
                "shares": shares, "capital": INITIAL_CAPITAL, "hold_days": 0,
                "reason": "百分位>95%"
            })
        
        elif in_position:
            # 判断是否触发止损（持仓亏损达到30%）
            loss_pct = (buy_price - close) / buy_price
            trigger_stop_loss = loss_pct >= STOP_LOSS
            
            if trigger_stop_loss:
                sell_value = shares * close * (1 - SELL_COST)
                capital = sell_value
                shares = 0
                in_position = False
                stop_loss_count += 1
                
                hold_days = (datetime.strptime(d["date"], "%Y-%m-%d") - datetime.strptime(buy_date, "%Y-%m-%d")).days
                hold_days_list.append(hold_days)
                
                trades.append({
                    "date": d["date"], "type": "止损卖出", "price": close, "pct": pct_rank,
                    "shares": 0, "capital": capital, "hold_days": hold_days,
                    "reason": f"亏损{loss_pct*100:.1f}%触发止损"
                })
                buy_date = None
                buy_price = 0
            
            elif pct_rank < SELL_THRESHOLD:
                sell_value = shares * close * (1 - SELL_COST)
                capital = sell_value
                shares = 0
                in_position = False
                
                hold_days = (datetime.strptime(d["date"], "%Y-%m-%d") - datetime.strptime(buy_date, "%Y-%m-%d")).days
                hold_days_list.append(hold_days)
                
                trades.append({
                    "date": d["date"], "type": "卖出", "price": close, "pct": pct_rank,
                    "shares": 0, "capital": capital, "hold_days": hold_days,
                    "reason": "百分位<40%"
                })
                buy_date = None
                buy_price = 0
        
        if in_position:
            equity = shares * close
        else:
            equity = capital
        equity_curve.append({"date": d["date"], "equity": equity})
    
    if in_position:
        capital = shares * data[-1]["close"]
        if buy_date:
            hold_days = (datetime.strptime(data[-1]["date"], "%Y-%m-%d") - datetime.strptime(buy_date, "%Y-%m-%d")).days
            hold_days_list.append(hold_days)
    
    total_return = (capital - INITIAL_CAPITAL) / INITIAL_CAPITAL * 100
    days = len(data) - 1
    years = days / 365
    if capital > 0 and INITIAL_CAPITAL > 0:
        if capital / INITIAL_CAPITAL > 0 and years > 0:
            annual_return = ((capital / INITIAL_CAPITAL) ** (1/years) - 1) * 100
        else:
            annual_return = -100
    else:
        annual_return = 0
    
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
    total_pnl = 0
    for i in range(0, len(trades)-1, 2):
        buy = trades[i]
        sell = trades[i+1]
        pnl = sell["capital"] - INITIAL_CAPITAL if i == 0 else sell["capital"] - trades[i-1]["capital"]
        total_pnl += pnl
        if sell["price"] > buy["price"]:
            winning_trades += 1
        else:
            losing_trades += 1
    win_rate = winning_trades / (winning_trades + losing_trades) * 100 if (winning_trades + losing_trades) > 0 else 0
    
    avg_hold_days = sum(hold_days_list) / len(hold_days_list) if hold_days_list else 0
    max_hold_days = max(hold_days_list) if hold_days_list else 0
    min_hold_days = min(hold_days_list) if hold_days_list else 0
    
    display_name = stock_name or stock_code
    
    return {
        "name": display_name,
        "code": stock_code,
        "days": days,
        "years": years,
        "initial": INITIAL_CAPITAL,
        "final": capital,
        "total_return": total_return,
        "annual_return": annual_return,
        "trades": len(trades),
        "buy_signals": sum(1 for t in trades if t["type"] == "买入"),
        "stop_loss_count": stop_loss_count,
        "max_drawdown": max_drawdown,
        "win_rate": win_rate,
        "winning_trades": winning_trades,
        "losing_trades": losing_trades,
        "total_pnl": total_pnl,
        "latest_score": data[-1]["score"],
        "latest_pct": sum(1 for s in [x["score"] for x in data] if s <= data[-1]["score"]) / len(data) * 100,
        "latest_price": data[-1]["close"],
        "avg_hold_days": avg_hold_days,
        "max_hold_days": max_hold_days,
        "min_hold_days": min_hold_days,
        "trades_detail": trades,
        "equity_curve": equity_curve,
    }

def generate_html_report(results):
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>股票估值百分位策略回测报告</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0f172a; color: #e2e8f0; padding: 20px; }}
        .container {{ max-width: 1400px; margin: 0 auto; }}
        h1 {{ text-align: center; color: #38bdf8; margin-bottom: 30px; font-size: 2rem; }}
        .params {{ background: #1e293b; border-radius: 12px; padding: 20px; margin-bottom: 20px; display: flex; flex-wrap: wrap; gap: 20px; }}
        .param-item {{ display: flex; align-items: center; gap: 8px; }}
        .param-label {{ color: #94a3b8; }}
        .param-value {{ color: #fbbf24; font-weight: 600; }}
        .summary {{ margin-bottom: 30px; }}
        .summary table {{ width: 100%; border-collapse: collapse; background: #1e293b; border-radius: 12px; overflow: hidden; }}
        .summary th, .summary td {{ padding: 12px 15px; text-align: right; }}
        .summary th {{ background: #0ea5e9; color: white; font-weight: 600; text-align: left; }}
        .summary td {{ border-bottom: 1px solid #334155; }}
        .summary tr:hover td {{ background: #334155; }}
        .positive {{ color: #4ade80; }}
        .negative {{ color: #f87171; }}
        .stock-detail {{ background: #1e293b; border-radius: 12px; padding: 20px; margin-bottom: 20px; }}
        .stock-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }}
        .stock-title {{ font-size: 1.5rem; color: #38bdf8; }}
        .stock-stats {{ display: flex; gap: 20px; }}
        .stat-item {{ text-align: center; }}
        .stat-value {{ font-size: 1.2rem; font-weight: 700; }}
        .stat-label {{ font-size: 0.8rem; color: #94a3b8; }}
        .trade-table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; }}
        .trade-table th {{ background: #0ea5e9; color: white; padding: 10px; text-align: left; font-weight: 600; }}
        .trade-table td {{ padding: 10px; border-bottom: 1px solid #334155; }}
        .trade-table tr:hover td {{ background: #334155; }}
        .buy-row {{ background: #16653420; }}
        .sell-row {{ background: #991b1b20; }}
        .stop-loss-row {{ background: #7c2d1220; }}
        .stats-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; }}
        .stat-card {{ background: #0f172a; border-radius: 8px; padding: 15px; text-align: center; }}
        .chart-container {{ height: 300px; margin-bottom: 20px; }}
        .equity-line {{ fill: none; stroke: #38bdf8; stroke-width: 2; }}
        .grid-line {{ stroke: #334155; stroke-width: 1; stroke-dasharray: 5,5; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 股票估值百分位策略回测报告</h1>
        <div class="params">
            <div class="param-item"><span class="param-label">买入阈值:</span><span class="param-value">百分位 > {BUY_THRESHOLD}%</span></div>
            <div class="param-item"><span class="param-label">卖出阈值:</span><span class="param-value">百分位 < {SELL_THRESHOLD}%</span></div>
            <div class="param-item"><span class="param-label">止损线:</span><span class="param-value">亏损 > {STOP_LOSS*100:.0f}%</span></div>
            <div class="param-item"><span class="param-label">滚动窗口:</span><span class="param-value">{ROLLING_WINDOW}天</span></div>
            <div class="param-item"><span class="param-label">交易成本:</span><span class="param-value">买入{BUY_COST*100:.2f}% / 卖出{SELL_COST*100:.2f}%</span></div>
            <div class="param-item"><span class="param-label">初始资金:</span><span class="param-value">¥{INITIAL_CAPITAL:,}</span></div>
            <div class="param-item"><span class="param-label">生成日期:</span><span class="param-value">{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</span></div>
        </div>
        
        <div class="summary">
            <table>
                <thead>
                    <tr>
                        <th>股票</th>
                        <th>天数</th>
                        <th>年数</th>
                        <th>总收益</th>
                        <th>年化</th>
                        <th>回撤</th>
                        <th>交易</th>
                        <th>止损</th>
                        <th>胜率</th>
                        <th>平均持股</th>
                        <th>最长持股</th>
                        <th>最短持股</th>
                        <th>最新价</th>
                        <th>估值分</th>
                        <th>百分位</th>
                    </tr>
                </thead>
                <tbody>
"""
    for r in sorted(results, key=lambda x: x["total_return"], reverse=True):
        sign = "+" if r["total_return"] > 0 else ""
        html += f"""
                    <tr>
                        <td style="text-align:left;"><strong>{r['name']}</strong></td>
                        <td>{r['days']}</td>
                        <td>{r['years']:.1f}年</td>
                        <td class="{r['total_return'] >= 0 and 'positive' or 'negative'}">{sign}{r['total_return']:.1f}%</td>
                        <td class="{r['annual_return'] >= 0 and 'positive' or 'negative'}">{sign}{r['annual_return']:.1f}%</td>
                        <td>{r['max_drawdown']:.1f}%</td>
                        <td>{r['trades']}</td>
                        <td>{r['stop_loss_count']}</td>
                        <td>{r['win_rate']:.0f}%</td>
                        <td>{r['avg_hold_days']:.1f}天</td>
                        <td>{r['max_hold_days']}天</td>
                        <td>{r['min_hold_days']}天</td>
                        <td>{r['latest_price']}</td>
                        <td>{r['latest_score']:.1f}</td>
                        <td>{r['latest_pct']:.1f}%</td>
                    </tr>
"""
    html += """
                </tbody>
            </table>
        </div>
"""
    for r in sorted(results, key=lambda x: x["total_return"], reverse=True):
        html += f"""
        <div class="stock-detail">
            <div class="stock-header">
                <div class="stock-title">📈 {r['name']}</div>
                <div class="stock-stats">
                    <div class="stat-item"><div class="stat-value {r['total_return'] >= 0 and 'positive' or 'negative'}">{r['total_return'] >= 0 and '+' or ''}{r['total_return']:.1f}%</div><div class="stat-label">总收益</div></div>
                    <div class="stat-item"><div class="stat-value {r['annual_return'] >= 0 and 'positive' or 'negative'}">{r['annual_return'] >= 0 and '+' or ''}{r['annual_return']:.1f}%</div><div class="stat-label">年化</div></div>
                    <div class="stat-item"><div class="stat-value">{r['max_drawdown']:.1f}%</div><div class="stat-label">最大回撤</div></div>
                    <div class="stat-item"><div class="stat-value">{r['win_rate']:.0f}%</div><div class="stat-label">胜率</div></div>
                </div>
            </div>
            
            <div class="stats-grid">
                <div class="stat-card"><div class="stat-value">{r['buy_signals']}</div><div class="stat-label">买入信号</div></div>
                <div class="stat-card"><div class="stat-value" style="color:#f87171;">{r['stop_loss_count']}</div><div class="stat-label">止损次数</div></div>
                <div class="stat-card"><div class="stat-value">{r['winning_trades']}/{r['losing_trades']}</div><div class="stat-label">赢/亏交易</div></div>
                <div class="stat-card"><div class="stat-value">{r['avg_hold_days']:.1f}天</div><div class="stat-label">平均持股</div></div>
            </div>
            
            <h3 style="color: #38bdf8; margin: 20px 0 10px;">交易明细</h3>
            <table class="trade-table">
                <thead>
                    <tr>
                        <th>序号</th>
                        <th>日期</th>
                        <th>操作</th>
                        <th>价格</th>
                        <th>百分位</th>
                        <th>持仓资金</th>
                        <th>持仓天数</th>
                        <th>操作原因</th>
                    </tr>
                </thead>
                <tbody>
"""
        seq = 1
        for t in r["trades_detail"]:
            if t["type"] == "买入":
                row_class = "buy-row"
            elif t["type"] == "止损卖出":
                row_class = "stop-loss-row"
            else:
                row_class = "sell-row"
            reason = t.get("reason", "-")
            capital_str = f"¥{t['capital']:,.2f}" if t["capital"] > 0 else "-"
            hold_str = f"{t['hold_days']}天" if t["hold_days"] > 0 else "-"
            html += f"""
                    <tr class="{row_class}">
                        <td>{seq}</td>
                        <td>{t['date']}</td>
                        <td><strong>{t['type']}</strong></td>
                        <td>¥{t['price']:.2f}</td>
                        <td>{t['pct']:.1f}%</td>
                        <td>{capital_str}</td>
                        <td>{hold_str}</td>
                        <td>{reason}</td>
                    </tr>
"""
            seq += 1
        
        if len(r["trades_detail"]) % 2 == 1:
            last_trade = r["trades_detail"][-1]
            if last_trade["type"] == "买入":
                html += f"""
                    <tr>
                        <td>{seq}</td>
                        <td>{r['equity_curve'][-1]['date']}</td>
                        <td><strong>当前持仓</strong></td>
                        <td>¥{r['latest_price']}</td>
                        <td>{r['latest_pct']:.1f}%</td>
                        <td>{last_trade['shares']:.2f}</td>
                        <td>¥{r['final']:,.2f}</td>
                        <td>{r['max_hold_days']}天</td>
                    </tr>
"""
        
        html += """
                </tbody>
            </table>
        </div>
"""
    html += """
    </div>
</body>
</html>
"""
    return html

def main():
    ensure_db()
    stocks = list_valuation_stocks()
    
    if not stocks:
        print("数据库中无估值历史数据，请先运行 build_report.py 生成估值报告")
        return
    
    results = []
    for s in stocks:
        code = s['stock_code']
        name = s.get('name') or code
        print(f"回测: {name}({code})")
        result = backtest_from_db(code, name)
        if result:
            results.append(result)
    
    if not results:
        print("没有有效回测结果")
        return
    
    html = generate_html_report(results)
    output_path = "backtest_report.html"
    with open(output_path, "w") as f:
        f.write(html)
    
    print(f"\n报告已生成: {output_path}")
    print(f"共回测 {len(results)} 只股票")

if __name__ == "__main__":
    main()
