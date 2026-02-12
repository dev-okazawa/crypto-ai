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

function formatTime(ts, interval) {
  const d = new Date(ts);

  if (interval === "1w") {
    return `${d.getUTCMonth() + 1}/${d.getUTCDate()}`;
  }

  return `${String(d.getUTCHours()).padStart(2, "0")}:00`;
}

function generateXTicks(minTime, maxTime, chartWidth) {

  const approxLabelWidth = 80;

  const maxLabels = Math.max(
    3,
    Math.floor(chartWidth / approxLabelWidth)
  );

  const ticks = [];
  const totalRange = maxTime - minTime;
  const step = totalRange / (maxLabels - 1);

  for (let i = 0; i < maxLabels; i++) {
    ticks.push(minTime + step * i);
  }

  return ticks;
}

function formatPrice(value) {
  if (value >= 1000) {
    return "$" + value.toLocaleString(undefined, { maximumFractionDigits: 0 });
  }
  if (value >= 1) {
    return "$" + value.toFixed(2);
  }
  return "$" + value.toFixed(6);
}

function renderPredictionChart({ chart, diff, interval = "1h", mode = "full" }) {

  if (!chart || !chart.candles || chart.candles.length === 0) {
    return "";
  }

  const isMini = mode === "mini";

  // 🔥 幅を固定（開発者モードと完全一致）
  const width = isMini
    ? 330
    : 720;

  const height = isMini ? 60 : 200;

  const margin = isMini
    ? { top: 4, right: 4, bottom: 4, left: 4 }
    : { top: 20, right: 20, bottom: 50, left: 90 };

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

  let axes = "";

  if (!isMini) {

    const yMin = margin.top + chartHeight;
    const yMid = margin.top + chartHeight / 2;
    const yMax = margin.top;

    const xTicks = generateXTicks(minTime, maxTime, chartWidth);

    const xLabels = xTicks.map(t => {

      const x =
        margin.left +
        ((t - minTime) / (maxTime - minTime || 1)) *
        chartWidth;

      return `
        <text x="${x}"
              y="${height - 15}"
              text-anchor="middle"
              font-size="16"
              fill="#94a3b8">
          ${formatTime(t, interval)}
        </text>
      `;
    }).join("");

    axes = `
      <line x1="${margin.left}" y1="${yMax}"
            x2="${margin.left + chartWidth}" y2="${yMax}"
            stroke="#1f2937"/>

      <line x1="${margin.left}" y1="${yMid}"
            x2="${margin.left + chartWidth}" y2="${yMid}"
            stroke="#1f2937"/>

      <line x1="${margin.left}" y1="${yMin}"
            x2="${margin.left + chartWidth}" y2="${yMin}"
            stroke="#1f2937"/>

      <text x="${margin.left - 15}" y="${yMax + 6}"
            text-anchor="end"
            font-size="16"
            fill="#fff">
        ${formatPrice(max)}
      </text>

      <text x="${margin.left - 15}" y="${yMid + 6}"
            text-anchor="end"
            font-size="16"
            fill="#cbd5e1">
        ${formatPrice(mid)}
      </text>

      <text x="${margin.left - 15}" y="${yMin + 6}"
            text-anchor="end"
            font-size="16"
            fill="#fff">
        ${formatPrice(min)}
      </text>

      ${xLabels}
    `;
  }

  return `
    <svg viewBox="0 0 ${width} ${height}" width="100%" height="${height}">
      ${axes}

      <polyline points="${pastLine}"
        fill="none"
        stroke="#cbd5e1"
        stroke-width="3" />

      <circle cx="${lastX}" cy="${lastY}"
        r="5"
        fill="#60a5fa"
        stroke="#ffffff"
        stroke-width="2"/>

      <polyline points="${futureLine}"
        fill="none"
        stroke="${color}"
        stroke-width="3"
        stroke-dasharray="8 6"
        opacity="0.9" />
    </svg>
  `;
}

window.renderPredictionChart = renderPredictionChart;
