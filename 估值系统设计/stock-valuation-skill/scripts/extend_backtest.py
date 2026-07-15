#!/usr/bin/env python3
"""
扩展回测周期到10年
从现有HTML报告中提取数据，获取更早的K线数据，合并后重新计算估值分
"""
import json, re, os, sys, math, glob, urllib.request, time
from datetime import datetime, timedelta

HTML_DIR = '/Users/zhanghe/MyProjs/trade/eval_sys/估值系统设计/tbea-valuation'
TEN_YEARS_AGO = (datetime.now() - timedelta(days=365 * 10)).strftime('%Y-%m-%d')

def fetch_kline(code, exchange, start_date, end_date):
    """从腾讯接口获取K线数据"""
    full_code = exchange + code
    url = f"http://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={full_code},day,{start_date},{end_date},500,qfq"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode('utf-8'))
        kline = data['data'][full_code]['qfqday']
        qt = data['data'][full_code]['qt'][full_code]
        return kline, qt
    except Exception as e:
        print(f"  获取K线失败: {e}")
        return None, None

def extract_from_html(html_path):
    """从HTML中提取VALUATION_DATA"""
    with open(html_path, 'r', encoding='utf-8') as f:
        content = f.read()
    match = re.search(r'var VALUATION_DATA = (\{.*?\});', content, re.DOTALL)
    if not match:
        return None
    return json.loads(match.group(1))

def reverse_params(records):
    """从已有数据反推评分参数"""
    # 找两个差异最大的点来反推PE_MIN, PE_MAX
    pe_data = [(r['pe_ttm'], r['s_pe']) for r in records if r['pe_ttm'] > 0 and r.get('s_pe', 0) > 0]
    pb_data = [(r['pb'], r['s_pb']) for r in records if r['pb'] > 0 and r.get('s_pb', 0) > 0]

    def reverse_range(data_points, score_key):
        if len(data_points) < 2:
            return 0, 100
        # 找score差异最大的两个点
        data_points.sort(key=lambda x: x[1])
        p1, p2 = data_points[0], data_points[-1]
        pe1, s1 = p1
        pe2, s2 = p2
        k1 = (100 - s1) / 100
        k2 = (100 - s2) / 100
        if abs(k1 - k2) < 0.001:
            return 0, 100
        rng = (pe1 - pe2) / (k1 - k2)
        lo = pe1 - k1 * rng
        hi = lo + rng
        return lo, hi

    pe_min, pe_max = reverse_range(pe_data, 's_pe')
    pb_min, pb_max = reverse_range(pb_data, 's_pb')

    # 反推EPS_GROWTH（从PEG得分）
    # peg = pe / (growth * 100)
    # s_peg=80 when peg<1.0, s_peg=65 when 1.0<=peg<1.2
    eps_growth = 0.15  # 默认值
    peg_records = [r for r in records if r.get('s_peg', 0) > 0 and r['pe_ttm'] > 0]
    if peg_records:
        # 尝试从s_peg=80的记录反推（peg=1.0边界）
        r80 = [r for r in peg_records if 78 <= r['s_peg'] <= 82]
        if r80:
            # peg ≈ 1.0, growth = pe / 100
            eps_growth = r80[-1]['pe_ttm'] / 100
        else:
            r65 = [r for r in peg_records if 63 <= r['s_peg'] <= 67]
            if r65:
                # peg ≈ 1.1 (边界中点)
                eps_growth = r65[-1]['pe_ttm'] / 110
            else:
                r35 = [r for r in peg_records if 33 <= r['s_peg'] <= 37]
                if r35:
                    eps_growth = r35[-1]['pe_ttm'] / 175  # peg≈1.75
    eps_growth = max(0.01, min(1.0, eps_growth))

    return pe_min, pe_max, pb_min, pb_max, eps_growth

def score_pe(pe, pe_min, pe_max):
    if pe <= 0: return 50
    p = (pe - pe_min) / (pe_max - pe_min)
    p = max(0, min(1, p))
    return (1 - p) * 100

def score_pb(pb, pb_min, pb_max):
    if pb <= 0: return 50
    p = (pb - pb_min) / (pb_max - pb_min)
    p = max(0, min(1, p))
    return (1 - p) * 100

def score_peg(pe, eps_growth):
    if pe <= 0 or eps_growth <= 0: return 50
    peg = pe / (eps_growth * 100)
    if peg < 0.8: return 95
    elif peg < 1.0: return 80
    elif peg < 1.2: return 65
    elif peg < 1.5: return 50
    elif peg < 2.0: return 35
    else: return 20

def score_ma(close, ma20, ma60):
    if ma20 <= 0: return 50
    dev20 = (close - ma20) / ma20 * 100
    dev60 = (close - ma60) / ma60 * 100 if ma60 > 0 else 0
    s20 = max(0, min(100, 50 - dev20 * 3))
    s60 = max(0, min(100, 50 - dev60 * 2.5))
    return s20 * 0.6 + s60 * 0.4

def score_vola(close, high, low):
    if close <= 0: return 50
    vol = (high - low) / close
    if vol < 0.01: return 85
    elif vol < 0.02: return 70
    elif vol < 0.03: return 55
    elif vol < 0.05: return 40
    else: return 20

def fetch_all_kline(code, exchange, start_date='2016-01-01'):
    """从腾讯接口获取完整K线数据（分批获取，包含high/low/volume）"""
    full_code = exchange + code
    all_kline = []
    batch_end = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    for _ in range(10):
        url = f"http://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={full_code},day,{start_date},{batch_end},500,qfq"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                jd = json.loads(resp.read().decode('utf-8'))
            kline = jd['data'][full_code]['qfqday']
            qt = jd['data'][full_code]['qt'][full_code]
        except:
            break
        if not kline:
            break
        all_kline = kline + all_kline
        batch_end = kline[0][0]
        if len(kline) < 500:
            break
        time.sleep(0.3)
    # 去重
    seen = set()
    result = []
    for row in all_kline:
        if row[0] not in seen:
            seen.add(row[0])
            result.append(row)
    result.sort(key=lambda x: x[0])
    return result, qt if 'qt' in dir() else None


def recalc_stock(html_path):
    """用meta中的正确参数和完整K线数据重新计算所有估值分"""
    name = os.path.basename(html_path).replace('-valuation.html', '')
    m = re.match(r'(.+?)(\d{6})', name)
    if not m:
        print(f"  跳过 {name}: 无法解析", flush=True)
        return
    stock_name = m.group(1)
    code = m.group(2)

    data = extract_from_html(html_path)
    if not data:
        print(f"  跳过 {name}: 无数据", flush=True)
        return

    records = data['data']
    meta = data['meta']

    # 获取参数
    pe_min = meta.get('pe_min')
    pe_max = meta.get('pe_max')
    pb_min = meta.get('pb_min')
    pb_max = meta.get('pb_max')
    eps_growth = meta.get('eps_growth')

    if not all(v is not None for v in [pe_min, pe_max, pb_min, pb_max, eps_growth]):
        print(f"  跳过 {name}: meta中缺少评分参数", flush=True)
        return

    print(f"\n重算: {stock_name}({code}) PE[{pe_min},{pe_max}] PB[{pb_min},{pb_max}] 增速{eps_growth:.0%}", flush=True)

    # 解析权重
    weights_str = meta.get('weights', '')
    weight_patterns = [
        (r'PE\(TTM\)\((\d+)%\)', 'pe'),
        (r'PEG\((\d+)%\)', 'peg'),
        (r'PB\((\d+)%\)', 'pb'),
        (r'MA偏离度\((\d+)%\)', 'ma'),
        (r'波动率\((\d+)%\)', 'vola'),
        (r'量能\((\d+)%\)', 'vol'),
        (r'ROE\((\d+)%\)', 'roe'),
        (r'股息率\((\d+)%\)', 'dividend_yield'),
    ]
    weight_map = {}
    for pattern, fk in weight_patterns:
        m = re.search(pattern, weights_str)
        if m:
            weight_map[fk] = int(m.group(1)) / 100
    total_w = sum(weight_map.values())
    if total_w > 0:
        for k in weight_map:
            weight_map[k] /= total_w

    # 从records获取latest_price/pe/pb
    last_rec = records[-1]
    latest_price = last_rec['close']
    latest_pe = last_rec['pe_ttm']
    latest_pb = last_rec['pb']
    total_shares = last_rec['market_cap'] / last_rec['close'] if last_rec['close'] > 0 else 0

    # 从腾讯接口获取完整K线（包含high/low/volume）
    exchange = meta.get('exchange', 'sh' if code.startswith('6') else 'sz')
    # 10年回测周期：从10年前到现在
    ten_years_ago = (datetime.now() - timedelta(days=365 * 10)).strftime('%Y-%m-%d')

    kline_data, qt = fetch_all_kline(code, exchange, ten_years_ago)
    if not kline_data:
        print(f"  获取K线失败，跳过", flush=True)
        return

    # 截取最近10年数据
    kline_data = [r for r in kline_data if r[0] >= ten_years_ago]

    print(f"  K线: {kline_data[0][0]} ~ {kline_data[-1][0]} ({len(kline_data)}条)", flush=True)

    # 构建记录列表
    kline_records = []
    for row in kline_data:
        close = float(row[2])
        high = float(row[3])
        low = float(row[4])
        volume = float(row[5]) if len(row) > 5 else 0
        pe_ttm = close / latest_price * latest_pe if latest_price > 0 else 0
        pb = close / latest_price * latest_pb if latest_price > 0 else 0
        kline_records.append({
            'date': row[0],
            'close': close,
            'high': high,
            'low': low,
            'volume': volume,
            'pe_ttm': pe_ttm,
            'pb': pb,
            'is_intraday': False,
        })

    # 重新计算所有分数
    closes = [r['close'] for r in kline_records]
    volumes = [r['volume'] for r in kline_records]

    scored_records = []
    for i, r in enumerate(kline_records):
        close = r['close']
        pe_ttm = r['pe_ttm']
        pb = r['pb']
        high = r['high']
        low = r['low']

        # MA
        ma20 = sum(closes[max(0, i-19):i+1]) / min(i+1, 20)
        ma60 = sum(closes[max(0, i-59):i+1]) / min(i+1, 60) if i > 0 else close

        # 量能（20日均量 vs 60日均量）
        if i >= 59 and len(volumes) > 59:
            vol20 = sum(volumes[i-19:i+1]) / 20
            vol60 = sum(volumes[i-59:i+1]) / 60
            vol_ratio = vol20 / vol60 if vol60 > 0 else 1
            if vol_ratio > 1.5: s_vol = 80
            elif vol_ratio > 1.2: s_vol = 65
            elif vol_ratio > 0.9: s_vol = 50
            elif vol_ratio > 0.7: s_vol = 35
            else: s_vol = 20
        else:
            s_vol = 50

        # 波动率（20日振幅均值）
        if i >= 19:
            vols = []
            for j in range(max(0, i-19), i+1):
                c = closes[j]
                h = kline_records[j]['high']
                l = kline_records[j]['low']
                if c > 0 and h >= 0 and l >= 0:
                    vols.append((h - l) / c)
            avg_vol = sum(vols) / len(vols) if vols else 0
            if avg_vol < 0.01: s_vola = 85
            elif avg_vol < 0.02: s_vola = 70
            elif avg_vol < 0.03: s_vola = 55
            elif avg_vol < 0.05: s_vola = 40
            else: s_vola = 20
        else:
            s_vola = 50

        # 因子得分
        s_pe = score_pe(pe_ttm, pe_min, pe_max)
        s_pb = score_pb(pb, pb_min, pb_max)
        s_peg = score_peg(pe_ttm, eps_growth)
        s_ma = score_ma(close, ma20, ma60)

        # 综合分
        factor_values_map = {'pe': s_pe, 'pb': s_pb, 'peg': s_peg, 'ma': s_ma, 'vol': s_vol, 'vola': s_vola}
        score = 0
        for fk, w in weight_map.items():
            if fk in factor_values_map:
                score += factor_values_map[fk] * w
            else:
                score += 50 * w  # 缺失因子默认50

        market_cap = total_shares * close

        scored_records.append({
            'date': r['date'],
            'close': round(close, 2),
            'pe_ttm': round(pe_ttm, 2),
            'pb': round(pb, 2),
            'market_cap': round(market_cap, 0),
            'ma20': round(ma20, 2),
            'ma60': round(ma60, 2),
            'score': round(score, 1),
            'is_intraday': r['is_intraday'],
            's_pe': round(s_pe, 1),
            's_pb': round(s_pb, 1),
            's_peg': round(s_peg, 1),
            's_ma': round(s_ma, 1),
            's_vol': round(s_vol, 1),
            's_vola': round(s_vola, 1),
        })

    # 更新meta
    meta['period'] = f"{scored_records[0]['date']} ~ {scored_records[-1]['date']}"
    meta['total_days'] = len(scored_records)

    # 更新HTML
    new_json = json.dumps({'meta': meta, 'data': scored_records}, ensure_ascii=False)
    with open(html_path, 'r', encoding='utf-8') as f:
        content = f.read()
    new_content = re.sub(
        r'var VALUATION_DATA = \{.*?\};',
        f'var VALUATION_DATA = {new_json};',
        content,
        flags=re.DOTALL
    )
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

    all_scores = [r['score'] for r in scored_records]
    latest_score = all_scores[-1]
    n = len(all_scores)
    pct = sum(1 for s in all_scores if s <= latest_score) / n * 100
    print(f"  ✓ {scored_records[0]['date']} ~ {scored_records[-1]['date']} ({len(scored_records)}天)", flush=True)
    print(f"  最新: {latest_score:.1f} | 百分位: {pct:.1f}% | 均值: {sum(all_scores)/n:.1f}", flush=True)


def process_stock(html_path):
    """处理单只股票：扩展回测周期"""
    name = os.path.basename(html_path).replace('-valuation.html', '')
    # 从文件名提取代码和交易所
    m = re.match(r'(.+?)(\d{6})', name)
    if not m:
        print(f"  跳过 {name}: 无法解析")
        return
    stock_name = m.group(1)
    code = m.group(2)
    exchange = 'sh' if code.startswith('6') else 'sz'

    data = extract_from_html(html_path)
    if not data:
        print(f"  跳过 {name}: 无数据")
        return

    records = data['data']
    meta = data['meta']
    earliest_date = records[0]['date']
    weights_label = meta.get('weights', '')

    print(f"\n{'='*60}", flush=True)
    print(f"处理: {stock_name}({code}) 交易所: {exchange}", flush=True)
    print(f"  当前数据: {earliest_date} ~ {records[-1]['date']} ({len(records)}天)", flush=True)
    print(f"  权重: {weights_label}", flush=True)

    # 如果已有数据超过10年，跳过
    first_dt = datetime.strptime(earliest_date, '%Y-%m-%d')
    if first_dt <= datetime.now() - timedelta(days=365 * 10):
        print(f"  数据已超过10年，跳过")
        return

    # 获取评分参数：优先从meta读取原始参数
    pe_min = meta.get('pe_min')
    pe_max = meta.get('pe_max')
    pb_min = meta.get('pb_min')
    pb_max = meta.get('pb_max')
    eps_growth = meta.get('eps_growth')

    if all(v is not None for v in [pe_min, pe_max, pb_min, pb_max, eps_growth]):
        print(f"  使用meta原始参数: PE[{pe_min:.1f}, {pe_max:.1f}] PB[{pb_min:.1f}, {pb_max:.1f}] 增速{eps_growth:.2%}", flush=True)
    else:
        # 回退：从已有数据反推
        pe_min, pe_max, pb_min, pb_max, eps_growth = reverse_params(records)
        print(f"  反推参数(无meta): PE[{pe_min:.1f}, {pe_max:.1f}] PB[{pb_min:.1f}, {pb_max:.1f}] 增速{eps_growth:.2%}", flush=True)

    # 从最后一条记录获取latest_price, latest_pe, latest_pb
    last_rec = records[-1]
    latest_price = last_rec['close']
    latest_pe = last_rec['pe_ttm']
    latest_pb = last_rec['pb']

    # 获取更早的K线数据（从TEN_YEARS_AGO到earliest_date）
    target_start = TEN_YEARS_AGO
    print(f"  获取更早数据: {target_start} ~ {earliest_date}", flush=True)

    # 分批获取（每批约2年，腾讯接口最多返回500条）
    new_kline = []
    seen_dates = set(r['date'] for r in records)

    # 从earliest_date往前分批获取，直到TEN_YEARS_AGO或无新数据
    batch_end = earliest_date
    batch_count = 0
    while batch_count < 10:  # 最多10批
        batch_start = TEN_YEARS_AGO
        kline_data, qt = fetch_kline(code, exchange, batch_start, batch_end)
        if not kline_data:
            break
        added = 0
        for row in kline_data:
            if row[0] not in seen_dates and row[0] < batch_end:
                new_kline.append(row)
                seen_dates.add(row[0])
                added += 1
        if added == 0:
            break
        # 更新batch_end为最早获取到的日期
        batch_end = min(r[0] for r in new_kline)
        batch_count += 1
        # 如果最早日期已经 <= TEN_YEARS_AGO，停止
        if batch_end <= TEN_YEARS_AGO:
            break

    print(f"  新增K线: {len(new_kline)}条", flush=True)

    if not new_kline:
        print(f"  无新增数据", flush=True)
        return

    # 计算新增数据的估值分
    # 先合并所有K线（新增 + 已有）
    all_records = []

    # 处理新增数据
    all_closes = [float(r[2]) for r in new_kline] + [r['close'] for r in records]
    all_dates = [r[0] for r in new_kline] + [r['date'] for r in records]

    for i, row in enumerate(new_kline):
        date_str = row[0]
        close = float(row[2])
        high = float(row[3])
        low = float(row[4])
        volume = float(row[5]) if len(row) > 5 else 0

        # 计算PE/PB
        pe_ttm = close / latest_price * latest_pe if latest_price > 0 else 0
        pb = close / latest_price * latest_pb if latest_price > 0 else 0

        # 计算MA20, MA60
        idx = i  # 在new_kline中的索引
        # 需要用全局K线序列计算MA
        # 先用已有数据的close + 新数据close
        # 但MA需要连续序列，所以需要合并

        all_records.append({
            'date': date_str,
            'close': close,
            'high': high,
            'low': low,
            'volume': volume,
            'pe_ttm': pe_ttm,
            'pb': pb,
            'is_intraday': False,
        })

    # 合并新旧数据
    for r in records:
        all_records.append({
            'date': r['date'],
            'close': r['close'],
            'high': r.get('high', r['close']),
            'low': r.get('low', r['close']),
            'volume': r.get('volume', 0),
            'pe_ttm': r['pe_ttm'],
            'pb': r['pb'],
            'is_intraday': r.get('is_intraday', False),
        })

    # 按日期排序
    all_records.sort(key=lambda x: x['date'])

    # 计算MA和评分
    closes = [r['close'] for r in all_records]
    volumes = [r['volume'] for r in all_records]

    scored_records = []
    for i, r in enumerate(all_records):
        close = r['close']
        pe_ttm = r['pe_ttm']
        pb = r['pb']

        # MA20
        if i >= 19:
            ma20 = sum(closes[i-19:i+1]) / 20
        else:
            ma20 = sum(closes[:i+1]) / (i + 1)

        # MA60
        if i >= 59:
            ma60 = sum(closes[i-59:i+1]) / 60
        else:
            ma60 = sum(closes[:i+1]) / (i + 1)

        # 量能评分（20日均量比60日均量）
        if i >= 59:
            vol20 = sum(volumes[i-19:i+1]) / 20
            vol60 = sum(volumes[i-59:i+1]) / 60
            if vol60 > 0:
                vol_ratio = vol20 / vol60
                if vol_ratio > 1.5: s_vol = 80
                elif vol_ratio > 1.2: s_vol = 65
                elif vol_ratio > 0.9: s_vol = 50
                elif vol_ratio > 0.7: s_vol = 35
                else: s_vol = 20
            else:
                s_vol = 50
        else:
            s_vol = 50

        # 波动率（20日振幅均值）
        if i >= 19:
            vols = []
            for j in range(i-19, i+1):
                c = closes[j]
                h = all_records[j]['high']
                l = all_records[j]['low']
                if c > 0:
                    vols.append((h - l) / c)
            avg_vol = sum(vols) / len(vols) if vols else 0
            if avg_vol < 0.01: s_vola = 85
            elif avg_vol < 0.02: s_vola = 70
            elif avg_vol < 0.03: s_vola = 55
            elif avg_vol < 0.05: s_vola = 40
            else: s_vola = 20
        else:
            s_vola = 50

        # 因子得分
        s_pe = score_pe(pe_ttm, pe_min, pe_max)
        s_pb = score_pb(pb, pb_min, pb_max)
        s_peg = score_peg(pe_ttm, eps_growth)
        s_ma = score_ma(close, ma20, ma60)

        # 从权重标签解析权重
        # 简化：根据已有的因子得分键来判断使用哪些因子
        weight_map = {}
        # 从已有记录中获取因子键
        old_keys = [k for k in records[-1].keys() if k.startswith('s_')]
        factor_map = {
            's_pe': ('pe', s_pe),
            's_pb': ('pb', s_pb),
            's_peg': ('peg', s_peg),
            's_ma': ('ma', s_ma),
            's_vol': ('vol', s_vol),
            's_vola': ('vola', s_vola),
        }

        # 使用已有记录的因子键
        active_factors = {}
        for ok in old_keys:
            if ok in factor_map:
                fk, fv = factor_map[ok]
                active_factors[fk] = fv

        # 从已有记录的score反推权重
        # 用最后一条记录来验证
        # 实际上，我们需要从权重标签解析权重
        # 更简单的方法：用已有记录的因子得分和总分来反推权重

        # 用最小二乘法反推权重
        # 但这太复杂了，我们直接从权重标签解析
        weight_str = weights_label
        # 解析格式: "PE(TTM)(31%) + PEG(22%) + PB(13%) + MA偏离度(13%) + 波动率(11%) + 量能(9%)"
        weight_patterns = [
            (r'PE\(TTM\)\((\d+)%\)', 'pe'),
            (r'PEG\((\d+)%\)', 'peg'),
            (r'PB\((\d+)%\)', 'pb'),
            (r'MA偏离度\((\d+)%\)', 'ma'),
            (r'波动率\((\d+)%\)', 'vola'),
            (r'量能\((\d+)%\)', 'vol'),
            (r'ROE\((\d+)%\)', 'roe'),
            (r'股息率\((\d+)%\)', 'dividend_yield'),
            (r'商品价格偏离\((\d+)%\)', 'commodity_dev'),
            (r'产能利用率\((\d+)%\)', 'capacity_util'),
            (r'NAV折价\((\d+)%\)', 'nav_discount'),
            (r'去化率\((\d+)%\)', 'clearance_rate'),
            (r'杠杆率\((\d+)%\)', 'leverage'),
            (r'研发费用率\((\d+)%\)', 'rd_ratio'),
            (r'毛利率稳定性\((\d+)%\)', 'margin_stability'),
            (r'品牌溢价度\((\d+)%\)', 'brand_premium'),
            (r'订单增速\((\d+)%\)', 'order_growth'),
            (r'营收增速\((\d+)%\)', 'revenue_growth'),
            (r'不良/偿付\((\d+)%\)', 'npl_ratio'),
        ]
        for pattern, fk in weight_patterns:
            m = re.search(pattern, weight_str)
            if m:
                weight_map[fk] = int(m.group(1)) / 100

        # 归一化
        total_w = sum(weight_map.values())
        if total_w > 0:
            for k in weight_map:
                weight_map[k] /= total_w

        # 计算综合得分
        score = 0
        for fk, w in weight_map.items():
            if fk in active_factors:
                score += active_factors[fk] * w
            elif fk == 'roe':
                # ROE因子：从已有记录中获取
                score += 50 * w  # 默认值
            elif fk == 'dividend_yield':
                score += 50 * w
            else:
                score += 50 * w  # 缺失因子默认50

        # 市值
        market_cap = close * (latest_price * latest_pe / close) / latest_pe * 100  # 简化
        # 用total_shares * close
        # 从最后一条记录反推total_shares
        total_shares = last_rec['market_cap'] / last_rec['close'] if last_rec['close'] > 0 else 0
        market_cap = total_shares * close

        scored_records.append({
            'date': r['date'],
            'close': round(close, 2),
            'pe_ttm': round(pe_ttm, 2),
            'pb': round(pb, 2),
            'market_cap': round(market_cap, 0),
            'ma20': round(ma20, 2),
            'ma60': round(ma60, 2),
            'score': round(score, 1),
            'is_intraday': r['is_intraday'],
            's_pe': round(s_pe, 1),
            's_pb': round(s_pb, 1),
            's_peg': round(s_peg, 1),
            's_ma': round(s_ma, 1),
            's_vol': round(s_vol, 1),
            's_vola': round(s_vola, 1),
        })

    # 更新meta
    meta['period'] = f"{scored_records[0]['date']} ~ {scored_records[-1]['date']}"
    meta['total_days'] = len(scored_records)

    # 计算百分位
    all_scores = [r['score'] for r in scored_records]
    sorted_scores = sorted(all_scores)
    n = len(sorted_scores)
    for r in scored_records:
        count_below = sum(1 for s in all_scores if s <= r['score'])
        r['_pct'] = round(count_below / n * 100, 1)

    new_data = {'meta': meta, 'data': scored_records}

    # 更新HTML
    new_json = json.dumps(new_data, ensure_ascii=False)
    new_content = re.sub(
        r'var VALUATION_DATA = \{.*?\};',
        f'var VALUATION_DATA = {new_json};',
        open(html_path, 'r', encoding='utf-8').read(),
        flags=re.DOTALL
    )

    # 更新HTML中的显示文本
    new_content = re.sub(
        r'统计区间[:：]\s*\d{4}-\d{2}-\d{2}\s*~\s*\d{4}-\d{2}-\d{2}\s*\(\d+个交易日\)',
        f"统计区间: {meta['period']} ({len(scored_records)}个交易日)",
        new_content
    )

    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print(f"  ✓ 扩展完成: {scored_records[0]['date']} ~ {scored_records[-1]['date']} ({len(scored_records)}天)", flush=True)

    # 输出统计
    latest_score = scored_records[-1]['score']
    count_below = sum(1 for s in all_scores if s <= latest_score)
    pct = count_below / n * 100
    print(f"  最新估值分: {latest_score:.1f} | 百分位: {pct:.1f}%", flush=True)
    print(f"  历史最高: {max(all_scores):.1f} | 最低: {min(all_scores):.1f} | 均值: {sum(all_scores)/n:.1f}", flush=True)

def main():
    recalc_mode = '--recalc' in sys.argv
    html_files = glob.glob(os.path.join(HTML_DIR, '*-valuation.html'))
    for html_path in sorted(html_files):
        name = os.path.basename(html_path)
        if 'standalone' in name or 'backtest' in name:
            continue
        try:
            if recalc_mode:
                recalc_stock(html_path)
            else:
                process_stock(html_path)
        except Exception as e:
            print(f"  ✗ 处理失败: {e}", flush=True)
            import traceback
            traceback.print_exc()
        time.sleep(0.5)  # 避免请求过快

if __name__ == '__main__':
    main()
