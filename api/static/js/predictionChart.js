// ===============================
// Normalize
// ===============================
function normalizePrices(data, chartWidth, chartHeight, min, max, minTime, maxTime) {
  return data.map(point => {

    const x =
      ((point.time - minTime) / (maxTime - minTime || 1)) *
      chartWidth;

    const y =
      chartHeight -
      ((point.price - min) / (max - min || 1)) *
      chartHeight;

    return { x, y };
  });
}


// ===============================
function formatTime(ts, interval) {

  const d = new Date(ts);

  if (interval === "1d" || interval === "1w") {
    return `${d.getUTCMonth() + 1}/${d.getUTCDate()}`;
  }

  return `${String(d.getUTCHours()).padStart(2, "0")}:00`;
}


// ===============================
// Y軸ラベル（SVG専用 sub対応）
// ===============================
function buildYLabel(value, yPos, margin, isMini) {

  const abs = Math.abs(value);

  // 1以上
  if (abs >= 1) {
    return `
      <text x="${margin.left - 10}" 
            y="${yPos}"
            text-anchor="end"
            font-size="${isMini ? 10 : 14}"
            fill="#ffffff">
        ${value.toLocaleString(undefined, {
          minimumFractionDigits: 2,
          maximumFractionDigits: 2
        })}
      </text>
    `;
  }

  // 0.01以上
  if (abs >= 0.01) {
    return `
      <text x="${margin.left - 10}" 
            y="${yPos}"
            text-anchor="end"
            font-size="${isMini ? 10 : 14}"
            fill="#ffffff">
        ${value.toFixed(4)}
      </text>
    `;
  }

  // 超小数
  const str = abs.toFixed(12);
  const match = str.match(/^0\.0+/);

  if (!match) {
    return `
      <text x="${margin.left - 10}" 
            y="${yPos}"
            text-anchor="end"
            font-size="${isMini ? 10 : 14}"
            fill="#ffffff">
        ${value.toFixed(6)}
      </text>
    `;
  }

  const zeroCount = match[0].length - 2;

  let significant = str.slice(match[0].length);
  significant = significant.replace(/0+$/, "").slice(0, 4);

  return `
    <text x="${margin.left - 10}" 
          y="${yPos}"
          text-anchor="end"
          font-size="${isMini ? 10 : 14}"
          fill="#ffffff">
      0.0
      <tspan baseline-shift="sub"
             font-size="${isMini ? 8 : 10}">
        ${zeroCount}
      </tspan>
      ${significant}
    </text>
  `;
}


// ===============================
function renderPredictionChart({ chart, diff, interval = "1h", mode = "full" }) {

  if (!chart || !chart.candles || chart.candles.length === 0) {
    return "";
  }

  const isMini = mode === "mini";

  const width = isMini ? 380 : 720;
  const height = isMini ? 150 : 300;

  const margin = isMini
    ? { top: 5, right: 20, bottom: 25, left: 55 }
    : { top: 10, right: 30, bottom: 35, left: 75 };

  const chartWidth = width - margin.left - margin.right;
  const chartHeight = height - margin.top - margin.bottom;

  const pastData = chart.candles.map(c => ({
    time: c.time,
    price: c.close
  }));

  let futureData = [];

  if (chart.prediction?.future?.length) {

    const firstFuture = chart.prediction.future[0];
    const lastCandle = chart.candles[chart.candles.length - 1];

    const intervalMap = {
      "1h": 60 * 60 * 1000,
      "1d": 24 * 60 * 60 * 1000,
      "1w": 7 * 24 * 60 * 60 * 1000
    };

    const intervalMs = intervalMap[interval] || 3600000;

    futureData.push({
      time: firstFuture.time,
      price: firstFuture.value
    });

    const slope = firstFuture.value - lastCandle.close;

    futureData.push({
      time: firstFuture.time + intervalMs,
      price: firstFuture.value + slope
    });
  }

  const allData = pastData.concat(futureData);

  const min = Math.min(...allData.map(d => d.price));
  const max = Math.max(...allData.map(d => d.price));
  const mid = (min + max) / 2;

  const minTime = Math.min(...allData.map(d => d.time));
  const maxTime = Math.max(...allData.map(d => d.time));

  const normalized = normalizePrices(
    allData,
    chartWidth,
    chartHeight,
    min,
    max,
    minTime,
    maxTime
  );

  const points = normalized.map(p =>
    `${p.x + margin.left},${p.y + margin.top}`
  );

  const split = pastData.length - 1;
  const pastLine = points.slice(0, split + 1).join(" ");
  const futureLine = points.slice(split).join(" ");

  const lastPoint = normalized[split];
  const lastX = lastPoint.x + margin.left;
  const lastY = lastPoint.y + margin.top;

  const color =
    diff > 0 ? "#22c55e" :
    diff < 0 ? "#ef4444" :
    "#9ca3af";

  // ===============================
  // X軸
  // ===============================
  const candleTimes = pastData.map(d => d.time);

  const approxLabelWidth = isMini ? 55 : 90;
  const maxLabels = Math.max(2, Math.floor(chartWidth / approxLabelWidth));
  const stepIndex = Math.max(1, Math.floor(candleTimes.length / maxLabels));

  let xTicks = [];

  xTicks.push(candleTimes[0]);

  for (let i = stepIndex; i < candleTimes.length - 1; i += stepIndex) {
    xTicks.push(candleTimes[i]);
  }

  xTicks.push(candleTimes[candleTimes.length - 1]);
  xTicks = [...new Set(xTicks)];

  const xLabels = xTicks.map((t, index) => {

    const x =
      margin.left +
      ((t - minTime) / (maxTime - minTime || 1)) *
      chartWidth;

    const isFirst = index === 0;
    const isLast = index === xTicks.length - 1;

    return `
      <text x="${x}"
            y="${margin.top + chartHeight + 22}"
            text-anchor="${isFirst ? "start" : isLast ? "end" : "middle"}"
            font-size="${isMini ? 10 : 14}"
            fill="#94a3b8">
        ${formatTime(t, interval)}
      </text>
    `;
  }).join("");

  // ===============================
  // Y軸
  // ===============================
  const yMin = margin.top + chartHeight;
  const yMid = margin.top + chartHeight / 2;
  const yMax = margin.top;

  const yLabels = `
    <line x1="${margin.left}" y1="${yMax}"
          x2="${margin.left + chartWidth}" y2="${yMax}"
          stroke="#1f2937"/>

    <line x1="${margin.left}" y1="${yMid}"
          x2="${margin.left + chartWidth}" y2="${yMid}"
          stroke="#1f2937"/>

    <line x1="${margin.left}" y1="${yMin}"
          x2="${margin.left + chartWidth}" y2="${yMin}"
          stroke="#1f2937"/>

    ${buildYLabel(max, yMax + 5, margin, isMini)}
    ${buildYLabel(mid, yMid + 5, margin, isMini)}
    ${buildYLabel(min, yMin + 5, margin, isMini)}
  `;

  return `
    <svg viewBox="0 0 ${width} ${height}" width="100%" height="${height}">
      ${yLabels}
      ${xLabels}

      <polyline points="${pastLine}"
        fill="none"
        stroke="#cbd5e1"
        stroke-width="${isMini ? 2 : 3}" />

      <circle cx="${lastX}" cy="${lastY}"
        r="${isMini ? 3 : 5}"
        fill="#60a5fa"
        stroke="#ffffff"
        stroke-width="2"/>

      <polyline points="${futureLine}"
        fill="none"
        stroke="${color}"
        stroke-width="${isMini ? 2 : 3}"
        stroke-dasharray="8 6"
        opacity="0.9" />
    </svg>
  `;
}

window.renderPredictionChart = renderPredictionChart;