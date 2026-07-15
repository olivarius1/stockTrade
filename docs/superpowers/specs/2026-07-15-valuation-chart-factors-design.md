# 估值报告页图表与因子展示优化设计

## 背景

估值报告页（`ValuationReport.vue`）存在三个体验问题：

1. **因子表显示全部 9 个因子**：前端 `factorNames` 写死全部因子，但不同估值模型实际参与的因子不同（如科技股模型不含 roe/dividend/ai），未参与因子在历史数据中为 null，表格却正常渲染进度条，误导用户。
2. **估值分与价格曲线视觉重叠**：两者同为 line 类型，颜色不同但视觉权重相近，重叠时难以区分。
3. **估值分缺乏百分位参考**：仅有 0-100 的 Y 轴刻度，用户无法直观判断当前分值处于低估/中性/高估区间。

## 设计

### 1. 未参与因子标识

#### 数据源

`/api/valuation/report/{code}` 返回的 `valuation.factors` 是实际参与计算的因子 code 集合（如 `{"pe": 50.0, "pb": 95.0, ...}`）。以此作为参与判断依据。

#### key 映射

前端 `factorNames` 的 key（如 `pe_score`）与后端 factor code（如 `pe`）存在命名差异，需建立映射：

```javascript
const factorKeyToCode = {
  pe_score: 'pe',
  pb_score: 'pb',
  peg_score: 'peg',
  ma_score: 'ma_deviation',
  volatility_score: 'volatility',
  volume_score: 'volume',
  roe_score: 'roe',
  dividend_score: 'dividend',
  ai_score: 'ai_analysis'
}
```

#### 标记逻辑

- `initFactorList` 时根据 `valuation.factors` 是否包含对应 code，标记每项 `participated: true/false`
- 未参与行：
  - 因子名称后追加灰色"(未参与)"标注
  - 得分对比列显示灰色"未参与"文字，不渲染进度条
  - 对比模式下不显示历史进度条，变化列显示"—"

### 2. 价格改为浅灰面积图

#### series 配置调整

- **估值分**（上层）：
  - `lineStyle.width: 3`，`symbolSize: 6`，`itemStyle.color: '#409EFF'`
  - `z: 2`，保持视觉主体地位
- **价格**（下层）：
  - `lineStyle: { width: 1, color: '#c0c4cc' }`（浅灰细线）
  - `areaStyle: { color: 'rgba(192,196,204,0.25)' }`（浅灰半透明填充）
  - `symbol: 'none'`（不显示数据点，避免点击干扰）
  - `z: 1`
- 双 Y 轴保持不变，价格轴视觉弱化

### 3. 百分位语义色虚线

#### markLine 合并

百分位虚线与选中日期竖线合并到估值分 series 的 `markLine.data`：

- `yAxis: 80` → `#10b981`（绿，极度低估阈值）
- `yAxis: 40` → `#f59e0b`（橙，中性阈值）
- `yAxis: 20` → `#ef4444`（红，高估阈值）

#### 样式

- `type: 'dashed'`，`width: 1.5`
- label `position: 'end'`，仅显示数值（"80"/"40"/"20"）
- 选中日期竖线保持红色虚线，一并放入 markLine.data

#### 刷新时机

与现有 `refreshChartMark` 一致：selectedDate 变化时调用 `updateChartOption` 重建 markLine。

## 影响范围

仅前端 `ValuationReport.vue`，不涉及后端改动。

## 验证

- 科技股（tech 模型）：roe/dividend/ai 显示"未参与"
- 银行股（bank 模型）：peg/volume/ai 显示"未参与"
- 价格曲线为浅灰面积图，估值分蓝色粗线在上层清晰可见
- 三条百分位虚线（绿/橙/红）显示在右侧标注 80/40/20
- 选中历史日期时，红色竖线与百分位线共存
