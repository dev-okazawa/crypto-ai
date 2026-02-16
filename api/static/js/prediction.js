let ALL_SYMBOLS = [];

/* ===============================
   Render Symbol Options
================================ */
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
}

/* ===============================
   Load Symbols
================================ */
async function loadSymbols() {

  try {

    const res = await fetch("/symbols?interval=1h");
    if (!res.ok) return;

    const data = await res.json();
    if (!Array.isArray(data)) return;

    ALL_SYMBOLS = data;

    renderSymbolOptions(ALL_SYMBOLS);

  } catch (e) {
    console.log("symbols error", e);
  }
}

/* ===============================
   Load Prediction
================================ */
async function loadPrediction() {

  const select = document.getElementById("symbol");
  if (!select) return;

  const symbol = select.value;
  if (!symbol) return;

  try {

    const res = await fetch(
      `/predict?symbol=${symbol}&interval=1h&horizon=1`
    );

    if (!res.ok) return;

    const response = await res.json();
    if (!response.data || !response.data.metrics) return;

    const payload = response.data;
    const m = payload.metrics;

    /* ===== Prices ===== */

    document.getElementById("curPrice").innerHTML =
      formatUSD(m.current);

    document.getElementById("predPrice").innerHTML =
      formatUSD(m.predicted);

    document.getElementById("priceChange").innerHTML =
      formatDiff(m.diff, m.pct_change);

    /* ===== Last Updated ===== */

    const updatedEl = document.getElementById("updatedAt");

    if (updatedEl) {
      updatedEl.innerText =
        m.current_price_at || "—";
    }

    /* ===== Confidence ===== */

    const confidence = Number(payload.confidence || 0);

    const confidenceFill = document.getElementById("confidenceFill");
    const confidenceText = document.getElementById("confidenceText");

    if (confidenceFill)
      confidenceFill.style.width = confidence + "%";

    if (confidenceText)
      confidenceText.innerText = confidence + "%";

    /* ===== Accuracy ===== */

    loadAccuracy(symbol);

    /* ===== Chart ===== */

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
          interval: payload.meta?.interval || "1h",
          mode: "full"
        });
      }
    }

  } catch (e) {
    console.log("predict error", e);
  }
}

/* ===============================
   Accuracy API
================================ */
async function loadAccuracy(symbol) {

  try {

    const res = await fetch(
      `/accuracy?interval=1h&symbol=${symbol}`
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

/* ===============================
   Init
================================ */
document.addEventListener("DOMContentLoaded", async () => {

  await loadSymbols();

  const select = document.getElementById("symbol");
  const btn = document.getElementById("predictBtn");
  const symbolSearch =
    document.getElementById("symbolSearch");

  /* URL symbol */

  const params = new URLSearchParams(window.location.search);
  const urlSymbol = params.get("symbol");

  if (urlSymbol && select) {

    const normalized = urlSymbol.toUpperCase();

    const exists = Array.from(select.options).some(
      opt => opt.value.toUpperCase() === normalized
    );

    if (exists)
      select.value = normalized;
  }

  /* Events */

  if (select)
    select.addEventListener("change", loadPrediction);

  if (btn)
    btn.addEventListener("click", loadPrediction);

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

      renderSymbolOptions(filtered);
    });
  }

  /* 初回ロード */
  loadPrediction();
});