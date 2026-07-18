---
name: stock-valuation-skill
description: A股估值分析Skill，自动获取东方财富年报/季报数据+腾讯财经10年K线，生成自包含HTML估值回测报告。支持8种行业模型、19种估值因子、财务报表自动校准、浅灰色面积图、全屏图表。
---

# A股估值系统 Skill

基于腾讯财经K线数据和东方财富财务报表API，自动生成单文件自包含HTML估值分析报告的独立Skill。不依赖后端系统代码。

## 功能特性

- **8种行业估值模型**：必选消费、可选消费、科技制造、周期资源、央企基建、银行保险、地产、医药消费
- **19种估值因子**：6种基础因子（PE、PB、PEG、MA偏离、量能、波动率）+ 13种可选因子（ROE、股息率、研发费用率、毛利率稳定性、品牌溢价度、NAV折价、去化率、杠杆率、营收增速、订单增速、商品价格偏离、产能利用率、不良率）
- **财务报表自动获取**：从东方财富API自动拉取历年年报、半年报、季报，自动计算并填充ROE、毛利率稳定性、营收增速等因子
- **10年K线自动获取**：未提供K线文件时自动从腾讯财经API拉取最近10年日K线数据（不足则用最长可用数据）
- **可选因子权重归一化**：缺失可选因子时权重自动均分到已有因子
- **兼容旧模型**：`growth` 别名映射到 `staples`
- **自包含HTML输出**：内联ECharts库，无需外部依赖，单文件可直接在浏览器打开
- **全屏图表**：支持横屏查看、十字轴光标、固定tooltip
- **历史百分位**：20th/80th百分位参考线，tooltip显示历史百分位
- **浅灰色面积图**：收盘价以浅灰色渐变面积图作为背景展示
- **财务报表摘要卡片**：报告中展示可用年报数、近5年平均ROE、近5年平均毛利率、5年营收CAGR等
- **6级评分系统**：极度低估(80-100)、低估(70-79)、中性偏低(60-69)、中性偏高(40-59)、高估(20-39)、极度高估(0-19)

## 文件结构

```
stock-valuation-skill/
├── SKILL.md              # Skill 描述文件（即本文件）
├── scripts/
│   ├── build_report.py        # 报告生成入口（调用report_generator.py）
│   ├── report_generator.py    # 核心报告生成器（独立副本，不依赖后端）
│   ├── financial_fetcher.py   # 财务报表数据获取器（东方财富API）
│   ├── db_manager.py          # DB模式支持（可选）
│   ├── fetch_kline.sh         # K线数据获取脚本
│   └── batch_build.sh         # 批量构建脚本
├── _shared/
│   ├── js/
│   │   └── echarts.min.js     # ECharts 库（内联到报告中）
│   └── fonts/                  # 字体文件（可选）
├── reports/                    # 示例报告（由脚本生成）
└── templates/
    ├── growth_params.md        # 各行业估值模型参数参考
    └── thinking_flow.md        # 分析思维流程
```

## 依赖

- Python 3.6+
- 网络访问（用于东方财富和腾讯财经API）

## 使用方式

### 1. 最简用法（自动获取10年K线+财务报表）

```bash
python scripts/build_report.py \
  <股票代码> <股票名称> <交易所> \
  <总股本(亿股)> \
  <PE最低> <PE最高> <PB最低> <PB最高> <预期增速> \
  <营收> <净利润> <毛利率> <当前市值(亿)> \
  <行业描述> <报告副标题> <模型类型> \
  [--可选因子:值 ...]
```

无需手动获取K线文件，脚本会自动从腾讯财经API拉取10年数据，并从东方财富API获取财务报表自动填充因子。

### 2. 手动提供K线文件

```bash
# 获取K线数据
curl -sL -H "User-Agent: Mozilla/5.0" \
  "http://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600887,day,2024-07-09,2025-07-09,500,qfq" \
  -o kline_2024_2025.json

# 使用K线文件生成报告
python scripts/build_report.py 600887 "伊利股份" sh 63.25 \
  15 35 2.0 5.0 0.08 \
  "1156.36" "115.65" "34%" "1571" \
  "乳制品龙头" "乳制品龙头估值框架与10年回测" \
  staples \
  kline_2024_2025.json
```

### 3. 带可选因子

```bash
python scripts/build_report.py 601899 "紫金矿业" sh 265.91 \
  10 35 1.5 6.0 0.12 \
  "3490.8" "517.77" "27.7%" "7666" \
  "有色金属采选" "有色金属龙头估值框架与10年回测" \
  cyclical \
  --commodity_dev:-0.05 --capacity_util:0.85
```

**8种模型类型**：`staples`(必选消费) / `discretionary`(可选消费) / `tech`(科技制造) / `cyclical`(周期资源) / `soe`(央企基建) / `bank`(银行保险) / `realestate`(地产) / `pharma`(医药消费)

**可选因子参数格式**（`--key:value`）：

| 因子 | 参数键 | 示例 | 适用模型 |
|------|--------|------|----------|
| ROE | `--roe` | `--roe:0.15` | soe, bank |
| 股息率 | `--div_yield` | `--div_yield:0.05` | soe, bank |
| 研发费用率 | `--rd_ratio` | `--rd_ratio:0.08` | tech |
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

> 未指定的可选因子将自动从东方财富财务报表数据中计算填充（ROE、毛利率稳定性、营收增速）。

## 数据来源

- **腾讯财经K线API**：`http://web.ifzq.gtimg.cn/appstock/app/fqkline/get`
  - 每次最多返回500天数据，脚本自动分批获取
  - 必须带 `User-Agent` 头
- **东方财富数据中心API**：`https://datacenter.eastmoney.com/securities/api/data/v1/get`
  - 获取历年年报、半年报、季报核心财务指标
  - 自动计算ROE均值、毛利率稳定性、营收同比等

## 输出

- 报告输出到项目根目录的 `local_reports/` 文件夹
- 文件名格式：`{股票名称}{股票代码}-valuation.html`
- 单文件自包含（内联ECharts），可直接在浏览器打开
