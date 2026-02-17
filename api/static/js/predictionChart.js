/**
 * static/js/predictionChart.js
 * - 上下余白の調整を維持 (margin: 30px 0 -120px 0)
 * - Y軸 3点表示 / 18px Bold / Nowラベル
 * - mode ("full" | "mini") による高さの自動分岐
 */

// ===============================
// Normalize
// ===============================
function normalizePrices(data, chartWidth, chartHeight, min, max, minTime, maxTime) {
  return data.map(point => {
    const x = ((point.time - minTime) / (maxTime - minTime || 1)) * chartWidth;
    const y = chartHeight - ((point.price - min) / (max - min || 1)) * chartHeight;
    return { x, y };
  });
}

// ===============================
// Time Formatter
// ===============================
function formatTime(ts, interval) {
  const d = new Date(ts);
  if (interval === "1d" || interval === "1w") {
    return `${d.getUTCMonth() + 1}/${d.getUTCDate()}`;
  }
  return `${String(d.getUTCHours()).padStart(2, "0")}:00`;
}

// ===============================
// Y軸ラベル（18px / 3点表示）
// ===============================
function buildYLabel(value, yPos, margin, isMini) {
  const abs = Math.abs(value);
  const fontSize = isMini ? 14 : 18;
  const xPos = margin.left - 10;
  const textAttr = `x="${xPos}" y="${yPos}" text-anchor="end" font-size="${fontSize}" fill="#cbd5e1" font-weight="bold"`;

  if (abs >= 1) {
    return `<text ${textAttr}>${value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</text>`;
  }
  if (abs >= 0.01) {
    return `<text ${textAttr}>${value.toFixed(4)}</text>`;
  }

  const str = abs.toFixed(14);
  const match = str.match(/^0\.0+/);
  if (!match) {
    return `<text ${textAttr}>${value.toFixed(6)}</text>`;
  }

  const zeroCount = match[0].length - 2;
  let significant = str.slice(match[0].length).replace(/0+$/, "").slice(0, 4);

  return `
    <text ${textAttr}>
      0.0<tspan baseline-shift="sub" font-size="${fontSize - 4}">${zeroCount}</tspan>${significant}
    </text>
  `;
}

// ===============================
// Main Renderer
// ===============================
function renderPredictionChart({ chart, diff, interval = "1h", mode = "full" }) {
  if (!chart || !chart.candles || chart.candles.length === 0) {
    return '<p style="text-align:center; opacity:0.5; padding: 10px;">No data available</p>';
  }

  const isMini = mode === "mini";
  const width = isMini ? 400 : 800;
  const height = isMini ? 140 : 300; 

  const margin = isMini
    ? { top: 5, right: 25, bottom: 25, left: 95 }
    : { top: 8, right: 35, bottom: 28, left: 125 };

  const chartWidth = width - margin.left - margin.right;
  const chartHeight = height - margin.top - margin.bottom;

  const pastData = chart.candles.map(c => ({ time: c.time, price: c.close }));
  let futureData = [];

  if (chart.prediction?.future?.length) {
    const firstFuture = chart.prediction.future[0];
    const lastCandle = chart.candles[chart.candles.length - 1];
    const intervalMap = { "1h": 3600000, "1d": 86400000, "1w": 604800000 };
    const intervalMs = intervalMap[interval] || 3600000;

    futureData.push({ time: firstFuture.time, price: firstFuture.value });
    const slope = firstFuture.value - lastCandle.close;
    futureData.push({ time: firstFuture.time + intervalMs, price: firstFuture.value + slope });
  }

  // --- 修正箇所：allDataを定義し、padding計算を行う ---
  const allData = pastData.concat(futureData);
  const rawMin = Math.min(...allData.map(d => d.price));
  const rawMax = Math.max(...allData.map(d => d.price));
  const range = rawMax - rawMin || 1;
  const padding = range * 0.15; // 上下に15%ずつの余白

  const min = rawMin - padding;
  const max = rawMax + padding;
  const mid = (min + max) / 2;
  
  const minTime = Math.min(...allData.map(d => d.time));
  const maxTime = Math.max(...allData.map(d => d.time));
  // --------------------------------------------------

  const normalized = normalizePrices(allData, chartWidth, chartHeight, min, max, minTime, maxTime);
  const points = normalized.map(p => `${p.x + margin.left},${p.y + margin.top}`);
  
  const split = pastData.length - 1;
  const pastLine = points.slice(0, split + 1).join(" ");
  const futureLine = points.slice(split).join(" ");

  const areaPath = `${pastLine} L ${normalized[split].x + margin.left},${chartHeight + margin.top} L ${margin.left},${chartHeight + margin.top} Z`;

  const lastPoint = normalized[split];
  const lastX = lastPoint.x + margin.left;
  const lastY = lastPoint.y + margin.top;
  const color = diff > 0 ? "#22c55e" : diff < 0 ? "#ef4444" : "#94a3b8";

  const candleTimes = pastData.map(d => d.time);
  const labelFontSize = isMini ? 14 : 18;
  const stepIndex = Math.max(1, Math.floor(candleTimes.length / (isMini ? 3 : 5)));
  
  let gridElements = "";
  for (let i = 0; i < candleTimes.length - 1; i += stepIndex) {
    const t = candleTimes[i];
    const x = margin.left + ((t - minTime) / (maxTime - minTime || 1)) * chartWidth;
    gridElements += `
      <line x1="${x}" y1="${margin.top}" x2="${x}" y2="${margin.top + chartHeight}" stroke="rgba(255,255,255,0.05)" />
      <text x="${x}" y="${margin.top + chartHeight + 35}" text-anchor="${i===0?'start':'middle'}" font-size="${labelFontSize}" fill="#64748b" font-weight="bold">
        ${formatTime(t, interval)}
      </text>
    `;
  }

  const lastUpdateTimeStr = formatTime(candleTimes[split], interval);
  gridElements += `
    <text x="${lastX}" y="${margin.top + chartHeight + 35}" text-anchor="middle" font-size="${labelFontSize}" fill="#cbd5e1" font-weight="bold">
      Now (${lastUpdateTimeStr})
    </text>
  `;

  return `
    <div style="margin: 30px 0 -120px 0; padding: 0; overflow: visible;">
      <svg viewBox="0 0 ${width} ${height}" 
           width="100%" 
           height="${height}" 
           preserveAspectRatio="xMidYMin meet"
           style="display: block; background: transparent; overflow: visible;">
        <defs>
          <linearGradient id="areaGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="#6366f1" stop-opacity="0.2" />
            <stop offset="100%" stop-color="#6366f1" stop-opacity="0" />
          </linearGradient>
        </defs>

        <line x1="${margin.left}" y1="${margin.top}" x2="${margin.left + chartWidth}" y2="${margin.top}" stroke="rgba(255,255,255,0.1)" />
        <line x1="${margin.left}" y1="${margin.top + chartHeight/2}" x2="${margin.left + chartWidth}" y2="${margin.top + chartHeight/2}" stroke="rgba(255,255,255,0.05)" stroke-dasharray="4 4" />
        <line x1="${margin.left}" y1="${margin.top + chartHeight}" x2="${margin.left + chartWidth}" y2="${margin.top + chartHeight}" stroke="rgba(255,255,255,0.2)" />
        
        ${gridElements}
        
        ${buildYLabel(max, margin.top + 6, margin, isMini)}
        ${buildYLabel(mid, margin.top + chartHeight/2 + 6, margin, isMini)}
        ${buildYLabel(min, margin.top + chartHeight + 6, margin, isMini)}

        <path d="${areaPath}" fill="url(#areaGradient)" />
        
        <polyline points="${pastLine}" fill="none" stroke="#cbd5e1" stroke-width="2.5" stroke-linecap="round" />
        
        <line x1="${lastX}" y1="${margin.top}" x2="${lastX}" y2="${margin.top + chartHeight}" stroke="${color}" stroke-dasharray="3 3" opacity="0.4" />
        <polyline points="${futureLine}" fill="none" stroke="${color}" stroke-width="4" stroke-dasharray="8 5" stroke-linecap="round" />

        <circle cx="${lastX}" cy="${lastY}" r="6" fill="#020617" stroke="${color}" stroke-width="2.5"/>
        <circle cx="${lastX}" cy="${lastY}" r="2.5" fill="${color}" />
      </svg>
    </div>
  `;
}

window.renderPredictionChart = renderPredictionChart;