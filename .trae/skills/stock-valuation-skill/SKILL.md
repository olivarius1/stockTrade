# A股估值系统 Skill

基于腾讯财经K线数据，自动生成单文件自包含HTML估值分析报告的 TRAE Skill。

## 功能特性

- **8种行业估值模型**：必选消费、可选消费、科技制造、周期资源、央企基建、银行保险、地产、医药消费
- **13种估值因子**：PE、PB、PEG、MA偏离、量能、波动率 + ROE、股息率、研发费用率、毛利率稳定性、品牌溢价度、NAV折价、去化率、杠杆率、营收增速、订单增速等
- **可选因子权重归一化**：缺失可选因子时权重自动均分到已有因子
- **兼容旧模型**：`growth` 别名映射到 `staples`，`cyclical` 保持不变
- **自包含HTML输出**：内联ECharts库，无需外部依赖，单文件可直接在浏览器打开
- **全屏图表**：支持横屏查看、十字轴光标、固定tooltip
- **历史百分位**：20th/80th百分位参考线，tooltip显示历史百分位
- **6级评分系统**：极度低估(80-100)、低估(70-79)、中性偏低(60-69)、中性偏高(40-59)、高估(20-39)、极度高估(0-19)

## 文件结构

```
stock-valuation-skill/
├── SKILL.md              # Skill 描述文件（即本文件）
├── scripts/
│   ├── build_report.py    # 通用报告生成器（核心脚本）
│   ├── fetch_kline.sh     # K线数据获取脚本
│   └── batch_build.sh     # 批量构建脚本
├── _shared/
│   ├── js/
│   │   └── echarts.min.js # ECharts 库（内联到报告中）
│   └── fonts/             # 字体文件（可选）
├── reports/               # 示例报告（由脚本生成）
└── templates/
    └── growth_params.md   # 各行业估值模型参数参考
```

## 依赖

- Python 3.6+
- curl（用于获取K线数据）
- node（用于验证JS语法）

## 使用方式

### 1. 获取K线数据

```bash
# 获取2年K线（两批，各500天）
curl -sL -H "User-Agent: Mozilla/5.0" \
  "http://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600938,day,2024-07-09,2025-07-09,500,qfq" \
  -o kline_2024_2025.json
curl -sL -H "User-Agent: Mozilla/5.0" \
  "http://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600938,day,2025-07-09,2027-07-09,500,qfq" \
  -o kline_2025_2027.json
```

### 2. 生成报告

```bash
python3 scripts/build_report.py \
  <股票代码> \
  <股票名称> \
  <交易所> \
  <总股本(亿股)> \
  <PE最低> <PE最高> \
  <PB最低> <PB最高> \
  <预期增速> \
  <2025营收> <2025净利润> <毛利率> <当前市值(亿)> \
  <行业描述> \
  <报告副标题> \
  <模型类型> \
  [--可选因子:值 ...] \
  <K线文件1> [K线文件2] ...
```

**8种模型类型**：`staples`(必选消费) / `discretionary`(可选消费) / `tech`(科技制造) / `cyclical`(周期资源) / `soe`(央企基建) / `bank`(银行保险) / `realestate`(地产) / `pharma`(医药消费)

**可选因子参数格式**（`--key:value`）：

| 因子 | 参数键 | 示例 | 适用模型 |
|------|--------|------|----------|
| ROE | `--roe` | `--roe:0.15` | staples, soe, bank |
| 股息率 | `--div_yield` | `--div_yield:0.05` | soe, bank |
| 研发费用率 | `--rd_ratio` | `--rd_ratio:0.08` | tech, pharma |
| 毛利率稳定性 | `--margin_stability` | `--margin_stability:0.02` | staples |
| 品牌溢价度 | `--brand_premium` | `--brand_premium:2.0` | discretionary |
| 不良率 | `--npl_ratio` | `--npl_ratio:0.012` | bank |
| NAV折价 | `--nav_discount` | `--nav_discount:0.6` | realestate |
| 去化率 | `--clearance_rate` | `--clearance_rate:0.7` | realestate |
| 杠杆率 | `--leverage` | `--leverage:0.4` | realestate |
| 营收增速 | `--revenue_growth` | `--revenue_growth:0.2` | pharma |
| 订单增速 | `--order_growth` | `--order_growth:0.15` | soe |
| 商品价格偏离 | `--commodity_dev` | `--commodity_dev:-0.05` | cyclical |
| 产能利用率 | `--capacity_util` | `--capacity_util:0.75` | cyclical |

### 3. 示例：中国海油

```bash
python3 scripts/build_report.py 600938 "中国海油" sh 475.30 \
  6 18 0.8 3.0 0.06 \
  "3982.2" "1220.82" "51.17%" "13671" \
  "海上油气勘探开发" \
  "海上油气央企龙头估值框架与两年回测" \
  cyclical \
  kline_2024_2025.json kline_2025_2027.json
```

### 4. 3年回测（3批K线）

```bash
python3 scripts/build_report.py 603899 "晨光股份" sh 9.16 \
  10 40 1.5 5.0 0.10 \
  "250.64" "13.10" "18.36%" "196" \
  "文具龙头" \
  "文具龙头估值框架与三年回测" \
  growth \
  kline_2023_2024.json kline_2024_2025.json kline_2025_2027.json
```

## 腾讯财经API说明

- 端点：`http://web.ifzq.gtimg.cn/appstock/app/fqkline/get`
- 参数：`param={交易所}{代码},day,{起始日期},{结束日期},500,qfq`
- 交易所：上海 `sh`，深圳 `sz`
- 必须带 `User-Agent` 头，否则返回302
- 每次最多返回500天数据
- qt字段索引：3=价格, 39=PE(TTM), 44=市值(万元), 46=PB, 47=总股本
