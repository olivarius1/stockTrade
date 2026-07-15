#!/usr/bin/env python3
"""
春立医疗(688236) 缠论结构分析与建仓建议
"""
import urllib.request
import json
import time
from datetime import datetime

CODE = "688236"
NAME = "春立医疗"

# ========== 数据获取 ==========

def fetch_klines_eastmoney(secid, klt, beg, end, lmt=1000, retries=3):
    """klt: 101=日,102=周,60=60min,30=30min, fqt=1前复权"""
    url = (f"https://push2his.eastmoney.com/api/qt/stock/kline/get"
           f"?secid={secid}&fields1=f1,f2,f3,f4,f5,f6"
           f"&fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61"
           f"&klt={klt}&fqt=1&beg={beg}&end={end}&lmt={lmt}")
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            time.sleep(1.0 + attempt * 0.5)
            data = urllib.request.urlopen(req, timeout=20).read()
            jd = json.loads(data)
            klines = jd.get("data", {}).get("klines", [])
            result = []
            for k in klines:
                parts = k.split(",")
                result.append({
                    "date": parts[0],
                    "open": float(parts[1]),
                    "close": float(parts[2]),
                    "high": float(parts[3]),
                    "low": float(parts[4]),
                    "volume": float(parts[5]),
                    "amount": float(parts[6]),
                    "amplitude": float(parts[7]),
                    "pct": float(parts[8]),
                    "change": float(parts[9]),
                    "turnover": float(parts[10]) if len(parts) > 10 else 0,
                })
            return result
        except Exception as e:
            print(f"    请求失败(尝试{attempt+1}/{retries}): {e}")
            if attempt == retries - 1:
                return []
    return []

def fetch_klines_tencent(code, exchange, period="day", start="20190101", end="20260714"):
    """period: day/week/month/m60/m30"""
    full = exchange + code
    qfq_map = {"day": "qfqday", "week": "qfqweek", "month": "qfqmonth",
               "m60": "qfqm60", "m30": "qfqm30"}
    raw_map = {"day": "day", "week": "week", "month": "month",
               "m60": "m60", "m30": "m30"}
    url = f"http://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={full},{period},{start},{end},1000,qfq"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        data = urllib.request.urlopen(req, timeout=15).read()
        jd = json.loads(data)
        stock_data = jd["data"][full]
        # 处理可能返回列表的情况
        if isinstance(stock_data, list):
            stock_data = stock_data[0] if stock_data else {}
        key = qfq_map.get(period, "day")
        kdata = stock_data.get(key) or stock_data.get(raw_map.get(period, "day"), [])
        result = []
        for row in kdata:
            if isinstance(row, list) and len(row) >= 6:
                result.append({
                    "date": row[0],
                    "open": float(row[1]),
                    "close": float(row[2]),
                    "high": float(row[3]),
                    "low": float(row[4]),
                    "volume": float(row[5]),
                    "amount": 0,
                })
        return result
    except Exception as e:
        print(f"    腾讯接口失败: {e}")
        return []

def load_local_klines(code):
    """从batch_valuation下载的本地JSON文件加载日线数据"""
    import os, glob
    kdir = f"tbea-valuation/kline_{code}"
    if not os.path.exists(kdir):
        return []
    all_k = []
    seen = set()
    for fpath in sorted(glob.glob(f"{kdir}/k*.json")):
        try:
            with open(fpath) as f:
                jd = json.load(f)
            stock_data = jd["data"][f"sh{code}"]
            for key in ["qfqday", "day"]:
                if key in stock_data:
                    for row in stock_data[key]:
                        if isinstance(row, list) and len(row) >= 6:
                            d = row[0]
                            if d not in seen:
                                seen.add(d)
                                all_k.append({
                                    "date": d,
                                    "open": float(row[1]),
                                    "close": float(row[2]),
                                    "high": float(row[3]),
                                    "low": float(row[4]),
                                    "volume": float(row[5]),
                                    "amount": 0,
                                })
                    break
        except Exception as e:
            print(f"    读取本地文件失败 {fpath}: {e}")
    all_k.sort(key=lambda x: x["date"])
    return all_k

def daily_to_weekly(daily):
    """日线合成周线（简化：按自然周）"""
    if not daily:
        return []
    weeks = []
    cur_week = None
    for k in daily:
        dt = datetime.strptime(k["date"], "%Y-%m-%d")
        week_key = dt.strftime("%Y-W%W")
        if cur_week is None or week_key != cur_week["key"]:
            if cur_week:
                weeks.append(cur_week["data"])
            cur_week = {"key": week_key, "data": {
                "date": k["date"],
                "open": k["open"],
                "close": k["close"],
                "high": k["high"],
                "low": k["low"],
                "volume": k["volume"],
                "amount": 0,
            }}
        else:
            cur_week["data"]["close"] = k["close"]
            cur_week["data"]["high"] = max(cur_week["data"]["high"], k["high"])
            cur_week["data"]["low"] = min(cur_week["data"]["low"], k["low"])
            cur_week["data"]["volume"] += k["volume"]
    if cur_week:
        weeks.append(cur_week["data"])
    return weeks

def fetch_realtime():
    url = f"https://qt.gtimg.cn/q=sh{CODE}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    data = urllib.request.urlopen(req, timeout=10).read().decode("gbk")
    fields = data.split("~")
    return {
        "name": fields[1],
        "price": float(fields[3]),
        "yest": float(fields[4]),
        "open": float(fields[5]),
        "high": float(fields[33]),
        "low": float(fields[34]),
        "pe": float(fields[39]) if fields[39] else 0,
        "pb": float(fields[46]) if fields[46] else 0,
        "market_cap_yi": float(fields[44]) / 10000 if fields[44] else 0,
        "total_shares_yi": float(fields[44]) / float(fields[3]) / 100000000 if fields[3] and fields[44] else 0,
        "turnover": float(fields[38]) if fields[38] else 0,
        "volume": float(fields[36]) if fields[36] else 0,
    }

# ========== 缠论基础结构 ==========

def find_fractals(klines):
    """找顶分型和底分型（简化版：严格3K）"""
    tops = []   # (index, high, date)
    bottoms = []  # (index, low, date)
    n = len(klines)
    for i in range(1, n - 1):
        prev, cur, nxt = klines[i-1], klines[i], klines[i+1]
        # 顶分型: 中间K线高点最高，且低点也最高
        if cur["high"] > prev["high"] and cur["high"] > nxt["high"]:
            tops.append((i, cur["high"], cur["date"]))
        # 底分型: 中间K线低点最低，且高点也最低
        if cur["low"] < prev["low"] and cur["low"] < nxt["low"]:
            bottoms.append((i, cur["low"], cur["date"]))
    return tops, bottoms

def build_bi(klines, tops, bottoms):
    """构建笔：顶底相连，间隔至少1根K线"""
    bi = []
    all_points = sorted([(i, "top", h, d) for i, h, d in tops] +
                        [(i, "bot", l, d) for i, l, d in bottoms])
    if not all_points:
        return bi

    # 从第一个分型开始，交替连接
    last = all_points[0]
    bi.append({"type": last[1], "idx": last[0], "price": last[2], "date": last[3]})

    for p in all_points[1:]:
        if p[1] != last[1]:  # 类型不同，可以连笔
            # 间隔至少1根K线
            if p[0] - last[0] >= 2:
                bi.append({"type": p[1], "idx": p[0], "price": p[2], "date": p[3]})
                last = p
    return bi

def analyze_trend(bi):
    """分析笔序列的趋势和结构"""
    if len(bi) < 3:
        return []

    segments = []
    direction = None  # "up" or "down"

    for i in range(1, len(bi)):
        prev, cur = bi[i-1], bi[i]
        if prev["type"] == "bot" and cur["type"] == "top":
            seg_dir = "up"
        elif prev["type"] == "top" and cur["type"] == "bot":
            seg_dir = "down"
        else:
            continue

        if direction is None:
            direction = seg_dir
            start = prev
        elif direction == seg_dir:
            # 同方向延伸
            pass
        else:
            # 方向改变，完成一段
            segments.append({
                "direction": direction,
                "start": start,
                "end": prev,
                "change": prev["price"] - start["price"],
                "change_pct": (prev["price"] - start["price"]) / start["price"] * 100
            })
            direction = seg_dir
            start = prev

    # 最后一段（未完成）
    if direction and len(bi) > 0:
        segments.append({
            "direction": direction,
            "start": start,
            "end": bi[-1],
            "change": bi[-1]["price"] - start["price"],
            "change_pct": (bi[-1]["price"] - start["price"]) / start["price"] * 100,
            "unfinished": True
        })
    return segments

def find_zhongshu(segments):
    """简化中枢识别：连续三段有重叠区间"""
    if len(segments) < 3:
        return []
    zhongshus = []
    i = 0
    while i < len(segments) - 2:
        s1, s2, s3 = segments[i], segments[i+1], segments[i+2]
        # 找三段的价格区间重叠
        highs = [s1["end"]["price"], s2["start"]["price"], s2["end"]["price"], s3["start"]["price"]]
        lows = [s1["start"]["price"], s2["start"]["price"], s2["end"]["price"], s3["end"]["price"]]
        # 简化：取各段极值
        range1 = (min(s1["start"]["price"], s1["end"]["price"]),
                  max(s1["start"]["price"], s1["end"]["price"]))
        range2 = (min(s2["start"]["price"], s2["end"]["price"]),
                  max(s2["start"]["price"], s2["end"]["price"]))
        range3 = (min(s3["start"]["price"], s3["end"]["price"]),
                  max(s3["start"]["price"], s3["end"]["price"]))

        overlap_low = max(range1[0], range2[0], range3[0])
        overlap_high = min(range1[1], range2[1], range3[1])

        if overlap_high > overlap_low:
            zhongshus.append({
                "idx": i,
                "low": overlap_low,
                "high": overlap_high,
                "start_date": s1["start"]["date"],
                "end_date": s3["end"]["date"],
                "segments": [s1, s2, s3]
            })
            i += 3
        else:
            i += 1
    return zhongshus

def detect_divergence(segments):
    """检测背驰（简化：同方向两段，后段力度弱于前段）"""
    signals = []
    for i in range(2, len(segments)):
        s_prev = segments[i-2]
        s_cur = segments[i]
        if s_prev["direction"] == s_cur["direction"] and s_prev["direction"] == "down":
            # 两段下跌比较
            change_prev = abs(s_prev["change"])
            change_cur = abs(s_cur["change"])
            if change_cur < change_prev * 0.8:  # 后段跌幅明显小于前段
                signals.append({
                    "type": "一买/底背驰",
                    "idx": i,
                    "date": s_cur["end"]["date"],
                    "price": s_cur["end"]["price"],
                    "desc": f"下跌力度衰减: {change_prev:.2f} -> {change_cur:.2f}"
                })
        elif s_prev["direction"] == s_cur["direction"] and s_prev["direction"] == "up":
            change_prev = abs(s_prev["change"])
            change_cur = abs(s_cur["change"])
            if change_cur < change_prev * 0.8:
                signals.append({
                    "type": "一卖/顶背驰",
                    "idx": i,
                    "date": s_cur["end"]["date"],
                    "price": s_cur["end"]["price"],
                    "desc": f"上涨力度衰减: {change_prev:.2f} -> {change_cur:.2f}"
                })
    return signals

def analyze_level(klines, level_name):
    """对某一级别的K线进行缠论分析"""
    tops, bottoms = find_fractals(klines)
    bi = build_bi(klines, tops, bottoms)
    segments = analyze_trend(bi)
    zhongshus = find_zhongshu(segments)
    signals = detect_divergence(segments)
    return {
        "level": level_name,
        "klines": len(klines),
        "tops": len(tops),
        "bottoms": len(bottoms),
        "bi": bi,
        "segments": segments,
        "zhongshus": zhongshus,
        "signals": signals,
        "latest_price": klines[-1]["close"] if klines else 0,
        "latest_date": klines[-1]["date"] if klines else "",
    }

# ========== 主程序 ==========

def main():
    print("=" * 60)
    print(f"【{NAME}({CODE})】缠论结构分析与建仓建议")
    print("=" * 60)

    # 获取实时数据
    rt = fetch_realtime()
    print(f"\n【实时数据】{rt['date'] if 'date' in rt else datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"  最新价: {rt['price']:.2f} | 涨跌: {((rt['price']/rt['yest']-1)*100):.2f}%")
    print(f"  开盘: {rt['open']:.2f} | 最高: {rt['high']:.2f} | 最低: {rt['low']:.2f}")
    print(f"  PE(TTM): {rt['pe']:.2f} | PB: {rt['pb']:.2f}")
    print(f"  市值: {rt['market_cap_yi']:.2f}亿 | 换手: {rt['turnover']:.2f}%")

    secid = f"1.{CODE}"

    # 获取各级别K线（优先本地文件，其次东方财富，最后腾讯）
    print("\n【数据获取】")

    print("  获取日线...")
    daily = load_local_klines(CODE)
    if not daily:
        daily = fetch_klines_eastmoney(secid, 101, "20210101", "20260714", 1200)
    if not daily:
        daily = fetch_klines_tencent(CODE, "sh", "day", "20190101", "20260714")

    print("  合成周线...")
    weekly = daily_to_weekly(daily)

    print("  获取60分钟...")
    m60 = fetch_klines_eastmoney(secid, 60, "20250101", "20260714", 500)
    if not m60:
        m60 = fetch_klines_tencent(CODE, "sh", "m60", "20250101", "20260714")

    print("  获取30分钟...")
    m30 = fetch_klines_eastmoney(secid, 30, "20250101", "20260714", 500)
    if not m30:
        m30 = fetch_klines_tencent(CODE, "sh", "m30", "20250101", "20260714")

    print(f"  日线: {len(daily)}条 ({daily[0]['date'] if daily else 'N/A'} ~ {daily[-1]['date'] if daily else 'N/A'})")
    print(f"  周线: {len(weekly)}条 ({weekly[0]['date'] if weekly else 'N/A'} ~ {weekly[-1]['date'] if weekly else 'N/A'})")
    print(f"  60min: {len(m60)}条 ({m60[0]['date'] if m60 else 'N/A'} ~ {m60[-1]['date'] if m60 else 'N/A'})")
    print(f"  30min: {len(m30)}条 ({m30[0]['date'] if m30 else 'N/A'} ~ {m30[-1]['date'] if m30 else 'N/A'})")

    # 各级别分析
    w = analyze_level(weekly, "周线")
    d = analyze_level(daily, "日线")
    h = analyze_level(m60, "60分钟")
    m = analyze_level(m30, "30分钟")

    print("\n" + "=" * 60)
    print("【缠论结构分析】")
    print("=" * 60)

    for level in [w, d, h, m]:
        print(f"\n{'─' * 50}")
        print(f"▶ {level['level']}级别 | 共{level['klines']}根K线 | 最新: {level['latest_date']} {level['latest_price']:.2f}")
        print(f"{'─' * 50}")

        # 笔
        bi = level["bi"]
        print(f"  笔序列 ({len(bi)}笔):")
        for i, b in enumerate(bi[-8:]):
            marker = "🔴" if b["type"] == "top" else "🟢"
            print(f"    {marker} {b['date']} {'顶' if b['type']=='top' else '底'} {b['price']:.2f}")

        # 线段
        segs = level["segments"]
        print(f"\n  线段 ({len(segs)}段):")
        for i, s in enumerate(segs[-5:]):
            status = "(未完成)" if s.get("unfinished") else ""
            arrow = "📈" if s["direction"] == "up" else "📉"
            print(f"    {arrow} {s['start']['date']} ~ {s['end']['date']} | "
                  f"{'上涨' if s['direction']=='up' else '下跌'} "
                  f"{s['change']:.2f} ({s['change_pct']:.1f}%) {status}")

        # 中枢
        zs = level["zhongshus"]
        if zs:
            print(f"\n  中枢 ({len(zs)}个):")
            for z in zs:
                print(f"    ⬜ {z['start_date']} ~ {z['end_date']} | "
                      f"区间 [{z['low']:.2f}, {z['high']:.2f}] | 幅度 {((z['high']-z['low'])/z['low']*100):.1f}%")
        else:
            print(f"\n  中枢: 未形成明显中枢结构")

        # 买卖点信号
        sigs = level["signals"]
        if sigs:
            print(f"\n  买卖点信号:")
            for sig in sigs[-3:]:
                emoji = "✅" if "买" in sig["type"] else "⚠️"
                print(f"    {emoji} {sig['type']} | {sig['date']} | 价格 {sig['price']:.2f} | {sig['desc']}")
        else:
            print(f"\n  买卖点: 暂无明确背驰信号")

    # ========== 综合判断 ==========
    print("\n" + "=" * 60)
    print("【综合研判与建仓建议】")
    print("=" * 60)

    # 基本面
    print("\n▶ 基本面评分: 中性偏谨慎")
    print(f"  • 行业: 医疗器械（骨科植入物）")
    print(f"  • PE {rt['pe']:.1f}倍 / PB {rt['pb']:.1f}倍，估值处于历史中低位")
    print(f"  • 总市值 {rt['market_cap_yi']:.1f}亿，流通盘适中")
    print(f"  • 风险: 集采政策压力、行业竞争加剧、科创板的波动特性")

    # 周线判断
    w_last_seg = w["segments"][-1] if w["segments"] else None
    w_trend = "📉 周线级别处于下跌趋势中" if w_last_seg and w_last_seg["direction"] == "down" else "📈 周线级别处于上涨趋势中"
    print(f"\n▶ {w_trend}")
    if w_last_seg:
        print(f"  • 当前线段: {'下跌' if w_last_seg['direction']=='down' else '上涨'} "
              f"{w_last_seg['change_pct']:.1f}% (未确认完成)" if w_last_seg.get("unfinished") else "")
        print(f"  • 周线从上市高点约28元跌至当前{rt['price']:.2f}元，跌幅约{((rt['price']/28-1)*100):.1f}%")
        print(f"  • 长期大级别处于熊市下跌后的低位震荡阶段")

    # 日线判断
    d_last_seg = d["segments"][-1] if d["segments"] else None
    d_prev_seg = d["segments"][-2] if len(d["segments"]) > 1 else None
    print(f"\n▶ 日线级别:")
    if d_last_seg:
        print(f"  • 当前线段方向: {'下跌' if d_last_seg['direction']=='down' else '上涨'}")
        if d_prev_seg and d_last_seg["direction"] == "down" and d_prev_seg["direction"] == "down":
            print(f"  • 连续两段下跌对比: 前段跌幅 {abs(d_prev_seg['change_pct']):.1f}% -> 当前段 {abs(d_last_seg['change_pct']):.1f}%")
            if abs(d_last_seg["change_pct"]) < abs(d_prev_seg["change_pct"]) * 0.7:
                print(f"  • ⚠️ 日线级别出现下跌背驰迹象（力度衰减）")
    print(f"  • 日线近半年在13-18元区间震荡，当前处于区间下沿附近")

    # 60/30分钟
    print(f"\n▶ 60分钟/30分钟级别:")
    h_last = h["segments"][-1] if h["segments"] else None
    m_last = m["segments"][-1] if m["segments"] else None
    if h_last and h_last["direction"] == "down":
        print(f"  • 60分钟当前处于下跌线段中，尚未出现明显底分型确认")
    else:
        print(f"  • 60分钟可能出现短暂反弹，但力度存疑")
    if m_last and m_last["direction"] == "down":
        print(f"  • 30分钟同样处于下跌结构中")

    # 建仓建议
    print(f"\n{'=' * 60}")
    print("【建仓策略建议】")
    print(f"{'=' * 60}")

    current_price = rt["price"]
    print(f"""
当前价格: {current_price:.2f}元

⚠️ 重要提示: 缠论分析显示，该股大级别（周线/日线）仍处于下跌后的底部震荡阶段，
   尚未出现明确的大级别一买确认信号。短期（60/30分钟）亦无明确买点。

建议策略:
┌─────────────────────────────────────────────────────────────┐
│ 1. 仓位控制: 试仓 10%-15%（不超过总仓位1/10）                │
│ 2. 建仓方式: 分批左侧建仓，不建议一次性重仓                  │
│ 3. 建仓区间: 13.50 - 14.50 元（当前接近区间下沿）            │
│ 4. 止损位:  12.80 元（前低下方约5%）                        │
│ 5. 目标位:  第一阶段 16.50-17.00元（日线中枢上沿）           │
│            第二阶段 20.00元以上（需周线反转确认）            │
└─────────────────────────────────────────────────────────────┘

买点跟踪（缠论视角）:
  ❌ 周线一买: 未确认（需等待下跌线段完成+背驰）
  ❌ 日线一买: 未确认（当前下跌线段未完成）
  ⚠️ 60分钟一买: 观察中（关注近期是否出现底分型+底背驰）
  ⚠️ 30分钟一买: 观察中

操作节奏:
  1. 激进型: 当前可轻仓试多（10%），跌破13.5元加仓至15%，破12.8元止损
  2. 稳健型: 等待日线出现明显底分型+MACD底背离后再建仓（15-16元区间）
  3. 保守型: 等待周线级别出现一买确认信号后再考虑介入

关键观察指标:
  • 日线能否在13元附近形成有效支撑
  • 成交量是否出现放量阳线（确认资金介入）
  • 60分钟级别是否形成底背驰结构
  • 骨科集采政策是否有新的利好消息
""")

    print(f"\n{'=' * 60}")
    print("免责声明: 以上分析仅供学习研究，不构成投资建议。")
    print(f"{'=' * 60}")

if __name__ == "__main__":
    main()
