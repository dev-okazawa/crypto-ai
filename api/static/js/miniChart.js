/**
 * static/js/miniChart.js
 * - Y軸の数値を正確に反映 (3点表示)
 * - X軸の時間を表示
 * - 右側の余白を最適化してグラフ領域を拡大
 */

(function() {
    // 内部用ヘルパー：時間フォーマット
    const _format = (ts, interval) => {
        const d = new Date(ts);
        if (interval === "1d" || interval === "1w") return `${d.getUTCMonth() + 1}/${d.getUTCDate()}`;
        return `${String(d.getUTCHours()).padStart(2, "0")}:00`;
    };

    // 内部用ヘルパー：Y軸ラベル (正確な数値表示)
    const _buildLabel = (value, yPos, xPos, fontSize) => {
        const abs = Math.abs(value);
        const textAttr = `x="${xPos}" y="${yPos}" text-anchor="end" font-size="${fontSize}" fill="#cbd5e1" font-weight="normal"`;

        if (abs >= 1) return `<text ${textAttr}>${value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</text>`;
        if (abs >= 0.01) return `<text ${textAttr}>${value.toFixed(4)}</text>`;
        
        const str = abs.toFixed(12);
        const match = str.match(/^0\.0+/);
        if (!match) return `<text ${textAttr}>${value.toFixed(6)}</text>`;
        
        const zeroCount = match[0].length - 2;
        let significant = str.slice(match[0].length).replace(/0+$/, "").slice(0, 4);
        return `<text ${textAttr}>0.0<tspan baseline-shift="sub" font-size="${fontSize - 4}">${zeroCount}</tspan>${significant}</text>`;
    };

    window.renderMiniChart = function({ chart, diff, interval = "1h" }) {
        if (!chart || !chart.candles || chart.candles.length === 0) return "";

        const width = 400;
        const height = 180; // 時間軸を表示するために少し高さを出す
        
        // ★ 右余白を 15 に詰め、下を 40 に広げて時間を表示
        const margin = { top: 10, right: 15, bottom: 40, left: 95 };

        const chartWidth = width - margin.left - margin.right;
        const chartHeight = height - margin.top - margin.bottom;

        const pastData = chart.candles.map(c => ({ time: c.time, price: c.close }));
        let futureData = [];
        if (chart.prediction?.future?.length) {
            const firstFuture = chart.prediction.future[0];
            const lastCandle = chart.candles[chart.candles.length - 1];
            futureData.push({ time: firstFuture.time, price: firstFuture.value });
            const intervalMs = (interval === "1d" ? 86400000 : 3600000);
            futureData.push({ time: firstFuture.time + intervalMs, price: firstFuture.value + (firstFuture.value - lastCandle.close) });
        }

        const allData = pastData.concat(futureData);
        const min = Math.min(...allData.map(d => d.price));
        const max = Math.max(...allData.map(d => d.price));
        const mid = (min + max) / 2;
        const minTime = Math.min(...allData.map(d => d.time));
        const maxTime = Math.max(...allData.map(d => d.time));

        const norm = allData.map(p => ({
            x: ((p.time - minTime) / (maxTime - minTime || 1)) * chartWidth + margin.left,
            y: chartHeight - ((p.price - min) / (max - min || 1)) * chartHeight + margin.top
        }));

        const split = pastData.length - 1;
        const pastLine = norm.slice(0, split + 1).map(p => `${p.x},${p.y}`).join(" ");
        const futureLine = norm.slice(split).map(p => `${p.x},${p.y}`).join(" ");
        const areaPath = `${pastLine} L ${norm[split].x},${chartHeight + margin.top} L ${margin.left},${chartHeight + margin.top} Z`;
        
        const color = diff > 0 ? "#22c55e" : diff < 0 ? "#ef4444" : "#94a3b8";

        // ★ X軸ラベル（時間）の生成ロジック
        const stepIndex = Math.floor(pastData.length / 3);
        let xLabels = "";
        for (let i = 0; i < pastData.length; i += stepIndex) {
            const x = norm[i].x;
            xLabels += `<text x="${x}" y="${margin.top + chartHeight + 25}" text-anchor="middle" font-size="12" fill="#64748b" font-weight="normal">${_format(pastData[i].time, interval)}</text>`;
        }
        xLabels += `<text x="${norm[split].x}" y="${margin.top + chartHeight + 25}" text-anchor="middle" font-size="12" fill="#cbd5e1" font-weight="normal">Now</text>`;

        return `
        <div style="margin: 0 0 0 -30px; padding: 0; overflow: visible;">
          <svg viewBox="0 0 ${width} ${height}" width="100%" height="${height}" preserveAspectRatio="xMidYMin meet" style="display: block; overflow: visible;">
            <defs>
              <linearGradient id="miniAreaGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stop-color="#6366f1" stop-opacity="0.15"/>
                <stop offset="100%" stop-color="#6366f1" stop-opacity="0"/>
              </linearGradient>
            </defs>

            <line x1="${margin.left}" y1="${margin.top}" x2="${margin.left + chartWidth}" y2="${margin.top}" stroke="rgba(255,255,255,0.1)" />
            <line x1="${margin.left}" y1="${margin.top + chartHeight/2}" x2="${margin.left + chartWidth}" y2="${margin.top + chartHeight/2}" stroke="rgba(255,255,255,0.05)" stroke-dasharray="4 4" />
            <line x1="${margin.left}" y1="${margin.top + chartHeight}" x2="${margin.left + chartWidth}" y2="${margin.top + chartHeight}" stroke="rgba(255,255,255,0.2)" />
            
            ${xLabels}

            ${_buildLabel(max, margin.top + 5, margin.left - 10, 12)}
            ${_buildLabel(mid, margin.top + chartHeight/2 + 5, margin.left - 10, 12)}
            ${_buildLabel(min, margin.top + chartHeight + 5, margin.left - 10, 12)}

            <path d="${areaPath}" fill="url(#miniAreaGrad)" />
            <polyline points="${pastLine}" fill="none" stroke="#94a3b8" stroke-width="2" />
            
            <line x1="${norm[split].x}" y1="${margin.top}" x2="${norm[split].x}" y2="${margin.top + chartHeight}" stroke="${color}" stroke-dasharray="3 3" opacity="0.4" />
            <polyline points="${futureLine}" fill="none" stroke="${color}" stroke-width="3" stroke-dasharray="6 4" stroke-linecap="round" />

            <circle cx="${norm[split].x}" cy="${norm[split].y}" r="4" fill="#020617" stroke="${color}" stroke-width="2"/>
          </svg>
        </div>`;
    };
})();