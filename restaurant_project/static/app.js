console.log("JS is connected!");

const searchIcon1 = document.querySelector("#searchicon1");
const searchInput1 = document.querySelector("#searchinput1");
if (searchIcon1 && searchInput1) {
  searchIcon1.addEventListener("click", function () {
    searchInput1.style.display = "flex";
    searchIcon1.style.display = "none";
  });
}

const searchIcon2 = document.querySelector("#searchicon2");
const searchInput2 = document.querySelector("#searchinput2");
if (searchIcon2 && searchInput2) {
  searchIcon2.addEventListener("click", function () {
    searchInput2.style.display = "flex";
    searchIcon2.style.display = "none";
  });
}

const bar = document.querySelector(".fa-bars");
const cross = document.querySelector("#hdcross");
const headerbar = document.querySelector(".headerbar");

if (bar && cross && headerbar) {
  bar.addEventListener("click", function () {
    setTimeout(() => {
      cross.style.display = "block";
    }, 200);
    headerbar.style.right = "0%";
  });

  cross.addEventListener("click", function () {
    cross.style.display = "none";
    headerbar.style.right = "-100%";
  });

  document.querySelectorAll(".headerbar .nav a").forEach((link) => {
    link.addEventListener("click", () => {
      headerbar.style.right = "-100%";
      cross.style.display = "none";
    });
  });
}
