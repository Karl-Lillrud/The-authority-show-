/* * * * * * * * */
/*  Navigation   */
/* * * * * * * * */

function toggleHamburger(x) {
  x.classList.toggle("change"); // Switch the hamburger icon to an "X" icon

  document.querySelector(".nav-links").classList.toggle("change"); // Toggle the visibility of the navigation background
  
  const menuItem = document.querySelectorAll(".nav-item");
  menuItem.forEach((item) => {
    item.classList.toggle("change"); // Toggle the visibility of the navigation items
  });
}

window.onscroll = () => { // Change the active class of the navigation items based on scroll position
  const sections = document.querySelectorAll("section");
  const navLi = document.querySelectorAll("nav ul.nav-links li");
  var current = "";
  var midOfDevice = window.innerHeight / 2;

  sections.forEach((section) => { // Loop through each section to determine which one is currently in view
    const sectionTop = section.offsetTop - midOfDevice;
    if (scrollY >= sectionTop ) {
      current = section.getAttribute("id"); }
  });

  navLi.forEach((li) => { // Loop through each navigation item to update its active state
    li.classList.remove("active");
    if (li.classList.contains(current)) {
      li.classList.add("active");
    }
  });
};