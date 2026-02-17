document.addEventListener("DOMContentLoaded", function () {
    const coinDataEl = document.getElementById("coin-data");
    const coinListContainer = document.getElementById("coin-list-container");
    const sortButtons = document.querySelectorAll(".sort-btn");

    if (!coinDataEl || !coinListContainer) return;

    // 事実：サーバーから送られてきた「元の順序」を保存しておく
    let initialCoins = [];
    let coins = [];
    
    try {
        const rawData = JSON.parse(coinDataEl.textContent);
        // 各データに「元のインデックス」を付与して、サーバーのソート順を記憶させる
        initialCoins = rawData.map((c, index) => ({ ...c, server_rank: index }));
        coins = [...initialCoins];
    } catch (e) {
        return;
    }

    function init() {
        if (!coins.length) return;
        
        // 初期表示：サーバーから届いた順（プルダウンと同じ順）
        reorderDOM(coins);
        applyFormatting();
        renderChartsAsync(coins);
    }

    sortButtons.forEach(button => {
        button.addEventListener('click', function() {
            const sortType = this.dataset.sort;
            sortButtons.forEach(btn => btn.classList.remove("active"));
            this.classList.add("active");

            sortCoins(coins, sortType);
            reorderDOM(coins);
        });
    });

    function sortCoins(data, type) {
        data.sort((a, b) => {
            if (type === 'marketcap_desc') {
                // MarketCap ↑ : サーバーが送ってきた順 (0, 1, 2...)
                return a.server_rank - b.server_rank;
            }
            if (type === 'marketcap_asc') {
                // MarketCap ↓ : サーバーが送ってきた順の逆
                return b.server_rank - a.server_rank;
            }
            if (type === 'change_desc') {
                return parseFloat(b.change_percent || 0) - parseFloat(a.change_percent || 0);
            }
            if (type === 'change_asc') {
                return parseFloat(a.change_percent || 0) - parseFloat(b.change_percent || 0);
            }
            return 0;
        });
    }

    function reorderDOM(sortedData) {
        const fragment = document.createDocumentFragment();
        sortedData.forEach(coin => {
            const card = coinListContainer.querySelector(`[data-symbol="${coin.symbol}"]`);
            if (card) fragment.appendChild(card);
        });
        coinListContainer.appendChild(fragment);
    }

    // --- 描画・補助関数 ---
    function applyFormatting() {
        const safeUSD = typeof formatUSD === "function" ? formatUSD : (v) => `$${Number(v).toLocaleString()}`;
        document.querySelectorAll(".price").forEach(el => {
            el.innerHTML = safeUSD(el.dataset.price || 0);
        });
        document.querySelectorAll(".change").forEach(el => {
            const pct = parseFloat(el.dataset.pct || 0);
            const dir = pct > 0 ? "up" : pct < 0 ? "down" : "flat";
            el.innerHTML = `<span class="${dir}">${pct.toFixed(2)}%</span>`;
        });
    }

    async function renderChartsAsync(data) {
        for (const coin of data) {
            await new Promise(r => requestAnimationFrame(() => {
                renderSingleChart(coin);
                r();
            }));
        }
    }

    function renderSingleChart(coin) {
        const canvasId = `chart-${coin.symbol}`;
        const ctx = document.getElementById(canvasId);
        if (!ctx || !coin.trend) return;
        const exist = Chart.getChart(canvasId);
        if (exist) exist.destroy();
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: new Array(coin.trend.length).fill(''),
                datasets: [{
                    data: coin.trend,
                    borderColor: parseFloat(coin.change_percent || 0) >= 0 ? "#0ecb81" : "#f6465d",
                    borderWidth: 2,
                    pointRadius: 0,
                    fill: false,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: { x: { display: false }, y: { display: false } },
                animation: false
            }
        });
    }

    init();
});