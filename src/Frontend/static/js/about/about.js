 // Mobile Menu Toggle
 const mobileMenuBtn = document.getElementById('mobile-menu-btn');
 const navLinks = document.getElementById('nav-links');
 
 mobileMenuBtn.addEventListener('click', () => {
     navLinks.classList.toggle('active');
     
     // Change icon based on menu state
     const icon = mobileMenuBtn.querySelector('i');
     if (navLinks.classList.contains('active')) {
         icon.classList.remove('fa-bars');
         icon.classList.add('fa-times');
     } else {
         icon.classList.remove('fa-times');
         icon.classList.add('fa-bars');
     }
 });
 
 // Navbar Scroll Effect
 window.addEventListener('scroll', () => {
     const navbar = document.querySelector('.navbar');
     if (window.scrollY > 50) {
         navbar.style.padding = '0.5rem 0';
         navbar.style.boxShadow = '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)';
     } else {
         navbar.style.padding = '';
         navbar.style.boxShadow = '';
     }
 });
 
 // Smooth Scrolling for Anchor Links
 document.querySelectorAll('a[href^="#"]').forEach(anchor => {
     anchor.addEventListener('click', function(e) {
         e.preventDefault();
         
         const targetId = this.getAttribute('href');
         if (targetId === '#') return;
         
         const targetElement = document.querySelector(targetId);
         if (targetElement) {
             window.scrollTo({
                 top: targetElement.offsetTop - 80,
                 behavior: 'smooth'
             });
             
             // Close mobile menu if open
             if (navLinks.classList.contains('active')) {
                 navLinks.classList.remove('active');
                 const icon = mobileMenuBtn.querySelector('i');
                 icon.classList.remove('fa-times');
                 icon.classList.add('fa-bars');
             }
         }
     });
 });
 
 // Animate elements on scroll
 const animateOnScroll = () => {
     const elements = document.querySelectorAll('.feature-card, .section-title, .why-choose-content');
     
     elements.forEach(element => {
         const elementPosition = element.getBoundingClientRect().top;
         const screenPosition = window.innerHeight / 1.2;
         
         if (elementPosition < screenPosition) {
             element.style.opacity = '1';
             element.style.transform = 'translateY(0)';
         }
     });
 };
 
 // Set initial styles for animation
 document.querySelectorAll('.feature-card, .section-title, .why-choose-content').forEach(element => {
     element.style.opacity = '0';
     element.style.transform = 'translateY(20px)';
     element.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
 });
 
 // Run animation on load and scroll
 window.addEventListener('load', animateOnScroll);
 window.addEventListener('scroll', animateOnScroll);