// ===============================
// State
// ===============================

let ALL_SYMBOLS = [];
let CURRENT_SYMBOL = null;


// ===============================
// Render Symbol Options
// ===============================

function renderSymbolOptions(list) {

  const select = document.getElementById("symbol");
  if (!select) return;

  select.innerHTML = "";

  list.forEach(c => {

    if (!c || !c.symbol || !c.name) return;

    const opt = document.createElement("option");
    opt.value = c.symbol;

    const base = c.symbol.replace("USDT", "");
    opt.textContent = `${c.name} ${base}`;

    select.appendChild(opt);
  });

  if (CURRENT_SYMBOL) {
    select.value = CURRENT_SYMBOL;
  }
}


// ===============================
// Load Symbols（🔥 interval対応）
// ===============================

async function loadSymbols({ keepSymbol = true } = {}) {

  try {

    const timeframeEl = document.getElementById("timeframe");
    const interval = timeframeEl ? timeframeEl.value : "1h";

    const prevSymbol = keepSymbol ? CURRENT_SYMBOL : null;

    const res = await fetch(`/symbols?interval=${interval}`);
    if (!res.ok) return;

    const data = await res.json();
    if (!Array.isArray(data)) return;

    ALL_SYMBOLS = data;

    if (prevSymbol && data.some(s => s.symbol === prevSymbol)) {
      CURRENT_SYMBOL = prevSymbol;
    } else {
      CURRENT_SYMBOL = data[0]?.symbol || null;
    }

    renderSymbolOptions(ALL_SYMBOLS);

  } catch (e) {
    console.log("symbols error", e);
  }
}


// ===============================
// Load Prediction（🔥 interval対応）
// ===============================

async function loadPrediction() {

  const select = document.getElementById("symbol");
  const timeframeEl = document.getElementById("timeframe");

  if (!select) return;

  const symbol = select.value;
  if (!symbol) return;

  CURRENT_SYMBOL = symbol;

  const interval = timeframeEl ? timeframeEl.value : "1h";

  try {

    const res = await fetch(
      `/predict?symbol=${symbol}&interval=${interval}&horizon=1`
    );

    if (!res.ok) return;

    const response = await res.json();
    if (!response.data || !response.data.metrics) return;

    const payload = response.data;
    const m = payload.metrics;

    // ===============================
    // 🔥 Symbol Header
    // ===============================

    const header = document.getElementById("symbolHeader");
    const logo = document.getElementById("symbolLogo");
    const title = document.getElementById("symbolTitle");

    const symbolInfo = ALL_SYMBOLS.find(s => s.symbol === symbol);

    if (header && logo && title) {

      const base = symbol.replace("USDT", "");
      title.innerText = `${base} / USDT`;

      if (symbolInfo && symbolInfo.image) {
        logo.src = symbolInfo.image;
        header.style.display = "flex";
      } else {
        header.style.display = "none";
      }
    }

    // ===============================
    // Prices
    // ===============================

    document.getElementById("curPrice").innerHTML =
      formatUSD(m.current);

    document.getElementById("predPrice").innerHTML =
      formatUSD(m.predicted);

    document.getElementById("priceChange").innerHTML =
      formatDiff(m.diff, m.pct_change);

    // ===============================
    // Last Updated
    // ===============================

    const updatedEl = document.getElementById("updatedAt");
    if (updatedEl) {
      updatedEl.innerText = m.current_price_at || "—";
    }

    // ===============================
    // Confidence
    // ===============================

    const confidence = Number(payload.confidence || 0);

    const confidenceFill = document.getElementById("confidenceFill");
    const confidenceText = document.getElementById("confidenceText");

    if (confidenceFill)
      confidenceFill.style.width = confidence + "%";

    if (confidenceText)
      confidenceText.innerText = confidence + "%";

    // ===============================
    // Accuracy（🔥 interval対応）
    // ===============================

    loadAccuracy(symbol, interval);

    // ===============================
    // Chart
    // ===============================

    if (
      payload.chart &&
      payload.chart.candles &&
      typeof renderPredictionChart === "function"
    ) {

      const container =
        document.getElementById("snapshotContainer");

      if (container) {

        container.innerHTML = renderPredictionChart({
          chart: payload.chart,
          diff: m.diff,
          interval: payload.meta?.interval || interval,
          mode: "full"
        });
      }
    }

  } catch (e) {
    console.log("predict error", e);
  }
}


// ===============================
// Accuracy API（🔥 interval対応）
// ===============================

async function loadAccuracy(symbol, interval) {

  try {

    const res = await fetch(
      `/accuracy?interval=${interval}&symbol=${symbol}`
    );

    if (!res.ok) return;

    const data = await res.json();
    if (!data) return;

    const accuracyFill = document.getElementById("accuracyFill");
    const accuracyText = document.getElementById("accuracyText");
    const maeText = document.getElementById("maeText");

    if (data.accuracy == null) {

      if (accuracyFill)
        accuracyFill.style.width = "0%";

      if (accuracyText)
        accuracyText.innerText = "--%";

      if (maeText)
        maeText.innerText = "--%";

      return;
    }

    if (accuracyFill)
      accuracyFill.style.width = data.accuracy + "%";

    if (accuracyText)
      accuracyText.innerText = data.accuracy + "%";

    if (maeText)
      maeText.innerText =
        data.mae != null ? data.mae + "%" : "--%";

  } catch (e) {
    console.log("accuracy error", e);
  }
}


// ===============================
// Init
// ===============================

document.addEventListener("DOMContentLoaded", async () => {

  await loadSymbols({ keepSymbol: false });

  const select = document.getElementById("symbol");
  const btn = document.getElementById("predictBtn");
  const symbolSearch = document.getElementById("symbolSearch");
  const timeframe = document.getElementById("timeframe");

  // ===============================
  // URL ?symbol=
  // ===============================

  const params = new URLSearchParams(window.location.search);
  const urlSymbol = params.get("symbol");

  if (urlSymbol && select) {

    const normalized = urlSymbol.toUpperCase();

    const exists = Array.from(select.options).some(
      opt => opt.value.toUpperCase() === normalized
    );

    if (exists) {
      select.value = normalized;
      CURRENT_SYMBOL = normalized;
    }
  }

  // ===============================
  // Events
  // ===============================

  if (select)
    select.addEventListener("change", loadPrediction);

  if (btn)
    btn.addEventListener("click", loadPrediction);

  if (timeframe)
    timeframe.addEventListener("change", async () => {
      await loadSymbols({ keepSymbol: true });
      loadPrediction();
    });

  if (symbolSearch) {

     symbolSearch.addEventListener("input", function () {

       const keyword =
         this.value.trim().toUpperCase();

       if (!keyword) {
         renderSymbolOptions(ALL_SYMBOLS);
         return;
        }

       const filtered = ALL_SYMBOLS.filter(c =>
         c.symbol.toUpperCase().includes(keyword) ||
         (c.name &&
          c.name.toUpperCase().includes(keyword))
       );

       if (filtered.length === 0) {
         renderSymbolOptions([]);
         return;
       }

       CURRENT_SYMBOL = filtered[0].symbol;   // 🔥 これが必要

       renderSymbolOptions(filtered);
    });
}

  // 初回ロード
  loadPrediction();
});