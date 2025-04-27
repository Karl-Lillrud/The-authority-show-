// store.js
let apiBaseUrl = ''; // Added for consistency if needed elsewhere
let stripePublicKey = ''; // Variable to hold the fetched key
let stripe = null; // Variable to hold the Stripe instance

document.addEventListener("DOMContentLoaded", async () => { // Make the listener async
  // Initialize the store layout first
  initializeStoreLayout(); // Renamed to avoid confusion with Stripe init

  // Initialize SVG icons
  initializeSvgIcons();

  // Load Stripe.js script tag (doesn't initialize Stripe object yet)
  loadStripeScript();

  // --- Fetch config and initialize Stripe ---
  try {
    const response = await fetch('/config'); // Fetch from the backend endpoint
    if (!response.ok) {
       const errorData = await response.json();
       throw new Error(errorData.error || `Failed to fetch config: ${response.statusText}`);
    }
    const config = await response.json();
    apiBaseUrl = config.apiBaseUrl || ''; // Store API base URL if needed
    stripePublicKey = config.stripePublicKey; // Get the key from config

    if (!stripePublicKey) {
      console.error("Stripe Public Key not found in config from server.");
      // Display error to user if needed
      const statusElement = document.getElementById("checkoutStatus"); // Example error display
      if (statusElement) statusElement.textContent = "Configuration error: Payment key missing.";
      return; // Stop initialization if key is missing
    }

    // Initialize Stripe object with the fetched key
    stripe = Stripe(stripePublicKey);
    console.log("Stripe initialized successfully.");

  } catch (error) {
    console.error("Error fetching or processing configuration:", error);
    // Display error to user if needed
    const statusElement = document.getElementById("checkoutStatus"); // Example error display
    if (statusElement) statusElement.textContent = "Error loading payment configuration: " + error.message;
  }
  // --- End config fetch and Stripe init ---

});

function loadStripeScript() {
  // Ensure Stripe.js script is added to the page
  if (!document.querySelector('script[src="https://js.stripe.com/v3/"]')) {
    const stripeScript = document.createElement("script");
    stripeScript.src = "https://js.stripe.com/v3/";
    stripeScript.async = true;
    document.head.appendChild(stripeScript);
  }
}

// Add resize event listener
window.addEventListener("resize", () => {
  // Re-evaluate cart setup on resize for responsive behavior
  setupCart();
});

function initializeStoreLayout() { // Renamed function
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

  // Route "Purchase History" button to Account page
  const purchaseHistoryButton = document.querySelector(".view-history");
  if (purchaseHistoryButton) {
    purchaseHistoryButton.addEventListener("click", () => {
      localStorage.setItem("activeAccountSection", "settings-purchases");
      window.location.href = "/account";
    });
  }
}

function setupCart() {
  const shoppingCart = document.getElementById("shoppingCart"); // The sidebar/modal
  const checkoutBtn = document.getElementById("checkoutBtn");

  // Remove previous listeners to avoid duplicates on resize
  shoppingCart.replaceWith(shoppingCart.cloneNode(true)); // Reset might clear cart items, so reload

  // Re-fetch elements after cloning
  const newShoppingCart = document.getElementById("shoppingCart");
  const newCheckoutBtn = document.getElementById("checkoutBtn");

  // Initialize cart from localStorage if available
  loadCartFromStorage();

  // Handle checkout
  newCheckoutBtn.addEventListener("click", async function () {
    if (this.disabled) return;

    // --- Check if Stripe is initialized ---
    if (!stripe) {
        console.error("Stripe is not initialized. Cannot proceed.");
        alert("Payment system is not ready. Please try again shortly.");
        this.disabled = false; // Re-enable button
        this.textContent = "Complete the Purchase";
        return;
    }
    // --- End Stripe check ---


    try {
      // Disable button to prevent multiple clicks
      this.disabled = true;
      this.textContent = "Processing...";

      // Filter cart items
      const creditItems = cart.filter((item) => item.type === "Credit Pack");
      const subscriptionItems = cart.filter(
        (item) => item.type === "Subscription"
      );

      // Enforce only one subscription and quantity 1
      if (
        subscriptionItems.length > 1 ||
        (subscriptionItems[0] && subscriptionItems[0].quantity > 1)
      ) {
        alert("You can only purchase one subscription at a time.");
        this.disabled = false;
        this.textContent = "Complete the Purchase";
        return;
      }

      if (creditItems.length === 0 && subscriptionItems.length === 0) {
        alert("Your cart is empty or contains unsupported items.");
        this.disabled = false;
        this.textContent = "Complete the Purchase";
        return;
      }

      let totalAmount = 0;
      let totalCredits = 0;
      let plan = null;

      if (creditItems.length > 0) {
        creditItems.forEach((item) => {
          totalAmount += item.price * item.quantity;
          const credits = getCreditsForProduct(item.id);
          totalCredits += credits * item.quantity;
        });
      }

      if (subscriptionItems.length === 1) {
        const subscription = subscriptionItems[0];
        plan = getPlanForProduct(subscription.id);
        totalAmount += subscription.price;
      }

      // Build payload
      let payload = { amount: totalAmount.toFixed(2) };
      if (totalCredits > 0) payload.credits = totalCredits;
      if (plan) payload.plan = plan;

      // Make API call to create checkout session
      // Construct the full URL using the fetched base URL or use relative path if empty
      const checkoutUrl = apiBaseUrl ? `${apiBaseUrl}/create-checkout-session` : "/create-checkout-session";
      const response = await fetch(checkoutUrl, { // Use constructed URL
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
        credentials: "same-origin"
      });

      const contentType = response.headers.get("content-type");
      if (contentType && contentType.includes("text/html")) {
        alert("Session expired. Please log in again.");
        setTimeout(() => {
          window.location.href =
            "/signin?redirect=" + encodeURIComponent(window.location.pathname);
        }, 2000);
        this.disabled = false;
        this.textContent = "Complete the Purchase";
        return;
      }

      const data = await response.json();

      if (data.sessionId) {
        // Use the globally initialized Stripe object to redirect
        await stripe.redirectToCheckout({ sessionId: data.sessionId });
        // Clear cart after successful redirection attempt
        clearCart();
      } else {
        alert("Failed to create checkout: " + (data.error || "Unknown error"));
        this.disabled = false;
        this.textContent = "Complete the Purchase";
      }
    } catch (err) {
      console.error("Error during checkout:", err);
      alert("Error: " + err.message);
      this.disabled = false;
      this.textContent = "Complete the Purchase";
    }
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

// Map product IDs to credit amounts based on credit_costs.py
function getCreditsForProduct(productId) {
  switch (productId) {
    case "credit-basic":
      return 2500; // Basic Pack
    case "credit-pro":
      return 5000; // Pro Pack
    case "credit-premium":
      return 12000; // Studio Pack
    default:
      return 0; // Non-credit products or unknown
  }
}

// Map product IDs to subscription plans
function getPlanForProduct(productId) {
  switch (productId) {
    case "sub-standard":
      return "pro"; // Corrected: Matches "Pro Subscription" and backend logic
    case "sub-pro":
      return "studio"; // Corrected: Matches "Studio Subscription" and backend logic
    case "sub-enterprise":
      return "enterprise"; // This seems correct
    default:
      return null; // Invalid subscription product
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
    case "episode":
      return "Episode Pack";
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
