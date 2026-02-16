// =====================
// Market Overview UI
// =====================

const container = document.getElementById("swipeContainer");
const lastUpdatedEl = document.getElementById("lastUpdated");

let CURRENT_INTERVAL = "1h";
let ALL_ITEMS = [];
let CURRENT_MODE = "gainers";


// =====================
// Utils
// =====================

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

function formatPair(symbol) {
  if (!symbol) return "";

  if (symbol.endsWith("USDT")) {
    const base = symbol.replace("USDT", "");
    return `${base} / USDT`;
  }

  return symbol;
}


// =====================
// Sorting
// =====================

function sortItems(items) {
  return [...items]
    .filter(item => item?.data?.metrics)
    .sort((a, b) => {

      const pctA = a.data.metrics.pct_change ?? 0;
      const pctB = b.data.metrics.pct_change ?? 0;

      return CURRENT_MODE === "gainers"
        ? pctB - pctA
        : pctA - pctB;
    });
}


// =====================
// Render Card
// =====================

function renderCard(item, index) {

  if (!item?.data?.metrics) {
    return document.createElement("div");
  }

  const payload = item.data;
  const metrics = payload.metrics;

  const current = metrics.current ?? 0;
  const predicted = metrics.predicted ?? 0;
  const diff = metrics.diff ?? 0;
  const pct_change = metrics.pct_change ?? 0;

  const trend =
    diff > 0 ? "UP" :
    diff < 0 ? "DOWN" :
    "FLAT";

  const colorClass =
    diff > 0 ? "up" :
    diff < 0 ? "down" :
    "flat";

  const isPick = index < 10 && CURRENT_MODE === "gainers";

  const card = document.createElement("a");
  card.href = `/prediction?symbol=${payload.symbol}`;
  card.className = "market-card market-link";

  card.innerHTML = `
    <div class="card-header">
      <div class="left" style="display:flex;align-items:center;gap:6px;flex-wrap:wrap;">

        <span class="rank">
          #${item.rank ?? index + 1}
        </span>

        ${item.image ? `
          <img 
            src="${item.image}" 
            alt="${payload.symbol}" 
            class="coin-logo"
            onerror="this.style.display='none'"
          />
        ` : ""}

        <span class="pair">
          ${formatPair(payload.symbol)}
        </span>

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
      ${formatDiff(diff, pct_change)}
    </div>

    <div class="mini-chart">
      ${
        payload.chart
          ? renderPredictionChart({
              chart: payload.chart,
              diff,
              interval: payload.meta?.interval || CURRENT_INTERVAL,
              mode: "mini"
            })
          : ""
      }
    </div>

    <div class="confidence-row">
      <span>Confidence</span>
      <div class="confidence-bar">
        <div
          class="confidence-fill"
          style="width:${payload.confidence ?? 0}%"
        ></div>
      </div>
      <span>${(payload.confidence ?? 0).toFixed(2)}%</span>
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

    if (!res.ok) {
      throw new Error("API error");
    }

    const data = await res.json();

    if (!data?.items) {
      throw new Error("Invalid response");
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

  if (!ALL_ITEMS.length) return;

  const input = document.getElementById("moSearch");
  if (!input) return;

  const keyword = input.value.trim().toUpperCase();

  if (!keyword) {
    renderList(ALL_ITEMS);
    return;
  }

  const filtered = ALL_ITEMS.filter(item => {
    const raw = item.data?.symbol?.toUpperCase() ?? "";
    const formatted = formatPair(item.data?.symbol ?? "").toUpperCase();
    return raw.includes(keyword) || formatted.includes(keyword);
  });

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

  renderList(ALL_ITEMS);
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

  setMode("gainers");
  loadMarket();
});