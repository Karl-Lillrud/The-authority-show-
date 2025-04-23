// SVG Icons for the store
const svgStore = {
  historyIcon: `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>`,

  creditsIcon: `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="16"/><line x1="8" y1="12" x2="16" y2="12"/></svg>`,

  creditSmallIcon: `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>`,

  creditMediumIcon: `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="5" width="20" height="14" rx="2"/><line x1="2" y1="10" x2="22" y2="10"/></svg>`,

  creditLargeIcon: `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="5" width="20" height="14" rx="2"/><path d="M16 14h.01"/><path d="M8 14h.01"/><path d="M12 14h.01"/><path d="M16 10h.01"/><path d="M8 10h.01"/><path d="M12 10h.01"/></svg>`,

  subscriptionProIcon: `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="m22 11-2 2-2-2"/><path d="M19 13V4"/></svg>`,

  subscriptionTeamIcon: `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>`,

  subscriptionEnterpriseIcon: `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 7h-9"/><path d="M14 17H5"/><circle cx="17" cy="17" r="3"/><circle cx="7" cy="7" r="3"/></svg>`,

  cartIcon: `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="21" r="1"/><circle cx="19" cy="21" r="1"/><path d="M2.05 2.05h2l2.66 12.42 Merchants and Markets of the Worlda2 2 0 0 0 2 1.58h9.78a2 2 0 0 0 1.95-1.57l1.65-7.43H5.12"/></svg>`,

  closeIcon: `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>`,

  episodeIcon: `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 3v18l6-6 6 6V3H5z"/><path d="M9 12h2"/><path d="M12 10h2"/><path d="M12 14h2"/></svg>`,

  removeIcon: `<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/><line x1="10" y1="11" x2="10" y2="17"/><line x1="14" y1="11" x2="14" y2="17"/></svg>`
};

function initSvgIcons() {
  // Initialize history and credits icons
  const historyIcon = document.querySelector(".history-icon");
  if (historyIcon) historyIcon.innerHTML = svgStore.historyIcon;

  const creditsIcon = document.querySelector(".credits-icon");
  if (creditsIcon) creditsIcon.innerHTML = svgStore.creditsIcon;

  // Initialize cart icon
  const cartIcon = document.querySelector(".cart-icon");
  if (cartIcon) cartIcon.innerHTML = svgStore.cartIcon;

  // Initialize close icon
  const closeIcon = document.querySelector(".close-icon");
  if (closeIcon) closeIcon.innerHTML = svgStore.closeIcon;

  // Initialize credit pack icons
  const creditSmallIcon = document.querySelector(".credit-small-icon");
  if (creditSmallIcon) creditSmallIcon.innerHTML = svgStore.creditSmallIcon;

  const creditMediumIcon = document.querySelector(".credit-medium-icon");
  if (creditMediumIcon) creditMediumIcon.innerHTML = svgStore.creditMediumIcon;

  const creditLargeIcon = document.querySelector(".credit-large-icon");
  if (creditLargeIcon) creditLargeIcon.innerHTML = svgStore.creditLargeIcon;

  // Initialize subscription icons
  const subscriptionProIcon = document.querySelector(".subscription-pro-icon");
  if (subscriptionProIcon)
    subscriptionProIcon.innerHTML = svgStore.subscriptionProIcon;

  const subscriptionTeamIcon = document.querySelector(
    ".subscription-team-icon"
  );
  if (subscriptionTeamIcon)
    subscriptionTeamIcon.innerHTML = svgStore.subscriptionTeamIcon;

  const subscriptionEnterpriseIcon = document.querySelector(
    ".subscription-enterprise-icon"
  );
  if (subscriptionEnterpriseIcon)
    subscriptionEnterpriseIcon.innerHTML = svgStore.subscriptionEnterpriseIcon;

  // Initialize episode pack icon
  const episodeIcon = document.querySelector(".episode-icon");
  if (episodeIcon) episodeIcon.innerHTML = svgStore.episodeIcon;

  // Initialize remove icons for cart items
  const removeIcons = document.querySelectorAll(".remove-icon");
  removeIcons.forEach((icon) => {
    icon.innerHTML = svgStore.removeIcon;
  });
}
