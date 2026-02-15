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
    return sign + "USD " + abs.toFixed(4);
  }

  const str = abs.toFixed(12);
  const match = str.match(/^0\.0+/);

  if (!match) {
    return sign + "USD " + abs.toFixed(6);
  }

  const zeroCount = match[0].length - 2;

  const significant = str
    .slice(match[0].length)
    .replace(/0+$/, "")
    .slice(0, 4);

  return `${sign}USD 0.0<sub class="zero-count">${zeroCount}</sub>${significant}`;
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

// =========================
// State
// =========================

let ALL_SYMBOLS = [];
let CURRENT_SYMBOL = null;

// =========================
// Render Symbol Options
// =========================

function renderSymbolOptions(list) {
  const select = document.getElementById("symbol");
  if (!select) return;

  select.innerHTML = "";

  list.forEach(c => {
    if (!c || !c.symbol || !c.name) return;

    const opt = document.createElement("option");
    opt.value = c.symbol;

    const base = c.symbol.replace("USDT", "");
    opt.textContent = `${c.name} ${base} / USDT`;

    select.appendChild(opt);
  });

  if (CURRENT_SYMBOL) {
    select.value = CURRENT_SYMBOL;
  }
}

// =========================
// Load Symbols
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
// Load Prediction
// =========================

async function loadPrediction({ silent = false } = {}) {

  const symbolEl = document.getElementById("symbol");
  const timeframeEl = document.getElementById("timeframe");

  if (!symbolEl || !timeframeEl) return;

  const symbol = symbolEl.value;
  if (!symbol) return;

  CURRENT_SYMBOL = symbol;

  const tf = timeframeEl.value;
  const { interval, horizon } = parseTimeframe(tf);

  try {

    const res = await fetch(
      `/predict?symbol=${symbol}&interval=${interval}&horizon=${horizon}`
    );

    if (!res.ok) throw new Error("Prediction API error");

    const response = await res.json();
    if (!response || !response.data) throw new Error("No data");

    const payload = response.data;
    const metrics = payload.metrics;
    if (!metrics) return;

    const {
      current,
      predicted,
      diff,
      pct_change,
      current_price_at
    } = metrics;

    const priceClass =
      diff > 0 ? "up" :
      diff < 0 ? "down" :
      "flat";

    // =========================
    // ⭐ Symbol Header
    // =========================

    const symbolInfo = ALL_SYMBOLS.find(s => s.symbol === symbol);
    const imageUrl = symbolInfo?.image;
    const base = symbol.replace("USDT", "");

    const header = document.getElementById("symbolHeader");
    const logo = document.getElementById("symbolLogo");
    const title = document.getElementById("symbolTitle");

    if (header && logo && title) {
      title.innerText = `${base} / USDT`;

      if (imageUrl) {
        logo.src = imageUrl;
        header.style.display = "flex";
      } else {
        header.style.display = "none";
      }
    }

    // =========================
    // Update DOM
    // =========================

    document.getElementById("curPrice").innerHTML =
      formatUSD(current);

    document.getElementById("predPrice").innerHTML =
      formatUSD(predicted);

    document.getElementById("priceChange").innerHTML =
      `<span class="${priceClass}">${formatDiff(diff, pct_change)}</span>`;

    document.getElementById("confidenceFill").style.width =
      `${Number(payload.confidence) || 0}%`;

    document.getElementById("confidenceText").innerText =
      `${Number(payload.confidence) || 0}%`;

    document.getElementById("updatedAt").innerText =
      current_price_at || "—";

    if (
      payload.chart &&
      payload.chart.candles &&
      typeof renderPredictionChart === "function"
    ) {
      const container = document.getElementById("snapshotContainer");
      container.innerHTML = renderPredictionChart({
        chart: payload.chart,
        diff: payload.metrics.diff,
        interval: payload.meta?.interval || "1h",
        mode: "full"
      });
    }

    loadAccuracy(symbol, interval);

  } catch (e) {
    console.error("Prediction error:", e);
  }
}

// =========================
// Accuracy + MAE
// =========================

async function loadAccuracy(symbol, interval) {
  try {
    const res = await fetch(
      `/accuracy?interval=${interval}&symbol=${symbol}`
    );
    if (!res.ok) return;

    const data = await res.json();

    const fill = document.getElementById("accuracyFill");
    const text = document.getElementById("accuracyText");
    const maeText = document.getElementById("maeText");

    if (!data || data.accuracy === null) {
      if (fill) fill.style.width = "0%";
      if (text) text.textContent = "Evaluating...";
      if (maeText) maeText.textContent = "--%";
      return;
    }

    if (fill) fill.style.width = `${data.accuracy}%`;
    if (text) text.textContent = `${data.accuracy}%`;

    if (maeText && data.mae !== null) {
      maeText.textContent = `${Number(data.mae).toFixed(2)}%`;
    } else if (maeText) {
      maeText.textContent = "--%";
    }

  } catch (e) {
    console.error("Accuracy error:", e);
  }
}

// =========================
// Init
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

  if (symbolSearch) {
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

      if (filtered.length === 0) {
        renderSymbolOptions([]);
        return;
       }

      CURRENT_SYMBOL = filtered[0].symbol;

    renderSymbolOptions(filtered);
  });
}

  await loadSymbols({ keepSymbol: false });

  setTimeout(() => loadPrediction({ silent: true }), 300);

  setInterval(() => {
    if (document.visibilityState === "visible") {
      loadPrediction({ silent: true });
    }
  }, 60000);

});