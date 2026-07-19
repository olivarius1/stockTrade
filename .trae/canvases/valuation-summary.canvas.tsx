import { Divider, Grid, H1, H2, Stack, Stat, Table, Text } from 'qoder/canvas';

export default function ValuationReportSummary() {
  return (
    <Stack gap={20}>
      <H1>A股估值报告生成摘要</H1>
      <Text tone="secondary" size="small">2026-07-18 · stock-valuation-skill · local_reports</Text>

      <Divider />

      <H2>生成结果</H2>
      <Grid columns={2} gap={16}>
        <Stat value="63.8" label="伊利股份 最新评分" tone="success" />
        <Stat value="61.4" label="紫金矿业 最新评分" tone="success" />
        <Stat value="2" label="报告数量" />
        <Stat value="484天" label="回测区间" />
      </Grid>

      <Divider />

      <H2>伊利股份 (600887) — 必选消费模型</H2>
      <Table
        headers={['参数', '数值']}
        rows={[
          ['模型类型', 'staples（必选消费）'],
          ['总股本', '63.25 亿股'],
          ['PE 区间', '15 ~ 35'],
          ['PB 区间', '2.0 ~ 5.0'],
          ['预期增速', '8%'],
          ['2025 营收', '1156.36 亿元'],
          ['2025 净利润', '115.65 亿元'],
          ['毛利率', '~34%'],
          ['当前市值', '1571 亿元'],
          ['毛利率稳定性', '0.03'],
          ['5年营收增长率', '4%'],
          ['评分均值', '64.9（中性偏低）'],
          ['评分最高 / 最低', '75.2 / 51.2'],
        ]}
      />

      <Divider />

      <H2>紫金矿业 (601899) — 周期资源模型</H2>
      <Table
        headers={['参数', '数值']}
        rows={[
          ['模型类型', 'cyclical（周期资源）'],
          ['总股本', '265.91 亿股'],
          ['PE 区间', '10 ~ 35'],
          ['PB 区间', '1.5 ~ 6.0'],
          ['预期增速', '12%'],
          ['2025 营收', '3490.8 亿元'],
          ['2025 净利润', '517.77 亿元'],
          ['毛利率', '27.7%'],
          ['当前市值', '7666 亿元'],
          ['商品价格偏离', '-5%'],
          ['产能利用率', '85%'],
          ['5年营收增长率', '15%'],
          ['评分均值', '64.2（中性偏低）'],
          ['评分最高 / 最低', '77.1 / 38.5'],
        ]}
      />

      <Divider />

      <H2>报告文件</H2>
      <Table
        headers={['文件名', '大小', '位置']}
        rows={[
          ['伊利股份600887-valuation.html', '~1.15 MB', 'local_reports/'],
          ['紫金矿业601899-valuation.html', '~1.15 MB', 'local_reports/'],
        ]}
      />

      <Text tone="secondary" size="small">
        报告为自包含 HTML 文件，内联 ECharts，直接用浏览器打开即可查看完整图表与回测分析。
      </Text>
    </Stack>
  );
}
