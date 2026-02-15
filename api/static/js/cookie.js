document.addEventListener("DOMContentLoaded", function () {

  const banner = document.getElementById("cookieBanner");
  const acceptBtn = document.getElementById("acceptCookies");
  const declineBtn = document.getElementById("declineCookies");

  if (!banner) return;

  // =========================
  // すでに選択済みか確認
  // =========================
  const consent = localStorage.getItem("cookieConsent");

  // 未選択のときだけ表示
  if (!consent) {
    banner.style.display = "flex"; // ← flexで表示（blockではない）
  }

  // =========================
  // Accept
  // =========================
  if (acceptBtn) {
    acceptBtn.addEventListener("click", function () {
      localStorage.setItem("cookieConsent", "accepted");
      banner.style.display = "none";
    });
  }

  // =========================
  // Decline
  // =========================
  if (declineBtn) {
    declineBtn.addEventListener("click", function () {
      localStorage.setItem("cookieConsent", "declined");
      banner.style.display = "none";
    });
  }

});