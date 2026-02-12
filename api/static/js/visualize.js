// =====================
// Market Overview UI
// =====================
const container = document.getElementById("swipeContainer");
const lastUpdatedEl = document.getElementById("lastUpdated");

// =====================
// Utils
// =====================
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
// Render Card
// =====================
function renderCard(item) {

  if (!item || !item.data) {
    return document.createElement("div");
  }

  const payload = item.data;

  if (
    !payload.metrics ||
    !payload.chart ||
    !payload.chart.candles
  ) {
    return document.createElement("div");
  }

  const { current, predicted, diff } = payload.metrics;

  const pct = (diff / current) * 100;

  const trend =
    diff > 0 ? "UP" :
    diff < 0 ? "DOWN" :
    "FLAT";

  const colorClass =
    diff > 0 ? "up" :
    diff < 0 ? "down" :
    "flat";

  const isPick = item.rank <= 3;

  const card = document.createElement("div");
  card.className = "market-card";

  card.innerHTML = `
    <div class="card-header">
      <div class="left">
        <span class="rank">#${item.rank} ${payload.symbol}</span>
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
      ${diff > 0 ? "+" : ""}${pct.toFixed(2)}%
    </div>

    <div class="mini-chart">
      ${renderPredictionChart({
        chart: payload.chart,
        diff,
        interval: payload.meta?.interval || "1h",
        mode: "mini"
      })}
    </div>

    <div class="confidence-row">
      <span>Confidence</span>
      <div class="confidence-bar">
        <div
          class="confidence-fill"
          style="width:${payload.confidence}%"
        ></div>
      </div>
      <span>${payload.confidence}%</span>
    </div>
  `;

  return card;
}

// =====================
// Load Market Overview
// =====================
async function loadMarket() {
  if (!container) return;

  container.innerHTML =
    "<p style='padding:16px;opacity:.6'>Loading market data...</p>";

  try {
    const res = await fetch("/api/market-overview");
    const data = await res.json();

    container.innerHTML = "";

    // ✅ 正しい generated_at 参照
    if (lastUpdatedEl && data.meta && data.meta.generated_at) {
      const formatted = formatUTC(data.meta.generated_at);
      if (formatted) {
        lastUpdatedEl.innerText =
          "Last Updated (UTC) " + formatted;
      }
    }

    if (Array.isArray(data.items)) {
      for (const item of data.items) {
        const card = renderCard(item);
        container.appendChild(card);
      }
    }

  } catch (e) {
    console.error(e);
    container.innerHTML =
      "<p style='padding:16px;color:#ef4444'>Failed to load market data.</p>";
  }
}

// =====================
// Init
// =====================
window.addEventListener("DOMContentLoaded", loadMarket);
