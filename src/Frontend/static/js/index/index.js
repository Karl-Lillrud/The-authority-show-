/* Hamburger menu */
function toggleHamburger(x) {
  x.classList.toggle("change"); // Switch the hamburger icon to an "X" icon

  document.querySelector(".nav-links").classList.toggle("change"); // Toggle the visibility of the navigation background
  
  const menuItem = document.querySelectorAll(".nav-item");
  menuItem.forEach((item) => {
    item.classList.toggle("change"); // Toggle the visibility of the navigation items
  });
}