import { api, getAppearance, requireLogin, toggleAppearance } from "./common.js";

const appearanceToggleBtn = document.getElementById("appearanceToggleBtn");
const adminQueueLink = document.getElementById("adminQueueLink");
const profileLink = document.getElementById("profileLink");
const logoutBtn = document.getElementById("logoutBtn");
const mapSearchInput = document.getElementById("mapSearchInput");
const mapSearchBtn = document.getElementById("mapSearchBtn");
const mapCount = document.getElementById("mapCount");
const mapStatus = document.getElementById("mapStatus");
const mapCarousel = document.getElementById("mapCarousel");
const useLocationBtn = document.getElementById("useLocationBtn");
const mapPrevBtn = document.getElementById("mapPrevBtn");
const mapNextBtn = document.getElementById("mapNextBtn");
const initialParams = new URLSearchParams(window.location.search);
const initialQuery = (initialParams.get("q") || "").trim();
const initialRestaurantId = Number(initialParams.get("restaurant_id") || "0");

const me = await requireLogin();
if (adminQueueLink) {
  adminQueueLink.classList.toggle("hidden", me.role !== "admin");
}
if (profileLink && me.role === "admin") {
  profileLink.classList.add("hidden");
}

let map;
let markersLayer;
let restaurants = [];
let filteredRestaurants = [];
let activeRestaurantId = null;
let userLocation = null;
let carouselIndex = 0;
const carouselPageSize = 3;

function syncAppearanceToggle() {
  if (!appearanceToggleBtn) return;
  appearanceToggleBtn.innerHTML = '<span class="appearance-symbol" aria-hidden="true">&#9681;</span>';
  appearanceToggleBtn.setAttribute(
    "aria-label",
    getAppearance() === "dark" ? "Switch to light mode" : "Switch to dark mode",
  );
}

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (char) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  }[char]));
}

function renderLogo(logoUrl, label) {
  const initials = String(label || "")
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0])
    .join("")
    .toUpperCase() || "IR";

  if (logoUrl) {
    return `<img src="${escapeHtml(logoUrl)}" alt="${escapeHtml(label)} logo" class="logo-mark brand-logo-image" />`;
  }

  return `<div class="logo-mark brand-logo-fallback">${escapeHtml(initials)}</div>`;
}

function renderPinLogo(logoUrl, label) {
  const initials = String(label || "")
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0])
    .join("")
    .toUpperCase() || "IR";

  if (logoUrl) {
    return `<img src="${escapeHtml(logoUrl)}" alt="${escapeHtml(label)} logo" class="map-pin-logo-image" />`;
  }

  return `<div class="map-pin-logo-fallback">${escapeHtml(initials)}</div>`;
}

function createRestaurantIcon(restaurant) {
  return L.divIcon({
    className: "map-logo-pin-wrapper",
    html: `
      <div class="map-logo-pin ${restaurant.restaurant_id === activeRestaurantId ? "map-logo-pin-active" : ""}">
        <div class="map-logo-pin-inner">
          ${renderPinLogo(restaurant.logo_url, restaurant.brand_name || restaurant.name)}
        </div>
      </div>
    `,
    iconSize: [46, 58],
    iconAnchor: [23, 58],
    popupAnchor: [0, -52],
  });
}

function haversineMiles(lat1, lon1, lat2, lon2) {
  const toRad = (value) => (value * Math.PI) / 180;
  const earthRadiusMiles = 3958.8;
  const dLat = toRad(lat2 - lat1);
  const dLon = toRad(lon2 - lon1);
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLon / 2) ** 2;
  return 2 * earthRadiusMiles * Math.asin(Math.sqrt(a));
}

function normalizeCoordinate(value) {
  const numeric = Number(value);
  return Number.isFinite(numeric) ? numeric : null;
}

function markerPopupHtml(restaurant) {
  const avgRating = restaurant.avg_rating == null ? "No ratings yet" : restaurant.avg_rating.toFixed(1);
  const reviewLabel = `${restaurant.review_count} review${restaurant.review_count === 1 ? "" : "s"}`;
  const actions = [];

  if (restaurant.menu_url) {
    actions.push(`<a href="${escapeHtml(restaurant.menu_url)}" class="menu-link-btn" target="_blank" rel="noopener noreferrer">View menu</a>`);
  }
  if (restaurant.website_url) {
    actions.push(`<a href="${escapeHtml(restaurant.website_url)}" class="menu-link-btn menu-link-btn-soft" target="_blank" rel="noopener noreferrer">Website</a>`);
  }
  if (restaurant.ordering_url) {
    actions.push(`<a href="${escapeHtml(restaurant.ordering_url)}" class="menu-link-btn menu-link-btn-soft" target="_blank" rel="noopener noreferrer">Order online</a>`);
  }

  return `
    <div class="map-popup">
      <div class="brand-header">
        ${renderLogo(restaurant.logo_url, restaurant.brand_name || restaurant.name)}
        <div>
          <div class="title" style="margin-bottom: 4px;">${escapeHtml(restaurant.name)}</div>
          <div class="muted">${escapeHtml(restaurant.brand_name || "")}</div>
        </div>
      </div>
      <div class="muted" style="margin-top: 8px;">${escapeHtml([restaurant.address_line1, restaurant.city, restaurant.postcode].filter(Boolean).join(", "))}</div>
      <div class="row" style="margin-top: 10px;">
        <div class="pill pill-rating">FHRS: ${escapeHtml(String(restaurant.hygiene_rating ?? "N/A"))}</div>
        <div class="pill pill-rating"><span class="rating-star">&#9733;</span>${escapeHtml(avgRating)}</div>
        <div class="pill pill-rating">${escapeHtml(reviewLabel)}</div>
      </div>
      ${actions.length ? `<div class="row" style="margin-top: 10px;">${actions.join("")}</div>` : ""}
    </div>
  `;
}

function initMap() {
  map = L.map("mapCanvas", {
    zoomControl: true,
    scrollWheelZoom: true,
  }).setView([51.4545, -2.5879], 12);

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
  }).addTo(map);

  markersLayer = L.layerGroup().addTo(map);
}

function renderMarkers(items) {
  markersLayer.clearLayers();

  const bounds = [];
  for (const restaurant of items) {
    if (restaurant.latitude == null || restaurant.longitude == null) continue;

    const marker = L.marker([restaurant.latitude, restaurant.longitude], {
      icon: createRestaurantIcon(restaurant),
    });
    marker.bindPopup(markerPopupHtml(restaurant));
    marker.on("click", () => {
      activeRestaurantId = restaurant.restaurant_id;
      renderMarkers(filteredRestaurants);
      renderCarousel();
    });
    marker.addTo(markersLayer);
    bounds.push([restaurant.latitude, restaurant.longitude]);
  }

  if (userLocation) {
    const userMarker = L.circleMarker([userLocation.latitude, userLocation.longitude], {
      radius: 9,
      color: "#8e1f23",
      weight: 2,
      fillColor: "#e6a8a8",
      fillOpacity: 0.95,
    });
    userMarker.bindPopup("You are here");
    userMarker.addTo(markersLayer);
    bounds.push([userLocation.latitude, userLocation.longitude]);
  }

  if (bounds.length) {
    map.fitBounds(bounds, { padding: [36, 36] });
  }
}

function getDistanceLabel(restaurant) {
  if (restaurant.distance_miles == null) return "Distance unavailable";
  return `${restaurant.distance_miles.toFixed(1)} mi away`;
}

function carouselCardHtml(restaurant) {
  const avgRating = restaurant.avg_rating == null ? "No ratings yet" : restaurant.avg_rating.toFixed(1);
  const isActive = restaurant.restaurant_id === activeRestaurantId ? " map-restaurant-card-active" : "";

  return `
    <article class="map-restaurant-card${isActive}" data-restaurant-id="${restaurant.restaurant_id}">
      <div class="brand-header">
        ${renderLogo(restaurant.logo_url, restaurant.brand_name || restaurant.name)}
        <div>
          <div class="title">${escapeHtml(restaurant.name)}</div>
          <div class="muted">${escapeHtml(restaurant.brand_name || "")}</div>
        </div>
      </div>
      <div class="muted map-result-address">${escapeHtml([restaurant.address_line1, restaurant.city, restaurant.postcode].filter(Boolean).join(", "))}</div>
      <div class="row" style="margin-top: 10px;">
        <div class="pill pill-rating">${escapeHtml(getDistanceLabel(restaurant))}</div>
        ${restaurant.cuisine_name ? `<div class="pill pill-rating">${escapeHtml(restaurant.cuisine_name)}</div>` : ""}
      </div>
      <div class="row" style="margin-top: 10px;">
        <div class="pill pill-rating"><span class="rating-star">&#9733;</span>${escapeHtml(avgRating)}</div>
        <div class="pill pill-rating">FHRS: ${escapeHtml(String(restaurant.hygiene_rating ?? "N/A"))}</div>
      </div>
    </article>
  `;
}

function renderCarousel() {
  const pageCount = Math.max(1, Math.ceil(filteredRestaurants.length / carouselPageSize));
  if (carouselIndex >= pageCount) carouselIndex = 0;
  const start = carouselIndex * carouselPageSize;
  const visible = filteredRestaurants.slice(start, start + carouselPageSize);

  mapCount.textContent = `${filteredRestaurants.length} mapped restaurant${filteredRestaurants.length === 1 ? "" : "s"}`;
  mapCarousel.innerHTML = visible.length
    ? visible.map(carouselCardHtml).join("")
    : '<div class="muted">No mapped restaurants match that search yet.</div>';

  if (mapPrevBtn) mapPrevBtn.disabled = pageCount <= 1;
  if (mapNextBtn) mapNextBtn.disabled = pageCount <= 1;
}

function sortRestaurants(items) {
  const sorted = items.slice();
  if (userLocation) {
    for (const restaurant of sorted) {
      const latitude = normalizeCoordinate(restaurant.latitude);
      const longitude = normalizeCoordinate(restaurant.longitude);
      restaurant.latitude = latitude;
      restaurant.longitude = longitude;
      restaurant.distance_miles = latitude == null || longitude == null
        ? null
        : haversineMiles(
            userLocation.latitude,
            userLocation.longitude,
            latitude,
            longitude,
          );
    }
    sorted.sort((a, b) => {
      const aDistance = a.distance_miles ?? Number.POSITIVE_INFINITY;
      const bDistance = b.distance_miles ?? Number.POSITIVE_INFINITY;
      return aDistance - bDistance || a.name.localeCompare(b.name);
    });
    const nearest = sorted.find((restaurant) => restaurant.distance_miles != null);
    mapStatus.textContent = nearest
      ? `Showing restaurants from nearest to furthest. Closest right now: ${nearest.name} (${nearest.distance_miles.toFixed(1)} mi).`
      : "Showing restaurants from nearest to furthest based on your current location.";
  } else {
    for (const restaurant of sorted) {
      restaurant.distance_miles = null;
    }
    sorted.sort((a, b) => a.name.localeCompare(b.name));
    mapStatus.textContent = "Enable location to reorder the cards from nearest to furthest.";
  }
  return sorted;
}

function applySearch() {
  const q = (mapSearchInput.value || "").trim().toLowerCase();
  const baseItems = restaurants.filter((restaurant) => {
    if (!q) return true;
    const haystack = [
      restaurant.name,
      restaurant.brand_name,
      restaurant.address_line1,
      restaurant.city,
      restaurant.postcode,
      restaurant.cuisine_name,
    ].join(" ").toLowerCase();
    return haystack.includes(q);
  });

  filteredRestaurants = sortRestaurants(baseItems);
  carouselIndex = 0;
  renderMarkers(filteredRestaurants);
  renderCarousel();
}

function focusNearestRestaurant() {
  const nearest = filteredRestaurants.find((restaurant) => restaurant.distance_miles != null);
  if (!nearest) return;
  focusRestaurant(nearest.restaurant_id);
}

function focusRestaurant(restaurantId) {
  const restaurant = filteredRestaurants.find((item) => item.restaurant_id === restaurantId);
  if (!restaurant || restaurant.latitude == null || restaurant.longitude == null) return;

  activeRestaurantId = restaurant.restaurant_id;
  renderCarousel();
  map.setView([restaurant.latitude, restaurant.longitude], 16, { animate: true });

  markersLayer.eachLayer((layer) => {
    const latLng = layer.getLatLng?.();
    if (!latLng) return;
    if (latLng.lat === restaurant.latitude && latLng.lng === restaurant.longitude) {
      layer.openPopup();
    }
  });
}

function applyInitialMapState() {
  if (initialQuery && mapSearchInput) {
    mapSearchInput.value = initialQuery;
    applySearch();
  }

  if (initialRestaurantId > 0) {
    const exactMatch = filteredRestaurants.find((item) => item.restaurant_id === initialRestaurantId);
    if (exactMatch) {
      focusRestaurant(initialRestaurantId);
      return;
    }
  }

  if (initialQuery && filteredRestaurants.length === 1) {
    focusRestaurant(filteredRestaurants[0].restaurant_id);
  }
}

mapCarousel.addEventListener("click", (event) => {
  const card = event.target.closest("[data-restaurant-id]");
  if (!card) return;
  focusRestaurant(Number(card.dataset.restaurantId || "0"));
});

mapSearchInput.addEventListener("input", applySearch);
mapSearchInput.addEventListener("keydown", (event) => {
  if (event.key !== "Enter") return;
  event.preventDefault();
  applySearch();
});

if (mapSearchBtn) {
  mapSearchBtn.addEventListener("click", applySearch);
}

if (mapPrevBtn) {
  mapPrevBtn.addEventListener("click", () => {
    const pageCount = Math.max(1, Math.ceil(filteredRestaurants.length / carouselPageSize));
    carouselIndex = (carouselIndex - 1 + pageCount) % pageCount;
    renderCarousel();
  });
}

if (mapNextBtn) {
  mapNextBtn.addEventListener("click", () => {
    const pageCount = Math.max(1, Math.ceil(filteredRestaurants.length / carouselPageSize));
    carouselIndex = (carouselIndex + 1) % pageCount;
    renderCarousel();
  });
}

if (useLocationBtn) {
  useLocationBtn.addEventListener("click", () => {
    if (!navigator.geolocation) {
      mapStatus.textContent = "This browser does not support location access.";
      return;
    }

    useLocationBtn.disabled = true;
    useLocationBtn.textContent = "Locating...";
    mapStatus.textContent = "Trying to get your location...";

    navigator.geolocation.getCurrentPosition(
      (position) => {
        userLocation = {
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
        };
        useLocationBtn.disabled = false;
        useLocationBtn.textContent = "Refresh my location";
        applySearch();
        focusNearestRestaurant();
      },
      () => {
        useLocationBtn.disabled = false;
        useLocationBtn.textContent = "Use my location";
        mapStatus.textContent = "Location was blocked or unavailable, so the cards are staying in default order.";
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 300000,
      },
    );
  });
}

logoutBtn.addEventListener("click", async () => {
  await api("/auth/logout", { method: "POST" });
  window.location.href = "/login";
});

if (appearanceToggleBtn) {
  appearanceToggleBtn.addEventListener("click", () => {
    toggleAppearance();
    syncAppearanceToggle();
  });
}

async function init() {
  syncAppearanceToggle();
  initMap();
  const data = await api("/map-restaurants");
  restaurants = (data.items || [])
    .map((item) => ({
      ...item,
      latitude: normalizeCoordinate(item.latitude),
      longitude: normalizeCoordinate(item.longitude),
    }))
    .filter((item) => item.latitude != null && item.longitude != null);
  filteredRestaurants = sortRestaurants(restaurants);
  renderMarkers(filteredRestaurants);
  renderCarousel();
  applyInitialMapState();
}

init();
