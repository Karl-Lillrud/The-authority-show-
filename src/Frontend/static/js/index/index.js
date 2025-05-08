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
};

/* * * * * * * * * */
/*  Scroll Events  */
/* * * * * * * * * */
function scrollNavigation() { // Change the active class of the navigation items based on scroll position
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

function scrollAnimation() { // Trigger animations based on scroll position
  const animateElements = []; // Array to hold elements that will be animated

  animateElements.push(document.querySelectorAll("#index-about .container h1")); 
  animateElements.push(document.querySelectorAll("#index-about .container #about-figure-1")); 
  animateElements.push(document.querySelectorAll("#index-about .container #about-figure-2"));
  animateElements.push(document.querySelectorAll("#index-about .container .benefits-container ul li"));
  animateElements.push(document.querySelectorAll("#index-features .container #feature-figure-1"));
  animateElements.push(document.querySelectorAll("#index-features .container #feature-figure-2"));
  animateElements.push(document.querySelectorAll("#index-features .container #feature-figure-3"));
  animateElements.push(document.querySelectorAll("#index-features .container #feature-figure-4"));
  animateElements.push(document.querySelectorAll("#index-features .container #feature-figure-5"));
  animateElements.push(document.querySelectorAll("#index-features .container h2"));
  animateElements.push(document.querySelectorAll("#index-features article:last-of-type h2"));
  animateElements.push(document.querySelectorAll("#index-features .future-item-icon svg"));
  animateElements.push(document.querySelectorAll("#index-get-started h1"));
  animateElements.push(document.querySelectorAll("#index-get-started a.button"));

  animateElements.forEach((element) => { // Loop through each element to check if it is in view
    element.forEach((el) => {
      const elTop = el.getBoundingClientRect().y - 1150; // Get the top position of the element relative to the viewport
      if (elTop <= 0) { // Check if the element is in view
        el.classList.add("animate"); // Add the animate class to trigger animations
        el.style.animationDelay = "0.5s";
      }
    });
  });
};

window.addEventListener("scroll", scrollNavigation); // Add scroll event listener to update navigation based on scroll position
window.addEventListener("scroll", scrollAnimation); // Add scroll event listener to trigger animations based on scroll position
