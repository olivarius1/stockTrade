# A股估值系统

基于腾讯财经K线数据，自动生成自包含HTML估值分析报告。

## 快速开始

```bash
# 1. 获取K线数据
bash scripts/fetch_kline.sh sh600938 kline_zghy

# 2. 生成报告
python3 scripts/build_report.py 600938 "中国海油" sh 475.30 \
  6 18 0.8 3.0 0.06 \
  "3982.2" "1220.82" "51.17%" "13671" \
  "海上油气勘探开发" \
  "海上油气央企龙头估值框架与两年回测" \
  cyclical \
  kline_zghy_2024_2025.json kline_zghy_2025_2027.json
```

## 报告特性

- 自包含单文件HTML，无需外部依赖
- 内联ECharts图表库
- 全屏横屏查看 + 十字轴光标
- 历史百分位分析（20th/80th）
- 6因子加权估值模型

## 目录

```
├── SKILL.md              # Skill 完整描述
├── README.md             # 本文件
├── scripts/
│   ├── build_report.py    # 核心生成脚本
│   ├── fetch_kline.sh     # K线获取
│   └── batch_build.sh     # 批量构建
├── templates/
│   ├── thinking_flow.md   # 思考流程
│   └── growth_params.md   # 行业参数参考
├── _shared/
│   └── js/echarts.min.js # ECharts库
└── reports/              # 示例报告
```

## License

MIT
