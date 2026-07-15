# 估值报告页图表与因子展示优化 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 优化估值报告页三项体验：标识未参与因子、价格改浅灰面积图、增加百分位语义色虚线。

**Architecture:** 仅前端 `ValuationReport.vue` 改动。通过 `valuation.factors` 判断因子参与状态；调整 ECharts series 配置实现价格面积图；在 markLine.data 中合并百分位虚线与选中日期竖线。

**Tech Stack:** Vue 3 Composition API、ECharts 5.6.0、Element Plus

---

## 文件结构

- 修改：`stockTrade/frontend/src/views/ValuationReport.vue`（全部三项改动集中于此文件）

---

### Task 1: 未参与因子标识

**Files:**
- Modify: `stockTrade/frontend/src/views/ValuationReport.vue`（script 的 factorNames 后新增映射表；initFactorList 增加 participated 标记；template 表格列改造）

- [ ] **Step 1: 在 factorNames 后添加 factorKeyToCode 映射表**

在 `stockTrade/frontend/src/views/ValuationReport.vue` 的 `factorNames` 常量定义之后（约 154 行后）、`factorColors` 之前，添加：

```javascript
/**
 * 前端 factorList 的 key 与后端 factors 返回的 code 映射。
 * 用于判断该因子是否实际参与当前估值模型的计算。
 */
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

- [ ] **Step 2: 修改 initFactorList 添加 participated 标记**

将 `initFactorList` 函数替换为：

```javascript
const initFactorList = () => {
  const latest = latestFactors.value
  // valuation.factors 是后端返回的参与计算的因子 code 集合
  const participatedCodes = valuation.value?.factors
    ? Object.keys(valuation.value.factors)
    : []
  factorList.value = Object.keys(factorNames).map(key => {
    const code = factorKeyToCode[key]
    return {
      name: factorNames[key],
      key: key,
      // 该因子是否参与当前模型计算
      participated: participatedCodes.includes(code),
      // 携带该因子的色系对，模板中直接取用
      deepColor: factorColors[key]?.deep || '#409EFF',
      lightColor: factorColors[key]?.light || '#d9ecff',
      latestScore: latest[key] || 0,
      selectedScore: latest[key] || 0
    }
  })
}
```

- [ ] **Step 3: 修改模板因子列显示「未参与」标注**

将 template 中 `<el-table-column prop="name" label="因子" width="140" />` 替换为：

```html
<el-table-column label="因子" width="160">
  <template #default="{ row }">
    <span>{{ row.name }}</span>
    <span v-if="!row.participated" class="not-participated-tag">未参与</span>
  </template>
</el-table-column>
```

- [ ] **Step 4: 修改得分对比列，未参与时不显示进度条**

将得分对比列的 template 替换为：

```html
<el-table-column label="得分对比" min-width="320">
  <template #default="{ row }">
    <!-- 未参与因子：显示灰色文字，不渲染进度条 -->
    <div v-if="!row.participated" class="not-participated-cell">未参与</div>
    <div v-else class="dual-bar">
      <!-- 上方深色：最新一天，用该因子的深色 -->
      <div class="bar-row bar-latest">
        <span class="bar-tag bar-tag-latest">最新</span>
        <el-progress
          :percentage="Math.round(row.latestScore)"
          :color="row.deepColor"
          :stroke-width="14"
          :show-text="false"
        />
        <span class="bar-value">{{ row.latestScore.toFixed(1) }}</span>
      </div>
      <!-- 下方浅色：选择的历史日期，用该因子的同色系浅色 -->
      <div v-if="showCompare" class="bar-row bar-selected">
        <span class="bar-tag bar-tag-selected">历史</span>
        <el-progress
          :percentage="Math.round(row.selectedScore)"
          :color="row.lightColor"
          :stroke-width="14"
          :show-text="false"
        />
        <span class="bar-value">{{ row.selectedScore.toFixed(1) }}</span>
      </div>
    </div>
  </template>
</el-table-column>
```

- [ ] **Step 5: 修改变化列，未参与时显示「—」**

将变化列的 template 替换为：

```html
<el-table-column label="变化" width="80" v-if="showCompare">
  <template #default="{ row }">
    <span v-if="!row.participated">—</span>
    <span v-else :class="getDeltaClass(row.latestScore - row.selectedScore)">
      {{ formatDelta(row.latestScore - row.selectedScore) }}
    </span>
  </template>
</el-table-column>
```

- [ ] **Step 6: 添加未参与相关样式**

在 `<style scoped>` 中 `.bar-value` 样式之后添加：

```css
/* 未参与因子标注：灰色小标签紧跟因子名称 */
.not-participated-tag {
  margin-left: 6px;
  padding: 1px 6px;
  font-size: 11px;
  color: #909399;
  background: #f5f5f5;
  border: 1px solid #e4e7ed;
  border-radius: 3px;
}
/* 未参与因子得分单元格：灰色居中文字 */
.not-participated-cell {
  color: #c0c4cc;
  font-size: 13px;
  text-align: center;
  padding: 8px 0;
}
```

- [ ] **Step 7: 构建前端验证编译通过**

Run: `cd stockTrade && docker compose build --no-cache frontend 2>&1 | tail -5`
Expected: 输出 `Image stocktrade-frontend Built`，无编译错误

- [ ] **Step 8: 重启容器并验证科技股未参与因子**

Run: `cd stockTrade && docker compose up -d frontend 2>&1 | tail -3`
Expected: 容器重启成功

验证：浏览器访问 `http://localhost:8080`，进入科技股报告页（如 600519），因子表中 roe/股息率/AI 三行应显示灰色「未参与」标注，得分列显示「未参与」文字。

- [ ] **Step 9: Commit**

```bash
cd stockTrade
git add frontend/src/views/ValuationReport.vue
git commit -m "feat: 标识未参与计算的因子"
```

---

### Task 2: 价格改为浅灰面积图

**Files:**
- Modify: `stockTrade/frontend/src/views/ValuationReport.vue`（updateChartOption 中 series 配置）

- [ ] **Step 1: 修改估值分 series 增强视觉主体地位**

将 `updateChartOption` 中 series 数组的第一项（估值分）替换为：

```javascript
{
  name: '估值分', type: 'line', data: scores, smooth: true,
  // 粗线 + 数据点，保持视觉主体地位
  symbol: 'circle', symbolSize: 6,
  lineStyle: { width: 3, color: '#409EFF' },
  itemStyle: { color: '#409EFF' },
  emphasis: { itemStyle: { borderWidth: 2 } },
  // z 层级在上，避免被价格面积图遮挡
  z: 2,
  markPoint,
  markLine,
},
```

- [ ] **Step 2: 修改价格 series 改为浅灰面积图**

将 series 数组的第二项（价格）替换为：

```javascript
{
  name: '价格', type: 'line', yAxisIndex: 1, data: prices, smooth: true,
  // 浅灰细线 + 半透明面积填充，视觉弱化不抢主视觉
  symbol: 'none',
  lineStyle: { width: 1, color: '#c0c4cc' },
  areaStyle: { color: 'rgba(192,196,204,0.25)' },
  itemStyle: { color: '#c0c4cc' },
  // z 层级在下，作为背景参考
  z: 1,
},
```

- [ ] **Step 3: 构建并重启验证**

Run: `cd stockTrade && docker compose build --no-cache frontend 2>&1 | tail -3 && docker compose up -d frontend 2>&1 | tail -3`
Expected: 构建成功，容器重启

验证：浏览器访问报告页，价格曲线应为浅灰色面积图（半透明填充），估值分蓝色粗线在上层清晰可见，两者不再视觉混淆。

- [ ] **Step 4: Commit**

```bash
cd stockTrade
git add frontend/src/views/ValuationReport.vue
git commit -m "feat: 价格曲线改为浅灰面积图，增强与估值分的视觉区分"
```

---

### Task 3: 增加百分位语义色虚线

**Files:**
- Modify: `stockTrade/frontend/src/views/ValuationReport.vue`（updateChartOption 中 markLine 构建）

- [ ] **Step 1: 在 updateChartOption 中构建合并的 markLine**

将 `updateChartOption` 中 markLine 构建部分替换为：

```javascript
  // 百分位参考线（语义色）+ 选中日期竖线，合并到同一 markLine
  // 百分位线始终显示，选中竖线仅对比时显示
  const markLineData = [
    // 80% 极度低估阈值（绿）
    {
      yAxis: 80,
      lineStyle: { color: '#10b981', type: 'dashed', width: 1.5 },
      label: { show: true, formatter: '80', position: 'end', color: '#10b981', fontSize: 11 }
    },
    // 40% 中性阈值（橙）
    {
      yAxis: 40,
      lineStyle: { color: '#f59e0b', type: 'dashed', width: 1.5 },
      label: { show: true, formatter: '40', position: 'end', color: '#f59e0b', fontSize: 11 }
    },
    // 20% 高估阈值（红）
    {
      yAxis: 20,
      lineStyle: { color: '#ef4444', type: 'dashed', width: 1.5 },
      label: { show: true, formatter: '20', position: 'end', color: '#ef4444', fontSize: 11 }
    }
  ]

  // 选中日期竖线，仅对比时添加
  if (selectedIdx >= 0) {
    markLineData.push({
      xAxis: selectedIdx,
      lineStyle: { color: '#f56c6c', type: 'dashed', width: 1.5 },
      label: { show: false }
    })
  }

  const markLine = {
    symbol: 'none',
    silent: true,
    data: markLineData
  }
```

- [ ] **Step 2: 删除旧的独立 markLine 构建代码**

确认上一步替换覆盖了原来的两段代码：
- 旧的「选中点位的竖直辅助线」markLine 构建（`const markLine = selectedIdx >= 0 ? {...}`）
- 确保不再有重复的 markLine 定义

- [ ] **Step 3: 构建并重启验证**

Run: `cd stockTrade && docker compose build --no-cache frontend 2>&1 | tail -3 && docker compose up -d frontend 2>&1 | tail -3`
Expected: 构建成功，容器重启

验证：浏览器访问报告页，图表应有三条横向虚线：
- 80 线绿色，右端标注「80」
- 40 线橙色，右端标注「40」
- 20 线红色，右端标注「20」
选中历史日期时，红色竖线与三条百分位线共存。

- [ ] **Step 4: Commit**

```bash
cd stockTrade
git add frontend/src/views/ValuationReport.vue
git commit -m "feat: 增加估值分百分位语义色虚线（80/40/20）"
```

---

## 自检

**Spec 覆盖：**
- 需求1（未参与因子标识）→ Task 1 ✓
- 需求2（价格浅灰面积图）→ Task 2 ✓
- 需求3（百分位语义色虚线）→ Task 3 ✓

**类型一致性：**
- `participated` 字段在 initFactorList 中定义，在 template 三处使用 ✓
- markLine 在 updateChartOption 中统一定义，refreshChartMark 调用 updateChartOption ✓

**无占位符：** 所有步骤含完整代码 ✓
