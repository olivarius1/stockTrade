#!/usr/bin/env python3
"""
批量估值报告生成器
"""
import subprocess, os, json, urllib.request, sys

# 股票列表: (代码, 名称, 交易所, 模型, 总股本亿, pe_min, pe_max, pb_min, pb_max, eps_growth, 行业描述)
STOCKS = [
    ("301087", "可孚医疗", "sz", "pharma",   5.65,  15, 50, 1.5, 6.0, 0.20, "医疗器械"),
    ("002461", "珠江啤酒", "sz", "staples",  8.79,  15, 40, 1.5, 5.0, 0.12, "啤酒饮料"),
    ("002768", "国恩股份", "sz", "cyclical", 57.45,  8, 30, 1.0, 4.0, 0.24, "高分子材料"),
    ("688236", "春立医疗", "sh", "pharma",   17.40, 15, 50, 1.5, 6.0, 0.30, "医疗器械"),
    ("300030", "阳普医疗", "sz", "pharma",   7.27,  15, 50, 1.5, 6.0, 0.25, "医疗器械"),
    ("601022", "宁波远洋", "sh", "soe",      8.48,  6, 20, 0.8, 3.0, 0.18, "航运物流"),
    ("688016", "心脉医疗", "sh", "pharma",   1.07,  15, 50, 1.5, 6.0, 0.15, "医疗器械"),
    ("301507", "民生健康", "sz", "pharma",   1.45,  15, 50, 1.5, 6.0, 0.29, "保健品"),
    ("601808", "中海油服", "sh", "soe",      12.52, 6, 20, 0.8, 3.0, 0.22, "石油服务"),
]

OUTPUT_DIR = "tbea-valuation"
SCRIPT = "../app/data/report_generator.py"

def download_klines(code, exchange):
    """下载10年K线数据，分5批"""
    kdir = f"{OUTPUT_DIR}/kline_{code}"
    os.makedirs(kdir, exist_ok=True)
    
    batches = [
        ("2016-07-14", "2018-07-14", "k1"),
        ("2018-07-14", "2020-07-14", "k2"),
        ("2020-07-14", "2022-07-14", "k3"),
        ("2022-07-14", "2024-07-14", "k4"),
        ("2024-07-14", "2027-07-14", "k5"),
    ]
    
    files = []
    for start, end, suffix in batches:
        url = f"http://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={exchange}{code},day,{start},{end},500,qfq"
        out = f"{kdir}/{suffix}.json"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            data = urllib.request.urlopen(req, timeout=15).read()
            with open(out, "wb") as f:
                f.write(data)
            files.append(out)
        except Exception as e:
            print(f"  [{code}] K线下载失败 {suffix}: {e}")
            return None
    
    return files

def get_stock_data(code, exchange):
    """获取实时数据"""
    try:
        req = urllib.request.Request(
            f'https://qt.gtimg.cn/q={exchange}{code}',
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        data = urllib.request.urlopen(req, timeout=10).read().decode('gbk')
        fields = data.split('~')
        return {
            'price': float(fields[3]) if len(fields) > 3 and fields[3] else 0,
            'pe': float(fields[39]) if len(fields) > 39 and fields[39] else 0,
            'pb': float(fields[46]) if len(fields) > 46 and fields[46] else 0,
            'market_cap': float(fields[45]) if len(fields) > 45 and fields[45] else 0,  # 万
        }
    except Exception as e:
        print(f"  [{code}] 实时数据获取失败: {e}")
        return None

def generate_report(stock_info, kline_files):
    """生成估值报告"""
    code, name, exchange, model, total_shares, pe_min, pe_max, pb_min, pb_max, eps_growth, industry = stock_info
    
    # 获取实时数据
    realtime = get_stock_data(code, exchange)
    if not realtime:
        return False
    
    market_cap_yi = realtime['market_cap'] / 10000  # 亿
    
    # 估算营收和净利润（简化：用市值/PE得到净利润，再估算营收）
    # 净利润 = 市值 / PE
    net_profit = market_cap_yi / realtime['pe'] if realtime['pe'] > 0 else 0
    # 营收 ≈ 净利润 / 净利率（假设10%）
    revenue = net_profit / 0.10
    
    # 毛利率假设
    gross_margin = "15.00%"
    
    cmd = [
        "python3", SCRIPT,
        code,
        name,
        exchange,
        str(total_shares),
        str(pe_min), str(pe_max),
        str(pb_min), str(pb_max),
        str(eps_growth),
        f"{revenue:.2f}",
        f"{net_profit:.2f}",
        gross_margin,
        f"{market_cap_yi:.0f}",
        industry,
        f"{name}{model}估值框架与十年回测",
        model,
    ] + kline_files
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        print(f"  [{code}] {result.stdout.strip()}")
        if result.returncode != 0:
            print(f"  [{code}] STDERR: {result.stderr[:200]}")
            return False
        return True
    except Exception as e:
        print(f"  [{code}] 生成报告失败: {e}")
        return False

def main():
    os.chdir("/Users/zhanghe/MyProjs/trade/eval_sys/stockTrade/估值系统设计")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    success = 0
    for stock in STOCKS:
        code, name, exchange, model, *_ = stock
        print(f"\n[{code}] {name} - 开始处理...")
        
        # 下载K线
        klines = download_klines(code, exchange)
        if not klines:
            print(f"  [{code}] K线下载失败，跳过")
            continue
        
        # 生成报告
        if generate_report(stock, klines):
            success += 1
    
    print(f"\n完成: {success}/{len(STOCKS)} 只股票生成报告成功")

if __name__ == "__main__":
    main()
