document.addEventListener("DOMContentLoaded", function () {

  const banner = document.getElementById("cookieBanner");
  const acceptBtn = document.getElementById("acceptCookies");
  const declineBtn = document.getElementById("declineCookies");

  const consent = localStorage.getItem("cookie_consent");

  if (!consent && banner) {
    banner.style.display = "block";
  }

  if (acceptBtn) {
    acceptBtn.addEventListener("click", function () {
      localStorage.setItem("cookie_consent", "accepted");
      banner.style.display = "none";
    });
  }

  if (declineBtn) {
    declineBtn.addEventListener("click", function () {
      localStorage.setItem("cookie_consent", "declined");
      banner.style.display = "none";
    });
  }

});