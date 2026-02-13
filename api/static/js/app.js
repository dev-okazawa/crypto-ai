// =========================
// Utils
// =========================

function formatUSD(price) {
  const n = Number(price);
  if (!Number.isFinite(n)) return "USD —";

  const abs = Math.abs(n);
  const sign = n < 0 ? "-" : "";

  if (abs >= 1) {
    return sign + "USD " + abs.toLocaleString(undefined, {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    });
  }

  if (abs >= 0.01) {
    return sign + "USD " + abs.toLocaleString(undefined, {
      minimumFractionDigits: 4,
      maximumFractionDigits: 4
    });
  }

  const str = abs.toFixed(18);
  if (!str.includes(".")) return sign + "USD " + str;

  const decimal = str.split(".")[1] || "";
  const zeroMatch = decimal.match(/^0+/);
  const zeroCount = zeroMatch ? zeroMatch[0].length : 0;
  const significant = decimal.slice(zeroCount, zeroCount + 4) || "0000";

  return sign + `USD 0.0<sub class="cg-zero">${zeroCount}</sub>${significant}`;
}

function formatDiff(diff, pct) {
  const sign = diff > 0 ? "+" : diff < 0 ? "-" : "";
  const diffAbs = Math.abs(diff);
  const pctAbs = Math.abs(pct);

  return `${sign}${formatUSD(diffAbs)} (${sign}${pctAbs.toFixed(2)}%)`;
}

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
  if (!select) return;

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
    const timeframeEl = document.getElementById("timeframe");
    if (!timeframeEl) return;

    const tf = timeframeEl.value;
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
// Snapshot Chart
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

  if (typeof renderPredictionChart !== "function") {
    console.warn("renderPredictionChart not found");
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
  const symbolEl = document.getElementById("symbol");
  const timeframeEl = document.getElementById("timeframe");

  if (!resultEl || !symbolEl || !timeframeEl) return;

  const symbol = symbolEl.value;
  if (!symbol) return;

  CURRENT_SYMBOL = symbol;

  const tf = timeframeEl.value;
  const { interval, horizon } = parseTimeframe(tf);

  if (!silent) resultEl.textContent = "Loading...";

  try {

    const res = await fetch(
      `/predict?symbol=${symbol}&interval=${interval}&horizon=${horizon}`
    );

    if (!res.ok) throw new Error("Prediction API error");

    const response = await res.json();
    if (!response || !response.data) throw new Error("No data");

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

         <!-- ⭐ Accuracyここに入れる -->
         <div class="result-row accuracy-row">
           <span class="result-label">Model Accuracy</span>
           <div class="accuracy-bar">
             <div id="accuracyFill" class="accuracy-fill"></div>
           </div>
           <span id="accuracyText">--%</span>
         </div>       

         <div class="result-row">
           <span class="result-label">MAE</span>
           <span id="maeText">--%</span>
         </div>

        <div class="result-row">
           <span class="result-label">Last Updated (UTC)</span>
           <span>${current_price_at || "—"}</span>
        </div>
      `;

    renderSnapshotFromPrediction(payload);

    loadAccuracy(interval);

  } catch (e) {
    console.error("Prediction error:", e);
    resultEl.textContent = "No data";
    if (snapshotContainer) snapshotContainer.innerHTML = "";
  }
}

// =========================
// Accuracy
// =========================

async function loadAccuracy(interval) {

  try {
    const res = await fetch(`/accuracy?interval=${interval}`);
    if (!res.ok) return;

    const data = await res.json();

    const fill = document.getElementById("accuracyFill");
    const text = document.getElementById("accuracyText");
    const maeText = document.getElementById("maeText");

    if (!data || data.accuracy === null) {
      fill.style.width = "0%";
      text.textContent = "Evaluating...";
      if (maeText) maeText.textContent = "--";
      return;
    }

    fill.style.width = `${data.accuracy}%`;
    text.textContent = `${data.accuracy}%`;

    if (maeText && data.mae !== null) {
      maeText.textContent = `${data.mae.toFixed(2)}%`;
    }

  } catch (e) {
    console.error("Accuracy error:", e);
  }
}

// =========================
// Init (安全版)
// =========================
window.addEventListener("DOMContentLoaded", async () => {

  const predictBtn = document.getElementById("predictBtn");
  const symbol = document.getElementById("symbol");
  const timeframe = document.getElementById("timeframe");
  const symbolSearch = document.getElementById("symbolSearch");

  if (predictBtn)
    predictBtn.addEventListener("click", () => loadPrediction());

  if (symbol)
    symbol.addEventListener("change", () =>
      loadPrediction({ silent: true })
    );

  if (timeframe)
    timeframe.addEventListener("change", async () => {
      await loadSymbols({ keepSymbol: true });
      loadPrediction({ silent: true });
    });

  if (symbolSearch)
    symbolSearch.addEventListener("input", function () {
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

  await loadSymbols({ keepSymbol: false });
  setTimeout(() => loadPrediction({ silent: true }), 300);

  // 1分ごと更新
  setInterval(() => {
    if (document.visibilityState === "visible") {
      loadPrediction({ silent: true });
    }
  }, 60000);

});
