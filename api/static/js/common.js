/* =========================================
   Global UI (Header / Footer)
========================================= */

document.addEventListener("DOMContentLoaded", function () {

  const hamburgerBtn = document.getElementById("hamburgerBtn");
  const mobileMenu = document.getElementById("mobileMenu");

  if (hamburgerBtn && mobileMenu) {
    hamburgerBtn.addEventListener("click", function () {
      hamburgerBtn.classList.toggle("active");
      mobileMenu.classList.toggle("active");
      hamburgerBtn.blur();
    });
  }

  const yearEl = document.getElementById("currentYear");
  if (yearEl) {
    yearEl.textContent = new Date().getFullYear();
  }

});


/* =========================================
   Number Formatting Utils
========================================= */

function formatSmallNumber(price) {

  const n = Number(price);
  if (!Number.isFinite(n)) return "—";

  const abs = Math.abs(n);

  if (abs >= 1) {
    return abs.toLocaleString(undefined, {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    });
  }

  if (abs >= 0.01) {
    return abs.toFixed(4);
  }

  const str = abs.toFixed(12);
  const match = str.match(/^0\.0+/);

  if (!match) {
    return abs.toFixed(6);
  }

  const zeroCount = match[0].length - 2;

  let significant = str.slice(match[0].length);
  significant = significant.replace(/0+$/, "");
  significant = significant.slice(0, 4);

  return `0.0<sub class="zero-count">${zeroCount}</sub>${significant}`;
}


function formatUSD(price) {

  const n = Number(price);
  if (!Number.isFinite(n)) return "USD —";

  const sign = n < 0 ? "-" : "";

  return sign + "USD " + formatSmallNumber(Math.abs(n));
}


function formatDiff(diff, pct) {

  const sign = diff > 0 ? "+" : diff < 0 ? "-" : "";
  const diffAbs = Math.abs(diff);
  const pctAbs = Math.abs(pct);

  return `${sign}$${formatSmallNumber(diffAbs)} (${sign}${pctAbs.toFixed(2)}%)`;
}


/* =========================================
   Apply Price Formatting (Reusable)
========================================= */

function applyPriceFormatting() {

  document.querySelectorAll(".price").forEach(el => {
    const value = el.dataset.price;
    el.innerHTML = formatUSD(value);
  });

  document.querySelectorAll(".change").forEach(el => {
    const diff = Number(el.dataset.diff);
    const pct = Number(el.dataset.pct);

    const direction =
      diff > 0 ? "up" :
      diff < 0 ? "down" :
      "flat";

    el.innerHTML =
      `<span class="${direction}">
        ${formatDiff(diff, pct)}
      </span>`;
  });

}