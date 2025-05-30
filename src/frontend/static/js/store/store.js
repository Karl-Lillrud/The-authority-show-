// store.js
import { showNotification } from "/static/js/components/notifications.js";

let apiBaseUrl = "";
let stripePublicKey = "";
let stripe = null;

document.addEventListener("DOMContentLoaded", async () => {
  initializeStoreLayout();
  initializeSvgIcons();
  await initializeStripe();
  // Återställ checkout-knappen vid sidladdning
  resetCheckoutButton();
  
  await handlePurchaseSuccess();
  setupContinueShoppingButton();

  const pageTitle = document.getElementById("page-title");
  if (pageTitle) {
    pageTitle.textContent = "Store"; // Set the page title
  }

  setupSubscriptionToggle();
});

async function handlePurchaseSuccess() {
  const urlParams = new URLSearchParams(window.location.search);
  const purchaseSuccess = urlParams.get("purchase_success") === "true";
  const subscriptionUpdated = urlParams.get("subscription_updated") === "true";

  if (purchaseSuccess || subscriptionUpdated) {
    localStorage.removeItem("podmanager_cart");
    removePurchaseParamsFromURL(urlParams, purchaseSuccess, subscriptionUpdated);
    displaySuccessPopup();
  }
}

function removePurchaseParamsFromURL(urlParams, purchaseSuccess, subscriptionUpdated) {
  const url = new URL(window.location.href);
  if (purchaseSuccess) url.searchParams.delete("purchase_success");
  if (subscriptionUpdated) url.searchParams.delete("subscription_updated");
  window.history.replaceState({}, document.title, url.href);
}

function displaySuccessPopup() {
  const successPopup = document.getElementById('success-popup');
  if (successPopup) {
    successPopup.style.display = 'flex';
  }
}

function setupContinueShoppingButton() {
  const continueShoppingBtn = document.getElementById('continueShoppingBtn');
  const successPopup = document.getElementById('success-popup');

  if (continueShoppingBtn) {
    continueShoppingBtn.addEventListener('click', () => {
      window.location.reload();
      if (successPopup) {
        successPopup.style.display = 'none';
      }
    });
  }
}

async function initializeStripe() {
  try {
    await loadStripeScript();
    const response = await fetch("/config");
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(
        errorData.error || `Failed to fetch config: ${response.statusText}`
      );
    }
    const config = await response.json();
    apiBaseUrl = config.apiBaseUrl || "";
    stripePublicKey = config.stripePublicKey;

    if (!stripePublicKey) {
      console.error("Stripe Public Key not found in config from server.");
      const statusElement = document.getElementById("checkoutStatus");
      if (statusElement)
        statusElement.textContent = "Configuration error: Payment key missing.";
      showNotification(
        "Configuration Error",
        "Payment key missing.",
        "error",
        5000
      );
      return;
    }

    if (typeof Stripe === "undefined") {
      throw new Error("Stripe.js failed to load.");
    }
    stripe = Stripe(stripePublicKey);
    console.log("Stripe initialized successfully.");
  } catch (error) {
    console.error("Error initializing Stripe:", error);
    const statusElement = document.getElementById("checkoutStatus");
    if (statusElement)
      statusElement.textContent =
        "Error loading payment configuration: " + error.message;
    showNotification(
      "Initialization Error",
      "Failed to load payment system: " + error.message,
      "error",
      5000
    );
  }
}

function loadStripeScript() {
  return new Promise((resolve, reject) => {
    if (document.querySelector('script[src="https://js.stripe.com/v3/"]')) {
      resolve();
      return;
    }
    const stripeScript = document.createElement("script");
    stripeScript.src = "https://js.stripe.com/v3/";
    stripeScript.async = true;
    stripeScript.onload = () => resolve();
    stripeScript.onerror = () => reject(new Error("Failed to load Stripe.js"));
    document.head.appendChild(stripeScript);
  });
}

// Återställ checkout-knappen
function resetCheckoutButton() {
  const checkoutBtn = document.getElementById("checkoutBtn");
  if (checkoutBtn) {
    checkoutBtn.disabled = cart.length === 0;
    checkoutBtn.textContent = "Complete the Purchase";
  }
}

// Lyssna på page show eller focus för att återställa knappen
window.addEventListener("pageshow", resetCheckoutButton);
window.addEventListener("focus", resetCheckoutButton);

window.addEventListener("resize", () => {
  setupCart();
  setupMobileCartToggles();
});

function initializeStoreLayout() {
  setupCart();
  setupMobileCartToggles();
  setupAddToCartButtons();
  setupPlaceholderImages();
}

function initializeSvgIcons() {
  if (typeof initSvgIcons === "function") {
    initSvgIcons();
  }
}

function setupPlaceholderImages() {
  const stylePreviews = document.querySelectorAll(".style-preview");
  stylePreviews.forEach((preview, index) => {
    const styles = ["minimal", "premium", "enterprise"];
    const style = styles[index % styles.length];
    preview.src = `/placeholder.svg?height=150&width=300&text=${style}`;
  });
}

function setupAddToCartButtons() {
  const addToCartButtons = document.querySelectorAll(".add-to-cart-btn");
  addToCartButtons.forEach((button) => {
    button.addEventListener("click", function () {
      const productId = this.getAttribute("data-product-id");

      // Handle Enterprise Subscription button separately
      if (productId === "sub-enterprise") {
        window.location.href = "/enterprise";
        return; // Stop further processing for this button
      }

      const productCard = document.querySelector(
        `.product-card[data-product-id="${productId}"]`
      );

      if (!productCard) return;

      const productName = productCard.querySelector("h3").textContent;
      const productType = productCard.getAttribute("data-product-type");
      const productPrice = Number.parseFloat(
        productCard.getAttribute("data-price")
      );

      addToCart(productId, productName, productType, productPrice);
      this.textContent = "Added to Cart";
      this.classList.add("in-cart");
      showNotification(
        "Product Added",
        `${productName} added to cart!`,
        "success",
        3000
      );
      setTimeout(() => {
        this.textContent = "Add to Cart";
        this.classList.remove("in-cart");
      }, 2000);
    });
  });

  const purchaseHistoryButton = document.querySelector(".view-history");
  if (purchaseHistoryButton) {
    purchaseHistoryButton.addEventListener("click", () => {
      localStorage.setItem("activeAccountSection", "settings-purchases");
      window.location.href = "/account";
    });
  }
}

function setupCart() {
  const shoppingCart = document.getElementById("shoppingCart");
  if (!shoppingCart) return;

  const checkoutBtn = document.getElementById("checkoutBtn");

  const cartParent = shoppingCart.parentNode;
  const newShoppingCart = shoppingCart.cloneNode(true);
  shoppingCart.remove();
  cartParent.appendChild(newShoppingCart);
  
  const newCheckoutBtn = newShoppingCart.querySelector("#checkoutBtn");

  loadCartFromStorage();

  if (newCheckoutBtn) {
    newCheckoutBtn.addEventListener("click", async function () {
      if (this.disabled) return;

      if (!stripe) {
        console.error("Stripe is not initialized. Cannot proceed.");
        showNotification(
          "Payment Error",
          "Payment system is not ready. Please try again shortly.",
          "error",
          5000
        );
        resetCheckoutButton();
        return;
      }

      try {
        this.disabled = true;
        this.textContent = "Processing...";
        showNotification("Processing", "Initiating checkout...", "info", 3000);

        const creditItems = cart.filter((item) => item.type === "Credit Pack");
        const subscriptionItems = cart.filter(
          (item) => item.type === "Subscription"
        );
        const episodeItems = cart.filter((item) => item.type === "Episode Pack");

        if (
          subscriptionItems.length > 1 ||
          (subscriptionItems[0] && subscriptionItems[0].quantity > 1)
        ) {
          showNotification(
            "Invalid Cart",
            "You can only purchase one subscription at a time.",
            "warning",
            5000
          );
          resetCheckoutButton();
          return;
        }

        if (
          creditItems.length === 0 &&
          subscriptionItems.length === 0 &&
          episodeItems.length === 0
        ) {
          showNotification(
            "Empty Cart",
            "Your cart is empty or contains unsupported items.",
            "warning",
            5000
          );
          resetCheckoutButton();
          return;
        }

        const items = [];

        if (creditItems.length > 0) {
          creditItems.forEach((item) => {
            const credits = getCreditsForProduct(item.id);
            items.push({
              productId: item.id,
              name: item.name,
              type: "credit",
              price: item.price.toFixed(2),
              quantity: item.quantity,
              credits: credits
            });
          });
        }

        if (subscriptionItems.length === 1) {
          const subscription = subscriptionItems[0];
          const plan = getPlanForProduct(subscription.id);
          items.push({
            productId: subscription.id,
            name: subscription.name,
            type: "subscription",
            price: subscription.price.toFixed(2),
            quantity: 1,
            plan: plan
          });
        }

        if (episodeItems.length > 0) {
          episodeItems.forEach((item) => {
            const episodeSlots = 1;
            items.push({
              productId: item.id,
              name: item.name,
              type: "episode",
              price: item.price.toFixed(2),
              quantity: item.quantity,
              episodeSlots: episodeSlots * item.quantity
            });
          });
        }

        const payload = { items };

        const checkoutUrl = apiBaseUrl
          ? `${apiBaseUrl}/create-checkout-session`
          : "/create-checkout-session";
        const response = await fetch(checkoutUrl, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
          credentials: "same-origin"
        });

        const contentType = response.headers.get("content-type");
        if (contentType && contentType.includes("text/html")) {
          showNotification(
            "Session Expired",
            "Your session has expired. Please log in again.",
            "error",
            5000
          );
          setTimeout(() => {
            window.location.href =
              "/signin?redirect=" + encodeURIComponent(window.location.pathname);
          }, 2000);
          resetCheckoutButton();
          return;
        }

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.error || "Failed to create checkout session");
        }

        const data = await response.json();
        if (data.sessionId) {
          await stripe.redirectToCheckout({ sessionId: data.sessionId });
          clearCart();
        } else {
          throw new Error(data.error || "Unknown error");
        }
      } catch (err) {
        console.error("Error during checkout:", err);
        showNotification(
          "Checkout Failed",
          "Unable to complete checkout. Please try again or contact support.",
          "error",
          5000
        );
        resetCheckoutButton();
      }
    });
  }
}

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

function getCreditsForProduct(productId) {
  switch (productId) {
    case "credit-basic":
      return 2500;
    case "credit-pro":
      return 5000;
    case "credit-premium":
      return 12000;
    case "credit-ultra":
      return 17000;
    default:
      return 0;
  }
}

function getPlanForProduct(productId) {
  switch (productId) {
    case "sub-standard":
      return "pro";
    case "sub-pro":
      return "studio";
    case "sub-enterprise":
      return "enterprise";
    default:
      return null;
  }
}

let cart = [];

function addToCart(productId, productName, productType, productPrice) {
  // Check if product already exists in cart
  const existingItemIndex = cart.findIndex((item) => item.id === productId);
  let itemAdded = false; // Flag to check if a new item was added or quantity increased

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
    itemAdded = true; // A new item was added
  }

  // Update cart UI
  updateCartUI();

  // Update notification badge
  updateCartNotification();

  // Save cart to localStorage
  saveCartToStorage();

  // --- Show notification ---
  const message = itemAdded
    ? `${productName} added to cart.`
    : `${productName} quantity increased.`;
  showNotification("Cart Updated", message, "success", 2000); // Show for 2 seconds
  // --- End notification ---
}

function removeFromCart(productId) {
  const itemIndex = cart.findIndex((item) => item.id === productId); // Find item before removing
  if (itemIndex === -1) return; // Item not found

  const removedItemName = cart[itemIndex].name; // Get name before removing

  cart = cart.filter((item) => item.id !== productId);

  // Update cart UI
  updateCartUI();

  // Update notification badge
  updateCartNotification();

  // Save cart to localStorage
  saveCartToStorage();

  // --- Show notification ---
  showNotification(
    "Cart Updated",
    `${removedItemName} removed from cart.`,
    "info",
    2000
  );
  // --- End notification ---
}

function updateItemQuantity(productId, newQuantity) {
  const itemIndex = cart.findIndex((item) => item.id === productId);

  if (itemIndex !== -1) {
    const itemName = cart[itemIndex].name; // Get name for notification
    let notificationMessage = "";

    if (newQuantity <= 0) {
      // Remove item if quantity is 0 or less
      removeFromCart(productId); // This already shows a notification
      return; // Exit early as removeFromCart handles UI/storage/notification
    } else {
      // Update quantity
      const oldQuantity = cart[itemIndex].quantity;
      cart[itemIndex].quantity = newQuantity;
      notificationMessage = `${itemName} quantity updated to ${newQuantity}.`;

      // Update cart UI
      updateCartUI();

      // Update notification badge
      updateCartNotification();

      // Save cart to localStorage
      saveCartToStorage();

      // --- Show notification ---
      showNotification("Cart Updated", notificationMessage, "info", 2000);
      // --- End notification ---
    }
  }
}

function clearCart() {
  const wasCartEmpty = cart.length === 0; // Check if cart was already empty
  cart = [];

  // Update cart UI
  updateCartUI();

  // Update notification badge
  updateCartNotification();

  // Save cart to localStorage
  saveCartToStorage();

  // --- Show notification (only if cart wasn't already empty) ---
  if (!wasCartEmpty) {
    showNotification(
      "Cart Cleared",
      "Your shopping cart is now empty.",
      "info",
      2000
    );
  }
  // --- End notification ---
}

function updateCartUI() {
  const cartItemsContainer = document.getElementById("cartItems");
  const cartItemCount = document.querySelector(".cart-item-count");
  const totalAmount = document.querySelector(".total-amount");
  const checkoutBtn = document.getElementById("checkoutBtn");

  cartItemsContainer.innerHTML = "";
  if (cart.length === 0) {
    cartItemsContainer.innerHTML =
      '<div class="empty-cart-message">Your cart is empty</div>';
    cartItemCount.textContent = "0 items";
    totalAmount.textContent = "$0.00";
    checkoutBtn.disabled = true;
  } else {
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

    const decreaseButtons = document.querySelectorAll(".decrease-btn");
    const increaseButtons = document.querySelectorAll(".increase-btn");
    const removeButtons = document.querySelectorAll(".remove-item-btn");

    decreaseButtons.forEach((button) => {
      button.addEventListener("click", function () {
        const productId = this.getAttribute("data-product-id");
        const item = cart.find((item) => item.id === productId);
        if (item) updateItemQuantity(productId, item.quantity - 1);
      });
    });

    increaseButtons.forEach((button) => {
      button.addEventListener("click", function () {
        const productId = this.getAttribute("data-product-id");
        const item = cart.find((item) => item.id === productId);
        if (item) updateItemQuantity(productId, item.quantity + 1);
      });
    });

    removeButtons.forEach((button) => {
      button.addEventListener("click", function () {
        const productId = this.getAttribute("data-product-id");
        removeFromCart(productId);
      });
    });

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
  initializeSvgIcons();
}

function updateCartNotification() {
  const cartNotification = document.getElementById("cartNotification");
  // --- Add null check ---
  if (!cartNotification) {
    console.warn(
      "Cart notification element with ID 'cartNotification' not found."
    );
    return; // Exit if element doesn't exist
  }
  // --- End null check ---

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

function setupMobileCartToggles() {
  const shoppingCart = document.getElementById("shoppingCart");
  const openCartArrowBtn = document.getElementById("openCartArrowBtn");
  const cartOverlay = document.getElementById("cartOverlay");

  if (!shoppingCart || !openCartArrowBtn || !cartOverlay) {
    // console.warn("Mobile cart toggle elements not all found. Skipping toggle setup.");
    return;
  }

  const openCart = () => {
    shoppingCart.classList.add("is-open");
    cartOverlay.classList.add("is-visible");
    // Prevent body scroll only on mobile when cart is a full overlay
    if (window.innerWidth <= 992) {
      document.body.style.overflow = 'hidden';
    }
  };

  const closeCart = () => {
    shoppingCart.classList.remove("is-open");
    cartOverlay.classList.remove("is-visible");
    document.body.style.overflow = ''; // Always restore body scroll
  };

  // Ensure listeners are fresh by removing old ones if any (optional, but good for re-calls)
  // However, simple re-adding is usually fine if elements are stable or replaced wholesale.
  openCartArrowBtn.onclick = openCart; // Use onclick to easily overwrite if called again
  cartOverlay.onclick = closeCart;

  // Event delegation for the close button inside the cart
  // This listener is attached to shoppingCart, so if shoppingCart itself is replaced, this needs re-attachment.
  // Given setupCart can replace shoppingCart, this also needs to be robust.
  // For simplicity, let's assume shoppingCart element reference is stable after setupCart call in initializeStoreLayout.
  // If setupCart replaces the #shoppingCart DOM element, then this delegated listener needs to be added to the *new* element.
  // The current structure calls setupMobileCartToggles AFTER setupCart, so `shoppingCart` should be the current one.
  
  // Remove previous listener to avoid duplicates if function is called multiple times on same element
  // This is a bit verbose. A more structured approach might use a flag or more complex listener management.
  const existingCloseHandler = shoppingCart.__closeCartHandler;
  if (existingCloseHandler) {
    shoppingCart.removeEventListener("click", existingCloseHandler);
  }
  shoppingCart.__closeCartHandler = (event) => {
    if (event.target.closest("#closeCartBtn")) {
      closeCart();
    }
  };
  shoppingCart.addEventListener("click", shoppingCart.__closeCartHandler);
}

function setupSubscriptionToggle() {
  const monthlyButton = document.querySelector(
    '.subscription-toggle button[data-period="monthly"]'
  );
  const yearlyButton = document.querySelector(
    '.subscription-toggle button[data-period="yearly"]'
  );
  const productCards = document.querySelectorAll(".product-card.subscription-card");

  if (!monthlyButton || !yearlyButton || !productCards) {
    console.warn("Subscription toggle elements not found.");
    return;
  }

  monthlyButton.addEventListener("click", () => {
    setActivePeriod("monthly");
  });

  yearlyButton.addEventListener("click", () => {
    setActivePeriod("yearly");
  });

  function setActivePeriod(period) {
    monthlyButton.classList.remove("active");
    yearlyButton.classList.remove("active");

    if (period === "monthly") {
      monthlyButton.classList.add("active");
    } else {
      yearlyButton.classList.add("active");
    }

    productCards.forEach((card) => {
      const monthlyPrice = card.dataset.monthlyPrice;
      const yearlyPrice = card.dataset.yearlyPrice;
      const priceElement = card.querySelector(".product-price .price-amount");
      const pricePeriod = card.querySelector(".product-price .price-period");
      const productName = card.querySelector(".product-name").textContent;
      const productFeaturesList = card.querySelector(".product-features .product-features-list");

      if (period === "monthly") {
        priceElement.textContent = `$${monthlyPrice}`;
        pricePeriod.textContent = "/month";
        if (productName === "Pro Subscription") {
          productFeaturesList.innerHTML = `
            <li>
              10,000 Credits at Month's Start<br />(resets monthly, no
              carry-over)
            </li>
            <li>3 Episode Slots / Month (Max. 5 Total Slots)</li>
            <li>
              Free Podcast Landing Page (Option to Host on Own Domain)
            </li>
          `;
        } else if (productName === "Studio Subscription") {
          productFeaturesList.innerHTML = `
            <li>
              20,000 Credits at Month's Start <br />(resets monthly,
              no carry-over)
            </li>
            <li>4 Episode Slots / Month (Max. 6 Total Slots)</li>
            <li>
              Free Podcast Landing Page (Option to Host on Own Domain)
            </li>
          `;
        }
      } else {
        priceElement.textContent = `$${yearlyPrice}`;
        pricePeriod.textContent = "/year";
        if (productName === "Pro Subscription") {
          productFeaturesList.innerHTML = `
            <li>
              10,000 Credits at Month's Start<br />(resets monthly, no
              carry-over)
            </li>
            <li>3 Episode Slots / Month (Max. 5 Total Slots)</li>
            <li>
              Free Podcast Landing Page (Option to Host on Own Domain)
            </li>
            <li>(Re-occuring Yearly Payment)</li>
            <li>(10 % Discount & One Month Free!)</li>
          `;
        } else if (productName === "Studio Subscription") {
          productFeaturesList.innerHTML = `
            <li>
              20,000 Credits at Month's Start <br />(resets monthly,
              no carry-over)
            </li>
            <li>4 Episode Slots / Month (Max. 6 Total Slots)</li>
            <li>
              Free Podcast Landing Page (Option to Host on Own Domain)
            </li>
            <li>(Re-occuring Yearly Payment)</li>
            <li>(20 % Discount & One Month Free!)</li>
          `;
        }
      }
    });
  }
}
