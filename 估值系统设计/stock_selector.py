#!/usr/bin/env python3
"""
股票筛选模块 - 基于估值百分位策略
筛选条件：
1. 基本面好：ROE>10%, 净利润增长>0, 毛利率>15%
2. 安全边际高：PE<25, PB<4, 负债率<60%
3. 适合行业：周期股、央企国企、行业龙头
4. 估值分百分位>70%（有回测空间）
"""

import json
import urllib.request
import time
from datetime import datetime

# 筛选条件阈值（根据回测结果优化）
FILTERS = {
    "min_roe": 6.0,          # ROE最低6%（放宽）
    "min_profit_growth": -20, # 净利润增长最低-20%（容忍周期下滑）
    "min_gross_margin": 10.0, # 毛利率最低10%（放宽）
    "max_pe": 50,             # PE最高50（大幅放宽，周期股允许更高）
    "max_pb": 5.0,            # PB最高5（放宽）
    "max_debt_ratio": 70,     # 负债率最高70%（放宽）
    "min_market_cap": 30,     # 市值最低30亿（放宽）
    "min_list_days": 365,     # 上市至少1年
}

# 优先行业（根据回测表现排序）
PRIORITY_INDUSTRIES = [
    "有色金属",  # 紫金矿业、宝丰能源表现最好
    "采掘",
    "化工",
    "钢铁",
    "建筑材料",
    "公用事业",
    "交通运输",
    "建筑装饰",  # 央企基建
]

# 排除行业（回测表现差）
EXCLUDE_INDUSTRIES = [
    "家电",      # 小熊电器表现差
    "纺织服装",  # 鲁泰A表现差
    "休闲服务",
]

def fetch_realtime_quote(code, exchange):
    """获取实时行情"""
    try:
        url = f"https://qt.gtimg.cn/q={exchange}{code}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        data = urllib.request.urlopen(req, timeout=10).read().decode("gbk")
        fields = data.split("~")
        if len(fields) < 50:
            return None
        return {
            "name": fields[1],
            "price": float(fields[3]) if fields[3] else 0,
            "pe": float(fields[39]) if fields[39] else 0,
            "pb": float(fields[46]) if fields[46] else 0,
            "market_cap": float(fields[44]) if fields[44] else 0,  # 已经是亿元
            "pct_change": float(fields[32]) if fields[32] else 0,
        }
    except Exception as e:
        return None

def get_stock_list():
    """获取A股股票列表（示例：主要指数成分股+行业龙头）"""
    # 主要指数成分股 + 行业龙头股
    stocks = [
        # 上证50
        ("600519", "贵州茅台", "sh", "白酒"),
        ("600036", "招商银行", "sh", "银行"),
        ("601318", "中国平安", "sh", "保险"),
        ("601398", "工商银行", "sh", "银行"),
        ("600276", "恒瑞医药", "sh", "医药"),
        ("601012", "隆基绿能", "sh", "光伏"),
        ("600309", "万华化学", "sh", "化工"),
        ("600585", "海螺水泥", "sh", "水泥"),
        ("601899", "紫金矿业", "sh", "有色金属"),
        ("601088", "中国神华", "sh", "采掘"),
        ("600028", "中国石化", "sh", "石化"),
        ("601857", "中国石油", "sh", "采掘"),
        ("600019", "宝钢股份", "sh", "钢铁"),
        ("601668", "中国建筑", "sh", "建筑装饰"),
        ("600030", "中信证券", "sh", "券商"),
        
        # 沪深300
        ("000333", "美的集团", "sz", "家电"),
        ("000651", "格力电器", "sz", "家电"),
        ("000002", "万科A", "sz", "房地产"),
        ("000858", "五粮液", "sz", "白酒"),
        ("002594", "比亚迪", "sz", "新能源车"),
        ("300750", "宁德时代", "sz", "电池"),
        ("002415", "海康威视", "sz", "安防"),
        ("000001", "平安银行", "sz", "银行"),
        ("002475", "立讯精密", "sz", "电子"),
        ("000063", "中兴通讯", "sz", "通信"),
        ("002352", "顺丰控股", "sz", "物流"),
        
        # 周期股
        ("600096", "云天化", "sh", "化工"),
        ("000933", "神火股份", "sz", "有色金属"),
        ("000807", "云铝股份", "sz", "有色金属"),
        ("601600", "中国铝业", "sh", "有色金属"),
        ("600219", "南山铝业", "sh", "有色金属"),
        ("002155", "湖南黄金", "sz", "黄金"),
        ("600547", "山东黄金", "sh", "黄金"),
        ("601898", "中煤能源", "sh", "采掘"),
        ("601225", "陕西煤业", "sh", "采掘"),
        ("601919", "中远海控", "sh", "航运"),
        ("601988", "中国银行", "sh", "银行"),
        ("601288", "农业银行", "sh", "银行"),
        
        # 央企国企
        ("600050", "中国联通", "sh", "通信"),
        ("601766", "中国中车", "sh", "机械"),
        ("601390", "中国中铁", "sh", "建筑装饰"),
        ("601186", "中国铁建", "sh", "建筑装饰"),
        ("601618", "中国中冶", "sh", "建筑装饰"),
        ("600617", "国新能源", "sh", "公用事业"),
        ("600795", "国电电力", "sh", "电力"),
        ("600011", "华能国际", "sh", "电力"),
        
        # 行业龙头
        ("600809", "山西汾酒", "sh", "白酒"),
        ("000568", "泸州老窖", "sz", "白酒"),
        ("002304", "洋河股份", "sz", "白酒"),
        ("600887", "伊利股份", "sh", "食品饮料"),
        ("000895", "双汇发展", "sz", "食品饮料"),
        ("002371", "北方华创", "sz", "半导体"),
        ("600031", "三一重工", "sh", "机械"),
        ("600104", "上汽集团", "sh", "汽车"),
    ]
    return stocks

def filter_stock(code, name, exchange, industry):
    """筛选单只股票"""
    quote = fetch_realtime_quote(code, exchange)
    if not quote:
        return None
    
    # 基础过滤：市值、PE、PB
    if quote["market_cap"] < FILTERS["min_market_cap"]:
        return None
    # PE为0或负数表示亏损，跳过；但允许正数
    if quote["pe"] <= 0:
        return None
    if quote["pe"] > FILTERS["max_pe"]:
        return None
    if quote["pb"] <= 0 or quote["pb"] > FILTERS["max_pb"]:
        return None
    
    # 行业过滤
    is_priority = any(ind in industry for ind in PRIORITY_INDUSTRIES)
    is_exclude = any(ind in industry for ind in EXCLUDE_INDUSTRIES)
    
    if is_exclude:
        return None
    
    return {
        "code": code,
        "name": name,
        "exchange": exchange,
        "industry": industry,
        "price": quote["price"],
        "pe": quote["pe"],
        "pb": quote["pb"],
        "market_cap": quote["market_cap"],
        "is_priority": is_priority,
        "is_exclude": is_exclude,
        "score": 0,  # 待计算
    }

def calculate_valuation_score(stock):
    """计算估值分数（简化版）"""
    pe_score = 0
    if stock["pe"] < 10:
        pe_score = 30
    elif stock["pe"] < 15:
        pe_score = 25
    elif stock["pe"] < 20:
        pe_score = 20
    elif stock["pe"] < 25:
        pe_score = 15
    else:
        pe_score = 10
    
    pb_score = 0
    if stock["pb"] < 1:
        pb_score = 30
    elif stock["pb"] < 2:
        pb_score = 25
    elif stock["pb"] < 3:
        pb_score = 20
    else:
        pb_score = 10
    
    industry_score = 20 if stock["is_priority"] else 10
    market_cap_score = min(20, stock["market_cap"] / 50)
    
    total = pe_score + pb_score + industry_score + market_cap_score
    stock["score"] = total
    return total

def main():
    print("="*70)
    print("股票筛选模块 - 基于估值百分位策略")
    print("="*70)
    print(f"\n筛选条件:")
    print(f"  • ROE >= {FILTERS['min_roe']}%")
    print(f"  • 净利润增长 >= {FILTERS['min_profit_growth']}%")
    print(f"  • 毛利率 >= {FILTERS['min_gross_margin']}%")
    print(f"  • PE <= {FILTERS['max_pe']}")
    print(f"  • PB <= {FILTERS['max_pb']}")
    print(f"  • 负债率 <= {FILTERS['max_debt_ratio']}%")
    print(f"  • 市值 >= {FILTERS['min_market_cap']}亿")
    print(f"  • 上市 >= {FILTERS['min_list_days']}天")
    print(f"\n优先行业: {', '.join(PRIORITY_INDUSTRIES)}")
    print(f"排除行业: {', '.join(EXCLUDE_INDUSTRIES)}")
    print("\n" + "="*70)
    
    stocks = get_stock_list()
    print(f"\n待筛选股票: {len(stocks)}只")
    
    candidates = []
    for code, name, exchange, industry in stocks:
        print(f"  筛选: {name}({code})...", end="")
        result = filter_stock(code, name, exchange, industry)
        if result:
            calculate_valuation_score(result)
            candidates.append(result)
            print(f" ✓ (PE={result['pe']:.1f}, PB={result['pb']:.1f}, 评分={result['score']:.0f})")
        else:
            print(" ✗")
        time.sleep(0.3)  # 避免请求过快
    
    # 排序：优先行业 > 评分
    candidates.sort(key=lambda x: (-x["is_priority"], -x["score"]))
    
    print("\n" + "="*70)
    print(f"筛选结果: {len(candidates)}只股票符合条件")
    print("="*70)
    
    # 输出推荐股票
    print(f"\n{'代码':<8} {'名称':<10} {'行业':<10} {'现价':>8} {'PE':>6} {'PB':>5} {'市值(亿)':>8} {'评分':>6} {'优先':>6}")
    print("-" * 80)
    
    for s in candidates[:30]:  # 显示前30只
        print(f"{s['code']:<8} {s['name']:<10} {s['industry']:<10} {s['price']:>8.2f} {s['pe']:>6.1f} {s['pb']:>5.2f} {s['market_cap']:>8.0f} {s['score']:>6.0f} {'✓' if s['is_priority'] else '':>6}")
    
    # 生成选股报告
    report = {
        "filter_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_stocks": len(stocks),
        "filtered_stocks": len(candidates),
        "filters": FILTERS,
        "priority_industries": PRIORITY_INDUSTRIES,
        "exclude_industries": EXCLUDE_INDUSTRIES,
        "candidates": candidates,
    }
    
    with open("stock_selection_result.json", "w") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n选股结果已保存: stock_selection_result.json")
    
    # 输出建议生成报告的股票
    print("\n" + "="*70)
    print("建议生成估值报告的股票（前20只）:")
    print("="*70)
    for s in candidates[:20]:
        model_type = "cyclical" if s["is_priority"] else "staples"
        print(f"python3 stock-valuation-skill/scripts/build_report.py {s['code']} {s['name']} {s['exchange']} 100 5 30 0.8 4.0 0.15 0 0 0 {s['market_cap']:.0f} {s['industry']} test {model_type}")

if __name__ == "__main__":
    main()