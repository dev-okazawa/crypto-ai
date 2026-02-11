// =========================
// Utils
// =========================
function formatUSD(price) {
  const n = Number(price);
  if (!Number.isFinite(n)) return "—";

  if (n >= 1) {
    return "USD " + n.toLocaleString(undefined, {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    });
  }
  if (n >= 0.01) {
    return "USD " + n.toLocaleString(undefined, {
      minimumFractionDigits: 4,
      maximumFractionDigits: 4
    });
  }
  return "USD " + n.toLocaleString(undefined, {
    minimumFractionDigits: 6,
    maximumFractionDigits: 6
  });
}

function formatDiff(diff, pct) {
  const sign = diff > 0 ? "+" : diff < 0 ? "-" : "";
  return `${sign}${formatUSD(Math.abs(diff))} (${sign}${pct.toFixed(2)}%)`;
}

// ✅ 正式週足対応
function parseTimeframe(tf) {
  if (tf === "1h") return { interval: "1h", horizon: 1 };
  if (tf === "1d") return { interval: "1d", horizon: 1 };
  if (tf === "1w") return { interval: "1w", horizon: 1 };
  return { interval: "1h", horizon: 1 };
}

function getBiasLabel(trend) {
  if (trend === "UP") return "Bullish Bias";
  if (trend === "DOWN") return "Bearish Bias";
  return "Neutral Bias";
}

// =========================
// State
// =========================
let ALL_SYMBOLS = [];
let CURRENT_SYMBOL = null;

// =========================
// Render symbol options
// =========================
function renderSymbolOptions(list) {
  const select = document.getElementById("symbol");
  select.innerHTML = "";

  list.forEach(c => {
    if (!c || !c.symbol || !c.name) return;

    const opt = document.createElement("option");
    opt.value = c.symbol;
    opt.textContent = `${c.name} (${c.symbol.replace("USDT", "")})`;
    select.appendChild(opt);
  });

  if (
    CURRENT_SYMBOL &&
    [...select.options].some(o => o.value === CURRENT_SYMBOL)
  ) {
    select.value = CURRENT_SYMBOL;
  }
}

// =========================
// Load symbols
// =========================
async function loadSymbols({ keepSymbol = true } = {}) {
  try {
    const tf = document.getElementById("timeframe").value;
    const { interval } = parseTimeframe(tf);
    const prev = keepSymbol ? CURRENT_SYMBOL : null;

    const res = await fetch(`/symbols?interval=${interval}`);
    if (!res.ok) throw new Error("Symbols API error");

    const data = await res.json();
    if (!Array.isArray(data)) return;

    ALL_SYMBOLS = data;
    CURRENT_SYMBOL = prev || (data[0] ? data[0].symbol : null);

    renderSymbolOptions(ALL_SYMBOLS);

  } catch (e) {
    console.error("loadSymbols error:", e);
  }
}

// =========================
// Snapshot Chart（🔥完全timestamp連動）
// =========================
function renderSnapshotFromPrediction(payload) {
  const container = document.getElementById("snapshotContainer");
  if (!container) return;

  if (
    !payload.chart ||
    !payload.chart.candles ||
    payload.chart.candles.length === 0
  ) {
    container.innerHTML = "";
    return;
  }

  container.innerHTML = renderPredictionChart({
    chart: payload.chart,
    diff: payload.metrics.diff,
    interval: payload.meta?.interval || "1h",
    mode: "full"
  });
}

// =========================
// Load Prediction
// =========================
async function loadPrediction({ silent = false } = {}) {

  const resultEl = document.getElementById("result");
  const snapshotContainer = document.getElementById("snapshotContainer");
  const symbol = document.getElementById("symbol").value;
  if (!symbol) return;

  CURRENT_SYMBOL = symbol;

  const tf = document.getElementById("timeframe").value;
  const { interval, horizon } = parseTimeframe(tf);

  if (!silent) resultEl.textContent = "Loading...";

  try {

    const res = await fetch(
      `/predict?symbol=${symbol}&interval=${interval}&horizon=${horizon}`
    );

    if (!res.ok) throw new Error("Prediction API error");

    const response = await res.json();

    if (!response || !response.data) {
      resultEl.textContent = "No data";
      if (snapshotContainer) snapshotContainer.innerHTML = "";
      return;
    }

    const payload = response.data;

    if (
      !payload.metrics ||
      !payload.chart ||
      !payload.chart.candles ||
      payload.chart.candles.length === 0
    ) {
      resultEl.textContent = "No data";
      if (snapshotContainer) snapshotContainer.innerHTML = "";
      return;
    }

    const {
      current,
      predicted,
      diff,
      pct_change,
      current_price_at
    } = payload.metrics;

    if (!Number.isFinite(current) || !Number.isFinite(predicted)) {
      resultEl.textContent = "No data";
      if (snapshotContainer) snapshotContainer.innerHTML = "";
      return;
    }

    const priceClass =
      diff > 0 ? "up" :
      diff < 0 ? "down" :
      "flat";

    resultEl.innerHTML = `
      <div class="result-row">
        <span class="result-label">Model Base Price</span>
        <span>${formatUSD(current)}</span>
      </div>

      <div class="result-row">
        <span class="result-label">Predicted Price</span>
        <span>${formatUSD(predicted)}</span>
      </div>

      <div class="result-row">
        <span class="result-label">Price Change</span>
        <span class="direction ${priceClass}">
          ${formatDiff(diff, pct_change)}
        </span>
      </div>

      <div class="result-row">
        <span class="result-label">AI Market Bias</span>
        <span class="direction ${priceClass}">
          ${getBiasLabel(payload.trend)}
        </span>
      </div>

      <div class="result-row confidence-row">
        <span class="result-label">Confidence</span>
        <div class="confidence-bar">
          <div class="confidence-fill"
               style="width:${Number(payload.confidence) || 0}%"></div>
        </div>
        <span>${Number(payload.confidence) || 0}%</span>
      </div>

      <div class="result-row">
        <span class="result-label">Last Updated (UTC)</span>
        <span>${current_price_at || "—"}</span>
      </div>
    `;

    renderSnapshotFromPrediction(payload);

  } catch (e) {
    console.error("Prediction error:", e);
    resultEl.textContent = "No data";
    if (snapshotContainer) snapshotContainer.innerHTML = "";
  }
}

// =========================
// Events & Init
// =========================
document.getElementById("predictBtn")
  .addEventListener("click", () => loadPrediction());

document.getElementById("symbol")
  .addEventListener("change", () =>
    loadPrediction({ silent: true })
  );

document.getElementById("timeframe")
  .addEventListener("change", async () => {
    await loadSymbols({ keepSymbol: true });
    loadPrediction({ silent: true });
  });

window.addEventListener("DOMContentLoaded", async () => {
  await loadSymbols({ keepSymbol: false });
  setTimeout(() => loadPrediction({ silent: true }), 300);
});

// 1分ごと自動更新
setInterval(() => {
  if (document.visibilityState === "visible") {
    loadPrediction({ silent: true });
  }
}, 60000);

// =========================
// Symbol Search
// =========================
document.getElementById("symbolSearch")
  .addEventListener("input", function () {

    const keyword = this.value.trim().toUpperCase();

    if (!keyword) {
      renderSymbolOptions(ALL_SYMBOLS);
      return;
    }

    const filtered = ALL_SYMBOLS.filter(c =>
      c.symbol.toUpperCase().includes(keyword) ||
      (c.name && c.name.toUpperCase().includes(keyword))
    );

    renderSymbolOptions(filtered);
  });

