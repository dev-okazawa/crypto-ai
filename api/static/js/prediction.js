// ===============================
// Utils
// ===============================

function parseTimeframe(tf) {
  if (tf === "1h") return { interval: "1h", horizon: 1 };
  if (tf === "1d") return { interval: "1d", horizon: 1 };
  if (tf === "1w") return { interval: "1w", horizon: 1 };
  return { interval: "1h", horizon: 1 };
}

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
    opt.textContent = `${c.name} ${base}/USDT`;

    select.appendChild(opt);
  });

  if (CURRENT_SYMBOL) {
    select.value = CURRENT_SYMBOL;
  }
}

// ===============================
// Load Symbols（interval対応）
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
// Load Prediction（interval対応）
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

    // Symbol Header
    const header = document.getElementById("symbolHeader");
    const logo = document.getElementById("symbolLogo");
    const title = document.getElementById("symbolTitle");

    const symbolInfo = ALL_SYMBOLS.find(s => s.symbol === symbol);

    if (header && logo && title) {
      const base = symbol.replace("USDT", "");
      title.innerText = `${base}/USDT`;

      if (symbolInfo && symbolInfo.image) {
        logo.src = symbolInfo.image;
        header.style.display = "flex";
      } else {
        header.style.display = "none";
      }
    }

    // Prices
    document.getElementById("curPrice").innerHTML = formatUSD(m.current);
    document.getElementById("predPrice").innerHTML = formatUSD(m.predicted);

    const priceChangeEl = document.getElementById("priceChange");
    if (priceChangeEl) {
      const direction = m.diff > 0 ? "up" : m.diff < 0 ? "down" : "flat";
      priceChangeEl.innerHTML = `<span class="${direction}">${formatDiff(m.diff, m.pct_change)}</span>`;
    }

    // --- 修正：ここでの updatedAt (—) への上書きを停止 ---
    /*
    const updatedEl = document.getElementById("updatedAt");
    if (updatedEl) {
      updatedEl.innerText = m.current_price_at || "—";
    }
    */

    // Confidence
    const confidence = Number(payload.confidence || 0);
    const confidenceFill = document.getElementById("confidenceFill");
    const confidenceText = document.getElementById("confidenceText");
    if (confidenceFill) confidenceFill.style.width = confidence + "%";
    if (confidenceText) confidenceText.innerText = confidence + "%";

    // Accuracy 更新
    loadAccuracy(symbol, interval);

    // Chart
    if (payload.chart && payload.chart.candles && typeof renderPredictionChart === "function") {
      const container = document.getElementById("snapshotContainer");
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
// Accuracy API（Last Updated 対応版）
// ===============================
async function loadAccuracy(symbol, interval) {
  try {
    const res = await fetch(`/accuracy?interval=${interval}&symbol=${symbol}`);
    if (!res.ok) return;

    const data = await res.json();
    console.log("Accuracy Data Received:", data);

    const accuracyFill = document.getElementById("accuracyFill");
    const accuracyText = document.getElementById("accuracyText");
    const maeText = document.getElementById("maeText");
    const totalText = document.getElementById("totalPredictionsText");
    
    // --- 修正：HTML側の ID "lastUpdatedText" を取得 ---
    const lastUpdatedText = document.getElementById("lastUpdatedText"); 

    if (!data || data.accuracy == null) {
      if (accuracyFill) accuracyFill.style.width = "0%";
      if (accuracyText) accuracyText.innerText = "--%";
      return;
    }

    // 1. Accuracy の反映（バーの幅を更新）
    if (accuracyFill) {
      accuracyFill.style.width = data.accuracy + "%";
    }
    if (accuracyText) {
      accuracyText.textContent = Number(data.accuracy).toFixed(2) + "%";
    }

    // 2. Total Predictions の反映
    if (totalText) {
      totalText.textContent = data.total + " Predictions";
    }

    // 3. MAE の反映
    if (maeText) {
      const maeVal = data.mae || 0;
      maeText.textContent = Number(maeVal).toFixed(2) + "%";
    }

    // 4. Last Updated の反映 (UTC表記を整形)
    if (lastUpdatedText && data.generated_at) {
      // "2026-02-18T04:20:00" -> "2026-02-18 04:20"
      lastUpdatedText.textContent = data.generated_at.replace("T", " ").substring(0, 16);
    }

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

  // URL ?symbol= 対応
  const params = new URLSearchParams(window.location.search);
  const urlSymbol = params.get("symbol");

  if (urlSymbol && select) {
    const normalized = urlSymbol.toUpperCase();
    const exists = Array.from(select.options).some(opt => opt.value.toUpperCase() === normalized);
    if (exists) {
      select.value = normalized;
      CURRENT_SYMBOL = normalized;
    }
  }

  // Events
  if (select) select.addEventListener("change", loadPrediction);
  if (btn) btn.addEventListener("click", loadPrediction);
  if (timeframe) {
    timeframe.addEventListener("change", async () => {
      await loadSymbols({ keepSymbol: true });
      loadPrediction();
    });
  }

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

  loadPrediction();
});