document.addEventListener("DOMContentLoaded", function () {

  const banner = document.getElementById("cookieBanner");
  const acceptBtn = document.getElementById("acceptCookies");
  const declineBtn = document.getElementById("declineCookies");

  if (!banner) return;

  // =========================
  // すでに選択済みか確認
  // =========================
  const consent = localStorage.getItem("cookieConsent");

  if (consent === "accepted" || consent === "declined") {
    banner.style.display = "none";
    return;
  }

  // 初回のみ表示
  banner.style.display = "block";

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