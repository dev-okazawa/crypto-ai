document.addEventListener("DOMContentLoaded", function () {

  // 🔥 JSONスクリプトタグから安全に取得
  const dataScript = document.getElementById("coin-data");

  if (!dataScript) {
    console.error("coin-data script tag not found");
    return;
  }

  let coins;

  try {
    coins = JSON.parse(dataScript.textContent);
  } catch (e) {
    console.error("Failed to parse coin data:", e);
    return;
  }

  if (!Array.isArray(coins)) {
    console.error("coin data is not array");
    return;
  }

  window._miniCharts = window._miniCharts || {};

  coins.forEach(function (coin) {

    const canvasId = "chart-" + coin.symbol;
    const canvas = document.getElementById(canvasId);

    if (!canvas) return;

    if (!coin.trend || coin.trend.length === 0) return;

    // 既存チャート破棄
    if (window._miniCharts[canvasId]) {
      window._miniCharts[canvasId].destroy();
    }

    const isUp = coin.change >= 0;
    const color = isUp ? "#22c55e" : "#ef4444";

    const ctx = canvas.getContext("2d");

    window._miniCharts[canvasId] = new Chart(ctx, {
      type: "line",
      data: {
        labels: coin.trend.map((_, i) => i),
        datasets: [{
          data: coin.trend,
          borderColor: color,
          borderWidth: 2,
          pointRadius: 0,
          tension: 0.4,
          fill: false
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: false,
        plugins: {
          legend: { display: false },
          tooltip: { enabled: false }
        },
        scales: {
          x: { display: false },
          y: { display: false }
        }
      }
    });

  });

});
