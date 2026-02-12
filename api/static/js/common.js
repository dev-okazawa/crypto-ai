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
