document.addEventListener("DOMContentLoaded", function () {

  const hamburgerBtn = document.getElementById("hamburgerBtn");
  const mobileMenu = document.getElementById("mobileMenu");

  if (!hamburgerBtn || !mobileMenu) return;

  hamburgerBtn.addEventListener("click", function () {
    hamburgerBtn.classList.toggle("active");
    mobileMenu.classList.toggle("active");
    hamburgerBtn.blur();
  });

});

document.addEventListener("DOMContentLoaded", function () {

  const yearEl = document.getElementById("currentYear");
  if (yearEl) {
    yearEl.textContent = new Date().getFullYear();
  }

});
