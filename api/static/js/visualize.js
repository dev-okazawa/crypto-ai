// =====================
// Market Overview UI
// =====================

const container = document.getElementById("swipeContainer");
const lastUpdatedEl = document.getElementById("lastUpdated");

let CURRENT_INTERVAL = "1h";
let ALL_ITEMS = [];
let CURRENT_MODE = "gainers"; // gainers / losers


// =====================
// Utils
// =====================

function formatUSD(price) {
  const n = Number(price);
  if (!Number.isFinite(n)) return "—";

  if (n >= 1) {
    return n.toLocaleString(undefined, {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    });
  }

  if (n >= 0.01) {
    return n.toLocaleString(undefined, {
      minimumFractionDigits: 4,
      maximumFractionDigits: 4
    });
  }

  return n.toLocaleString(undefined, {
    minimumFractionDigits: 6,
    maximumFractionDigits: 6
  });
}

function formatUTC(isoString) {
  if (!isoString) return null;

  const dt = new Date(isoString);
  if (isNaN(dt.getTime())) return null;

  const yyyy = dt.getUTCFullYear();
  const mm = String(dt.getUTCMonth() + 1).padStart(2, "0");
  const dd = String(dt.getUTCDate()).padStart(2, "0");
  const hh = String(dt.getUTCHours()).padStart(2, "0");
  const min = String(dt.getUTCMinutes()).padStart(2, "0");

  return `${yyyy}-${mm}-${dd} ${hh}:${min}`;
}


// =====================
// Sorting
// =====================

function sortItems(items) {
  return [...items].sort((a, b) => {
    const pctA = a.data.metrics.pct_change;
    const pctB = b.data.metrics.pct_change;

    return CURRENT_MODE === "gainers"
      ? pctB - pctA
      : pctA - pctB;
  });
}


// =====================
// Render Card
// =====================

function renderCard(item, index) {

  if (!item || !item.data) return document.createElement("div");

  const payload = item.data;

  if (!payload.metrics || !payload.chart?.candles) {
    return document.createElement("div");
  }

  const { current, predicted, diff, pct_change } = payload.metrics;

  const trend =
    diff > 0 ? "UP" :
    diff < 0 ? "DOWN" :
    "FLAT";

  const colorClass =
    diff > 0 ? "up" :
    diff < 0 ? "down" :
    "flat";

  const isPick = index < 10 && CURRENT_MODE === "gainers";

  const card = document.createElement("div");
  card.className = "market-card";

  card.innerHTML = `
    <div class="card-header">
      <div class="left">
        <span class="rank">#${index + 1} ${payload.symbol}</span>
        ${isPick ? `<span class="ai-pick">🔥 AI PICK</span>` : ""}
      </div>

      <span class="trend ${colorClass}">
        ${trend}
      </span>
    </div>

    <div class="price-row">
      <span class="current">${formatUSD(current)}</span>
      <span class="arrow">→</span>
      <span class="target">${formatUSD(predicted)}</span>
    </div>

    <div class="price-change ${colorClass}">
      ${pct_change > 0 ? "+" : ""}${pct_change.toFixed(2)}%
    </div>

    <div class="mini-chart">
      ${renderPredictionChart({
        chart: payload.chart,
        diff,
        interval: payload.meta?.interval || CURRENT_INTERVAL,
        mode: "mini"
      })}
    </div>

    <div class="confidence-row">
      <span>Confidence</span>
      <div class="confidence-bar">
        <div
          class="confidence-fill"
          style="width:${payload.confidence || 0}%"
        ></div>
      </div>
      <span>${payload.confidence || 0}%</span>
    </div>
  `;

  return card;
}


// =====================
// Render List
// =====================

function renderList(items) {

  if (!container) return;

  container.innerHTML = "";

  if (!items || items.length === 0) {
    container.innerHTML =
      "<p style='padding:16px;opacity:.6'>No data</p>";
    return;
  }

  const sorted = sortItems(items);

  sorted.forEach((item, index) => {
    const card = renderCard(item, index);
    container.appendChild(card);
  });
}


// =====================
// Load Market Overview
// =====================

async function loadMarket() {

  if (!container) return;

  container.innerHTML =
    "<p style='padding:16px;opacity:.6'>Loading market data...</p>";

  try {

    const intervalSelect = document.getElementById("moInterval");
    if (intervalSelect) {
      CURRENT_INTERVAL = intervalSelect.value;
    }

    const res = await fetch(
      `/api/market-overview?interval=${CURRENT_INTERVAL}&limit=200`
    );

    const data = await res.json();

    if (!data.items) {
      container.innerHTML =
        "<p style='padding:16px;color:#ef4444'>No data</p>";
      return;
    }

    ALL_ITEMS = data.items;

    if (lastUpdatedEl && data.meta?.generated_at) {
      const formatted = formatUTC(data.meta.generated_at);
      if (formatted) {
        lastUpdatedEl.innerText =
          "Last Updated (UTC) " + formatted;
      }
    }

    renderList(ALL_ITEMS);

  } catch (e) {
    console.error(e);
    container.innerHTML =
      "<p style='padding:16px;color:#ef4444'>Failed to load market data.</p>";
  }
}


// =====================
// Search
// =====================

function handleSearch() {

  const input = document.getElementById("moSearch");
  if (!input) return;

  const keyword = input.value.trim().toUpperCase();

  if (!keyword) {
    renderList(ALL_ITEMS);
    return;
  }

  const filtered = ALL_ITEMS.filter(item =>
    item.data.symbol.toUpperCase().includes(keyword)
  );

  renderList(filtered);
}


// =====================
// Toggle Buttons
// =====================

function setMode(mode) {
  CURRENT_MODE = mode;

  document.getElementById("btnGainers")?.classList.remove("active");
  document.getElementById("btnLosers")?.classList.remove("active");

  if (mode === "gainers") {
    document.getElementById("btnGainers")?.classList.add("active");
  } else {
    document.getElementById("btnLosers")?.classList.add("active");
  }

  handleSearch(); // 現在の検索状態を維持
}


// =====================
// Init
// =====================

window.addEventListener("DOMContentLoaded", () => {

  const intervalEl = document.getElementById("moInterval");
  const searchEl = document.getElementById("moSearch");
  const btnGainers = document.getElementById("btnGainers");
  const btnLosers = document.getElementById("btnLosers");

  if (intervalEl) {
    intervalEl.addEventListener("change", loadMarket);
  }

  if (searchEl) {
    searchEl.addEventListener("input", handleSearch);
  }

  if (btnGainers) {
    btnGainers.addEventListener("click", () => setMode("gainers"));
  }

  if (btnLosers) {
    btnLosers.addEventListener("click", () => setMode("losers"));
  }

  setMode("gainers"); // 初期は上昇率
  loadMarket();
});
