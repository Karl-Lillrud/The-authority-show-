document.addEventListener("DOMContentLoaded", () => {
  // Initialize the store
  initializeStore();

  // Initialize SVG icons
  initializeSvgIcons();

  // Match sidebar height on initial load - DISABLED
  // matchSidebarHeight();
});

// Add resize event listener
window.addEventListener("resize", () => {
  // Match sidebar height on resize - DISABLED
  // matchSidebarHeight();
  // Re-evaluate cart setup on resize for responsive behavior
  setupCart();
});

function initializeStore() {
  // Set up cart functionality
  setupCart();

  // Set up add to cart buttons
  setupAddToCartButtons();

  // Set up placeholder images for style previews
  setupPlaceholderImages();
}

function initializeSvgIcons() {
  // This function will be implemented in svgstore.js
  if (typeof initSvgIcons === "function") {
    initSvgIcons();
  }
}

function setupPlaceholderImages() {
  // Replace image placeholders with actual placeholder images
  const stylePreviews = document.querySelectorAll(".style-preview");

  stylePreviews.forEach((preview, index) => {
    const styles = ["minimal", "premium", "enterprise"];
    const style = styles[index % styles.length];

    // Set placeholder image URL
    preview.src = `/placeholder.svg?height=150&width=300&text=${style}`;
  });
}

function setupAddToCartButtons() {
  const addToCartButtons = document.querySelectorAll(".add-to-cart-btn");

  addToCartButtons.forEach((button) => {
    button.addEventListener("click", function () {
      const productId = this.getAttribute("data-product-id");
      const productCard = document.querySelector(
        `.product-card[data-product-id="${productId}"]`
      );

      if (!productCard) return;

      const productName = productCard.querySelector("h3").textContent;
      const productType = productCard.getAttribute("data-product-type");
      const productPrice = Number.parseFloat(
        productCard.getAttribute("data-price")
      );

      // Add product to cart
      addToCart(productId, productName, productType, productPrice);

      // Update button state
      this.textContent = "Added to Cart";
      this.classList.add("in-cart");

      // Reset button after 2 seconds
      setTimeout(() => {
        this.textContent = "Add to Cart";
        this.classList.remove("in-cart");
      }, 2000);
    });
  });
}

function setupCart() {
  const cartButton = document.getElementById("cartButton"); // Button to open modal
  const closeCartBtn = document.getElementById("closeCartBtn"); // Button inside modal
  const shoppingCart = document.getElementById("shoppingCart"); // The sidebar/modal
  const checkoutBtn = document.getElementById("checkoutBtn");
  const viewportWidth = window.innerWidth;

  // Remove previous listeners to avoid duplicates on resize
  cartButton.replaceWith(cartButton.cloneNode(true));
  closeCartBtn.replaceWith(closeCartBtn.cloneNode(true));
  document.removeEventListener("click", closeCartOnClickOutside);
  shoppingCart.replaceWith(shoppingCart.cloneNode(true)); // Might reset cart items, consider alternatives if needed

  // Re-fetch elements after cloning
  const newCartButton = document.getElementById("cartButton");
  const newCloseCartBtn = document.getElementById("closeCartBtn");
  const newShoppingCart = document.getElementById("shoppingCart");
  const newCheckoutBtn = document.getElementById("checkoutBtn"); // Re-fetch checkout button too

  // Initialize cart from localStorage if available
  loadCartFromStorage(); // Ensure this repopulates the newShoppingCart if cloned

  if (viewportWidth <= 992) {
    // Mobile: Modal behavior
    newShoppingCart.classList.add("hidden"); // Start hidden on mobile
    newShoppingCart.style.height = ""; // Ensure height is not fixed

    newCartButton.addEventListener("click", (e) => {
      e.stopPropagation();
      newShoppingCart.classList.remove("hidden");
    });

    newCloseCartBtn.addEventListener("click", () => {
      newShoppingCart.classList.add("hidden");
    });

    document.addEventListener("click", closeCartOnClickOutside);

    newShoppingCart.addEventListener("click", (e) => {
      e.stopPropagation();
    });
  } else {
    // Desktop: Sidebar is always visible
    newShoppingCart.classList.remove("hidden"); // Ensure visible
    document.removeEventListener("click", closeCartOnClickOutside); // Remove outside click listener
    // matchSidebarHeight(); // Ensure height is matched - DISABLED
  }

  // Handle checkout (attach to the potentially new button)
  newCheckoutBtn.addEventListener("click", function () {
    if (this.disabled) return;
    alert("Processing your order...");
    setTimeout(() => {
      alert("Thank you for your purchase!");
      clearCart();
      if (viewportWidth <= 992) {
        // Only hide modal on mobile
        newShoppingCart.classList.add("hidden");
      }
    }, 1500);
  });
}

// Define the outside click handler separately
function closeCartOnClickOutside(e) {
  const shoppingCart = document.getElementById("shoppingCart");
  const cartButton = document.getElementById("cartButton");
  if (
    shoppingCart &&
    cartButton &&
    !shoppingCart.contains(e.target) &&
    e.target !== cartButton &&
    !cartButton.contains(e.target)
  ) {
    shoppingCart.classList.add("hidden");
  }
}

// Cart functionality
let cart = [];

function addToCart(productId, productName, productType, productPrice) {
  // Check if product already exists in cart
  const existingItemIndex = cart.findIndex((item) => item.id === productId);

  if (existingItemIndex !== -1) {
    // Increment quantity if product already in cart
    cart[existingItemIndex].quantity += 1;
  } else {
    // Add new item to cart
    cart.push({
      id: productId,
      name: productName,
      type: formatProductType(productType),
      price: productPrice,
      quantity: 1
    });
  }

  // Update cart UI
  updateCartUI();

  // Update notification badge
  updateCartNotification();

  // Save cart to localStorage
  saveCartToStorage();
}

function removeFromCart(productId) {
  cart = cart.filter((item) => item.id !== productId);

  // Update cart UI
  updateCartUI();

  // Update notification badge
  updateCartNotification();

  // Save cart to localStorage
  saveCartToStorage();
}

function updateItemQuantity(productId, newQuantity) {
  const itemIndex = cart.findIndex((item) => item.id === productId);

  if (itemIndex !== -1) {
    if (newQuantity <= 0) {
      // Remove item if quantity is 0 or less
      removeFromCart(productId);
    } else {
      // Update quantity
      cart[itemIndex].quantity = newQuantity;

      // Update cart UI
      updateCartUI();

      // Update notification badge
      updateCartNotification();

      // Save cart to localStorage
      saveCartToStorage();
    }
  }
}

function clearCart() {
  cart = [];

  // Update cart UI
  updateCartUI();

  // Update notification badge
  updateCartNotification();

  // Save cart to localStorage
  saveCartToStorage();
}

function updateCartUI() {
  const cartItemsContainer = document.getElementById("cartItems");
  const cartItemCount = document.querySelector(".cart-item-count");
  const totalAmount = document.querySelector(".total-amount");
  const checkoutBtn = document.getElementById("checkoutBtn");

  // Clear current items
  cartItemsContainer.innerHTML = "";

  if (cart.length === 0) {
    // Show empty cart message
    cartItemsContainer.innerHTML =
      '<div class="empty-cart-message">Your cart is empty</div>';
    cartItemCount.textContent = "0 items";
    totalAmount.textContent = "$0.00";
    checkoutBtn.disabled = true;
  } else {
    // Add items to cart
    cart.forEach((item) => {
      const cartItem = document.createElement("div");
      cartItem.classList.add("cart-item");

      cartItem.innerHTML = `
        <div class="cart-item-info">
          <span class="cart-item-name">${item.name}</span>
          <span class="cart-item-type">${item.type}</span>
        </div>
        <div class="cart-item-price">$${(item.price * item.quantity).toFixed(
          2
        )}</div>
        <div class="cart-item-actions">
          <div class="cart-item-quantity">
            <button class="quantity-btn decrease-btn" data-product-id="${
              item.id
            }">-</button>
            <span class="quantity-value">${item.quantity}</span>
            <button class="quantity-btn increase-btn" data-product-id="${
              item.id
            }">+</button>
          </div>
          <button class="remove-item-btn" data-product-id="${item.id}">
            <span class="svg-placeholder remove-icon"></span>
          </button>
        </div>
      `;

      cartItemsContainer.appendChild(cartItem);
    });

    // Add event listeners to quantity buttons
    const decreaseButtons = document.querySelectorAll(".decrease-btn");
    const increaseButtons = document.querySelectorAll(".increase-btn");
    const removeButtons = document.querySelectorAll(".remove-item-btn");

    decreaseButtons.forEach((button) => {
      button.addEventListener("click", function () {
        const productId = this.getAttribute("data-product-id");
        const item = cart.find((item) => item.id === productId);
        if (item) {
          updateItemQuantity(productId, item.quantity - 1);
        }
      });
    });

    increaseButtons.forEach((button) => {
      button.addEventListener("click", function () {
        const productId = this.getAttribute("data-product-id");
        const item = cart.find((item) => item.id === productId);
        if (item) {
          updateItemQuantity(productId, item.quantity + 1);
        }
      });
    });

    removeButtons.forEach((button) => {
      button.addEventListener("click", function () {
        const productId = this.getAttribute("data-product-id");
        removeFromCart(productId);
      });
    });

    // Update cart count and total
    const itemCount = cart.reduce((total, item) => total + item.quantity, 0);
    const totalPrice = cart.reduce(
      (total, item) => total + item.price * item.quantity,
      0
    );

    cartItemCount.textContent = `${itemCount} item${
      itemCount !== 1 ? "s" : ""
    }`;
    totalAmount.textContent = `$${totalPrice.toFixed(2)}`;
    checkoutBtn.disabled = false;
  }
}

function updateCartNotification() {
  const cartNotification = document.getElementById("cartNotification");
  const itemCount = cart.reduce((total, item) => total + item.quantity, 0);

  if (itemCount > 0) {
    cartNotification.textContent = itemCount;
    cartNotification.classList.add("visible");
  } else {
    cartNotification.textContent = "0";
    cartNotification.classList.remove("visible");
  }
}

function formatProductType(type) {
  switch (type) {
    case "credit":
      return "Credit Pack";
    case "style":
      return "Landing Page Style";
    case "subscription":
      return "Subscription";
    default:
      return type;
  }
}

// LocalStorage functions
function saveCartToStorage() {
  localStorage.setItem("podmanager_cart", JSON.stringify(cart));
}

function loadCartFromStorage() {
  const savedCart = localStorage.getItem("podmanager_cart");

  if (savedCart) {
    try {
      cart = JSON.parse(savedCart);
      updateCartUI();
      updateCartNotification();
    } catch (error) {
      console.error("Error loading cart from storage:", error);
      cart = [];
    }
  }
}

// Function to match sidebar height to credit packs section height - DISABLED
/*
function matchSidebarHeight() {
  const creditPacksSection = document.querySelector('.credit-packs-section');
  const shoppingCart = document.getElementById('shoppingCart');
  const viewportWidth = window.innerWidth;

  if (creditPacksSection && shoppingCart) {
    if (viewportWidth > 992) {
      // Desktop: Match height and ensure it's visible
      shoppingCart.classList.remove('hidden'); // Make sure it's not hidden
      const creditPacksHeight = creditPacksSection.offsetHeight;
      shoppingCart.style.height = `${creditPacksHeight}px`;
    } else {
      // Mobile: Reset height for modal behavior
      shoppingCart.style.height = ''; // Reset height
      // Hidden state is managed by setupCart based on clicks
    }
  }
}
*/
// Add a placeholder function if needed, or just remove the calls
function matchSidebarHeight() {
  // Placeholder - height matching disabled for now
  const shoppingCart = document.getElementById("shoppingCart");
  const viewportWidth = window.innerWidth;
  if (shoppingCart && viewportWidth <= 992) {
    // Ensure height is reset on mobile if JS was setting it
    shoppingCart.style.height = "";
  } else if (shoppingCart && viewportWidth > 992) {
    // Ensure height is reset on desktop too, as JS is disabled
    shoppingCart.style.height = "";
  }
}
