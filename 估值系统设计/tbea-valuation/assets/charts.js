(function() {
  var style = getComputedStyle(document.documentElement);
  var accent = style.getPropertyValue('--accent').trim();
  var accent2 = style.getPropertyValue('--accent2').trim();
  var ink = style.getPropertyValue('--ink').trim();
  var muted = style.getPropertyValue('--muted').trim();
  var rule = style.getPropertyValue('--rule').trim();
  var bg2 = style.getPropertyValue('--bg2').trim();
  var success = style.getPropertyValue('--success').trim();
  var warn = style.getPropertyValue('--warn').trim();
  var danger = style.getPropertyValue('--danger').trim();

  var palette = [accent, accent2, success, warn, muted, accent + '99', accent2 + '99'];

  // --- Chart 1: Profit vs PE (2022-2025) ---
  var chart1 = echarts.init(document.getElementById('chart-profit-pe'), null, { renderer: 'svg' });
  chart1.setOption({
    animation: false,
    tooltip: { trigger: 'axis', appendToBody: true },
    legend: { data: ['归母净利润(亿元)', 'TTM PE'], bottom: 0, textStyle: { color: ink } },
    grid: { left: 70, right: 70, top: 30, bottom: 50 },
    xAxis: { type: 'category', data: ['2022', '2023', '2024', '2025'], axisLabel: { color: muted }, axisLine: { lineStyle: { color: rule } } },
    yAxis: [
      { type: 'value', name: '净利润(亿元)', nameTextStyle: { color: muted }, axisLabel: { color: muted }, splitLine: { lineStyle: { color: rule } } },
      { type: 'value', name: 'PE(倍)', nameTextStyle: { color: muted }, axisLabel: { color: muted }, splitLine: { show: false } }
    ],
    series: [
      {
        name: '归母净利润(亿元)', type: 'bar', data: [228.85, 140.93, 41.35, 59.54],
        itemStyle: { color: accent }, barWidth: '40%', yAxisIndex: 0
      },
      {
        name: 'TTM PE', type: 'line', data: [4.5, 8.2, 28.6, 18.5],
        itemStyle: { color: accent2 }, lineStyle: { width: 3 }, symbol: 'circle', symbolSize: 10, yAxisIndex: 1
      }
    ]
  });
  window.addEventListener('resize', function() { chart1.resize(); });

  // --- Chart 2: EV/EBITDA Historical Percentile ---
  var chart2 = echarts.init(document.getElementById('chart-ev-ebitda'), null, { renderer: 'svg' });
  var evEbitdaData = [7.2, 6.8, 8.5, 9.1, 10.3, 12.5, 11.2, 9.8, 8.2, 8.8];
  var years = ['2016', '2017', '2018', '2019', '2020', '2021', '2022', '2023', '2024', '2025'];
  var avg = evEbitdaData.reduce(function(a, b) { return a + b; }, 0) / evEbitdaData.length;

  chart2.setOption({
    animation: false,
    tooltip: { trigger: 'axis', appendToBody: true, formatter: function(p) { return p[0].name + '<br/>EV/EBITDA: ' + p[0].value + 'x'; } },
    grid: { left: 60, right: 30, top: 30, bottom: 40 },
    xAxis: { type: 'category', data: years, axisLabel: { color: muted }, axisLine: { lineStyle: { color: rule } } },
    yAxis: { type: 'value', name: 'EV/EBITDA (倍)', min: 4, nameTextStyle: { color: muted }, axisLabel: { color: muted }, splitLine: { lineStyle: { color: rule } } },
    series: [
      {
        type: 'bar', data: evEbitdaData.map(function(v, i) {
          return { value: v, itemStyle: { color: v > 10 ? accent2 : v < 8 ? success : accent } };
        }), barWidth: '50%'
      },
      {
        type: 'line', data: Array(10).fill(avg), lineStyle: { color: muted, type: 'dashed', width: 2 },
        symbol: 'none', name: '10年均值(' + avg.toFixed(1) + 'x)', label: { show: true, position: 'end', color: muted, fontSize: 11, formatter: '均值 ' + avg.toFixed(1) + 'x' }
      }
    ]
  });
  window.addEventListener('resize', function() { chart2.resize(); });

  // --- Chart 3: Valuation Method Comparison ---
  var chart3 = echarts.init(document.getElementById('chart-valuation-comparison'), null, { renderer: 'svg' });
  chart3.setOption({
    animation: false,
    tooltip: { trigger: 'axis', appendToBody: true, formatter: function(p) { return p[0].name + '<br/>估值区间: ' + p[0].value[0] + ' - ' + p[0].value[1] + ' 亿元'; } },
    grid: { left: 140, right: 40, top: 20, bottom: 30 },
    xAxis: { type: 'value', name: '估值(亿元)', nameTextStyle: { color: muted }, axisLabel: { color: muted }, splitLine: { lineStyle: { color: rule } }, min: 600, max: 1800 },
    yAxis: {
      type: 'category',
      data: ['场景加权DCF', '周期修正DCF', 'EV/EBITDA分位', 'CAPE周期PE', 'SOTP分部估值'],
      axisLabel: { color: ink, fontSize: 12, fontWeight: 600 },
      axisLine: { lineStyle: { color: rule } }
    },
    series: [{
      type: 'bar', data: [
        { value: [1065, 1320], itemStyle: { color: accent + '66' } },
        { value: [1000, 1300], itemStyle: { color: accent + '88' } },
        { value: [950, 1250], itemStyle: { color: accent + 'aa' } },
        { value: [930, 1550], itemStyle: { color: accent + 'cc' } },
        { value: [982, 1224], itemStyle: { color: accent } }
      ],
      barWidth: '55%',
      label: {
        show: true, position: 'right', color: ink, fontSize: 11,
        formatter: function(p) { return p.value[0] + ' - ' + p.value[1]; }
      }
    }, {
      type: 'line', data: Array(5).fill(1100), lineStyle: { color: accent2, type: 'dashed', width: 2 },
      symbol: 'none', name: '当前市值~1,100亿',
      label: { show: true, position: 'end', color: accent2, fontSize: 11, formatter: '当前市值 1,100亿' }
    }]
  });
  window.addEventListener('resize', function() { chart3.resize(); });

  // --- Chart 4: Risk Premium Decomposition ---
  var chart4 = echarts.init(document.getElementById('chart-risk-premium'), null, { renderer: 'svg' });
  chart4.setOption({
    animation: false,
    tooltip: { trigger: 'axis', appendToBody: true },
    grid: { left: 120, right: 40, top: 20, bottom: 30 },
    xAxis: { type: 'value', name: '溢价(基点 bps)', nameTextStyle: { color: muted }, axisLabel: { color: muted }, splitLine: { lineStyle: { color: rule } } },
    yAxis: {
      type: 'category',
      data: ['财务风险', '减值风险', '电网投资', '铜价波动', '海外地缘', '电力市场化', '新能源消纳', '硅料价格'],
      axisLabel: { color: ink, fontSize: 11 },
      axisLine: { lineStyle: { color: rule } }
    },
    series: [{
      type: 'bar',
      data: [
        { value: 75, itemStyle: { color: accent + '66' } },
        { value: 75, itemStyle: { color: accent + '66' } },
        { value: 75, itemStyle: { color: accent + '88' } },
        { value: 100, itemStyle: { color: accent + '99' } },
        { value: 200, itemStyle: { color: accent2 + '99' } },
        { value: 150, itemStyle: { color: accent2 + 'aa' } },
        { value: 150, itemStyle: { color: accent2 + 'cc' } },
        { value: 250, itemStyle: { color: accent2 } }
      ],
      barWidth: '50%',
      label: { show: true, position: 'right', color: ink, fontSize: 11, formatter: '+{c}bps' }
    }]
  });
  window.addEventListener('resize', function() { chart4.resize(); });

  // --- Chart 6: Valuation Score Backtest ---
  var chart6Container = document.getElementById('chart-backtest');
  if (chart6Container && typeof VALUATION_DATA !== 'undefined') {
    {
        var data = VALUATION_DATA.data;
        var dates = data.map(function(d) { return d.date; });
        var scores = data.map(function(d) { return d.score; });
        var closes = data.map(function(d) { return d.close; });
        var peTTMs = data.map(function(d) { return d.pe_ttm; });
        var marketCaps = data.map(function(d) { return d.market_cap; });

        var chart6 = echarts.init(chart6Container, null, { renderer: 'svg' });
        chart6.setOption({
          animation: false,
          tooltip: {
            trigger: 'axis',
            appendToBody: true,
            formatter: function(p) {
              var idx = p[0].dataIndex;
              var d = data[idx];
              return '<strong>' + d.date + '</strong><br/>' +
                '估值分: <strong>' + d.score + '</strong><br/>' +
                '收盘价: ' + d.close + ' 元<br/>' +
                'PE(TTM): ' + d.pe_ttm + '<br/>' +
                'PB: ' + d.pb + '<br/>' +
                '总市值: ' + d.market_cap.toFixed(0) + ' 亿<br/>' +
                'MA20: ' + d.ma20 + ' / MA60: ' + d.ma60;
            }
          },
          legend: {
            data: ['估值分(0-100)', '收盘价(元)', 'PE(TTM)', '总市值(亿元)'],
            bottom: 0, textStyle: { color: ink, fontSize: 11 }
          },
          grid: { left: 60, right: 75, top: 50, bottom: 55 },
          xAxis: {
            type: 'category', data: dates,
            axisLabel: {
              color: muted, fontSize: 10, rotate: 45,
              formatter: function(v) { return v.substring(5); }
            },
            axisLine: { lineStyle: { color: rule } }
          },
          yAxis: [
            {
              type: 'value', name: '估值分', min: 0, max: 100,
              nameTextStyle: { color: accent },
              axisLabel: { color: accent },
              splitLine: { lineStyle: { color: rule } }
            },
            {
              type: 'value', name: '价格/PE/市值',
              nameTextStyle: { color: muted },
              axisLabel: { color: muted },
              splitLine: { show: false }
            }
          ],
          series: [
            {
              name: '估值分(0-100)', type: 'line', data: scores, yAxisIndex: 0,
              lineStyle: { color: accent, width: 2.5 },
              itemStyle: { color: accent },
              symbol: 'none',
              areaStyle: {
                color: {
                  type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
                  colorStops: [
                    { offset: 0, color: accent + '44' },
                    { offset: 1, color: accent + '05' }
                  ]
                }
              },
              markLine: {
                silent: true,
                data: [
                  { yAxis: 70, label: { formatter: '低估区间', position: 'insideEndTop', color: success, fontSize: 10 }, lineStyle: { color: success, type: 'dashed', width: 1 } },
                  { yAxis: 40, label: { formatter: '高估区间', position: 'insideEndBottom', color: danger, fontSize: 10 }, lineStyle: { color: danger, type: 'dashed', width: 1 } }
                ]
              },
              z: 5
            },
            {
              name: '收盘价(元)', type: 'line', data: closes, yAxisIndex: 1,
              lineStyle: { color: accent2, width: 1.5 },
              itemStyle: { color: accent2 },
              symbol: 'none', z: 3
            },
            {
              name: 'PE(TTM)', type: 'line', data: peTTMs, yAxisIndex: 1,
              lineStyle: { color: warn + '88', width: 1 },
              itemStyle: { color: warn },
              symbol: 'none', z: 2
            },
            {
              name: '总市值(亿元)', type: 'bar', data: marketCaps, yAxisIndex: 1,
              itemStyle: { color: bg2, opacity: 0.5 },
              barWidth: '60%', barGap: '-100%', z: 1
            }
          ]
        });
        window.addEventListener('resize', function() { chart6.resize(); });
    }
  }

  // --- Fallback: Pure Canvas backtest chart (if ECharts fails) ---
  (function() {
    var el = document.getElementById('chart-backtest');
    if (!el || typeof VALUATION_DATA === 'undefined') return;
    // Check if ECharts already rendered (has SVG or Canvas child)
    var rendered = el.querySelector('svg') || el.querySelector('canvas');
    if (rendered) return;
    // Pure Canvas fallback
    var canvas = document.createElement('canvas');
    canvas.style.width = '100%';
    canvas.style.height = '500px';
    el.innerHTML = '';
    el.appendChild(canvas);
    var W = el.clientWidth || 800;
    var H = 500;
    canvas.width = W * 2;
    canvas.height = H * 2;
    canvas.style.width = W + 'px';
    canvas.style.height = H + 'px';
    var ctx = canvas.getContext('2d');
    ctx.scale(2, 2);

    var data = VALUATION_DATA.data;
    if (!data || data.length === 0) return;
    var scores = data.map(function(d) { return d.score; });
    var closes = data.map(function(d) { return d.close; });
    var dates = data.map(function(d) { return d.date.substring(5); });
    var n = data.length;

    var pad = { t: 20, r: 55, b: 60, l: 50 };
    var cw = W - pad.l - pad.r;
    var ch = H - pad.t - pad.b;
    var minS = 0, maxS = 100;
    var minC = Math.min.apply(null, closes) * 0.9;
    var maxC = Math.max.apply(null, closes) * 1.1;
    if (minC === maxC) maxC = minC + 1;

    function x(i) { return pad.l + (i / (n - 1)) * cw; }
    function yScore(v) { return pad.t + (1 - (v - minS) / (maxS - minS)) * ch; }
    function yClose(v) { return pad.t + (1 - (v - minC) / (maxC - minC)) * ch; }

    // Background
    ctx.fillStyle = '#fafaf9';
    ctx.fillRect(0, 0, W, H);

    // Grid lines
    ctx.strokeStyle = '#d4d0c8';
    ctx.lineWidth = 0.5;
    for (var i = 0; i <= 4; i++) {
      var yy = pad.t + (i / 4) * ch;
      ctx.beginPath(); ctx.moveTo(pad.l, yy); ctx.lineTo(W - pad.r, yy); ctx.stroke();
      ctx.fillStyle = '#6b6b6b';
      ctx.font = '10px sans-serif';
      ctx.textAlign = 'right';
      ctx.fillText(Math.round(maxS - i * 25), pad.l - 5, yy + 3);
    }

    // X axis labels (every 30 days)
    ctx.fillStyle = '#6b6b6b';
    ctx.font = '9px sans-serif';
    ctx.textAlign = 'center';
    for (var i = 0; i < n; i += 30) {
      ctx.save();
      ctx.translate(x(i), H - pad.b + 10);
      ctx.rotate(-0.4);
      ctx.fillText(dates[i], 0, 0);
      ctx.restore();
    }

    // Reference lines: 70 (undervalued), 40 (overvalued)
    ctx.setLineDash([4, 3]);
    ctx.strokeStyle = '#2d7d46';
    ctx.lineWidth = 1;
    ctx.beginPath(); ctx.moveTo(pad.l, yScore(70)); ctx.lineTo(W - pad.r, yScore(70)); ctx.stroke();
    ctx.fillStyle = '#2d7d46';
    ctx.font = '10px sans-serif';
    ctx.textAlign = 'left';
    ctx.fillText('\u4f4e\u4f30\u533a\u95f4', W - pad.r + 5, yScore(70) + 3);

    ctx.strokeStyle = '#b22222';
    ctx.beginPath(); ctx.moveTo(pad.l, yScore(40)); ctx.lineTo(W - pad.r, yScore(40)); ctx.stroke();
    ctx.fillStyle = '#b22222';
    ctx.fillText('\u9ad8\u4f30\u533a\u95f4', W - pad.r + 5, yScore(40) + 3);
    ctx.setLineDash([]);

    // Draw close price (orange line, thin)
    ctx.strokeStyle = 'rgba(199,91,42,0.6)';
    ctx.lineWidth = 1;
    ctx.beginPath();
    for (var i = 0; i < n; i++) {
      if (i === 0) ctx.moveTo(x(i), yClose(closes[i]));
      else ctx.lineTo(x(i), yClose(closes[i]));
    }
    ctx.stroke();

    // Draw score area fill
    ctx.beginPath();
    ctx.moveTo(x(0), yScore(scores[0]));
    for (var i = 1; i < n; i++) ctx.lineTo(x(i), yScore(scores[i]));
    ctx.lineTo(x(n - 1), pad.t + ch);
    ctx.lineTo(x(0), pad.t + ch);
    ctx.closePath();
    var grad = ctx.createLinearGradient(0, pad.t, 0, pad.t + ch);
    grad.addColorStop(0, 'rgba(26,75,140,0.25)');
    grad.addColorStop(1, 'rgba(26,75,140,0.02)');
    ctx.fillStyle = grad;
    ctx.fill();

    // Draw score line (main, blue)
    ctx.strokeStyle = '#1a4b8c';
    ctx.lineWidth = 2;
    ctx.beginPath();
    for (var i = 0; i < n; i++) {
      if (i === 0) ctx.moveTo(x(i), yScore(scores[i]));
      else ctx.lineTo(x(i), yScore(scores[i]));
    }
    ctx.stroke();

    // Latest point marker
    ctx.fillStyle = '#1a4b8c';
    ctx.beginPath();
    ctx.arc(x(n - 1), yScore(scores[n - 1]), 4, 0, Math.PI * 2);
    ctx.fill();
    ctx.font = 'bold 11px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText(scores[n - 1].toFixed(1), x(n - 1), yScore(scores[n - 1]) - 8);

    // Axis titles
    ctx.fillStyle = '#1a4b8c';
    ctx.font = 'bold 11px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('\u4f30\u503c\u5206(0-100)', pad.l + cw / 2, pad.t - 5);

    // Legend
    ctx.fillStyle = '#1a4b8c';
    ctx.fillRect(pad.l, H - 15, 12, 3);
    ctx.font = '10px sans-serif';
    ctx.textAlign = 'left';
    ctx.fillText('\u4f30\u503c\u5206', pad.l + 16, H - 10);
    ctx.fillStyle = 'rgba(199,91,42,0.8)';
    ctx.fillRect(pad.l + 70, H - 15, 12, 3);
    ctx.fillText('\u6536\u76d8\u4ef7', pad.l + 86, H - 10);
  })();

  // --- Chart 5: Radar ---
  var chart5 = echarts.init(document.getElementById('chart-radar'), null, { renderer: 'svg' });
  chart5.setOption({
    animation: false,
    tooltip: { appendToBody: true },
    radar: {
      center: ['50%', '55%'],
      radius: '65%',
      indicator: [
        { name: 'SOTP估值', max: 10 },
        { name: '周期调整PE', max: 10 },
        { name: 'EV/EBITDA分位', max: 10 },
        { name: '供给端周期因子', max: 10 },
        { name: '需求端结构因子', max: 10 },
        { name: '利润质量因子', max: 10 },
        { name: '治理与资本配置', max: 10 },
        { name: '宏观政策环境', max: 10 }
      ],
      axisName: { color: muted, fontSize: 10 }
    },
    series: [{
      type: 'radar',
      data: [{
        value: [6.5, 6.0, 7.0, 4.5, 8.0, 7.5, 4.0, 7.0],
        name: '当前评分',
        areaStyle: { color: accent + '33' },
        lineStyle: { color: accent, width: 2 },
        itemStyle: { color: accent },
        symbol: 'circle',
        symbolSize: 6
      }, {
        value: [7.5, 7.0, 7.5, 6.5, 8.5, 8.0, 6.0, 7.5],
        name: '乐观情景（6个月后）',
        areaStyle: { color: accent2 + '11' },
        lineStyle: { color: accent2, width: 2, type: 'dashed' },
        itemStyle: { color: accent2 },
        symbol: 'diamond',
        symbolSize: 6
      }]
    }],
    legend: { bottom: 0, textStyle: { color: ink } }
  });
  window.addEventListener('resize', function() { chart5.resize(); });

})();