document.addEventListener("DOMContentLoaded", function () {
  // Initialize the store
  initializeStore();

  // Initialize SVG icons
  initializeSvgIcons();
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
      const productPrice = parseFloat(productCard.getAttribute("data-price"));

      // Add product to cart without checking for collapse
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
  // Removed toggle-cart functionality since the sidebar is always expanded.
  const checkoutBtn = document.getElementById("checkoutBtn");

  // Initialize cart from localStorage if available
  loadCartFromStorage();

  // Removed event listener for toggleCartBtn

  // Handle checkout
  checkoutBtn.addEventListener("click", function () {
    if (this.disabled) return;

    // Simulate checkout process
    alert("Processing your order...");

    // In a real application, you would redirect to a checkout page or open a modal
    setTimeout(() => {
      alert("Thank you for your purchase!");
      clearCart();
    }, 1500);
  });
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

  // Save cart to localStorage
  saveCartToStorage();
}

function removeFromCart(productId) {
  cart = cart.filter((item) => item.id !== productId);

  // Update cart UI
  updateCartUI();

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

      // Save cart to localStorage
      saveCartToStorage();
    }
  }
}

function clearCart() {
  cart = [];

  // Update cart UI
  updateCartUI();

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
    } catch (error) {
      console.error("Error loading cart from storage:", error);
      cart = [];
    }
  }
}
