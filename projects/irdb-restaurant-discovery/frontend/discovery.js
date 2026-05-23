import { api, requireLogin, getAppearance, toggleAppearance } from "./common.js";

await requireLogin();

const me = await api("/auth/me");
const adminLink = document.getElementById("adminQueueLink");
const profileLink = document.getElementById("profileLink");
if (adminLink) {
  if (me.role === "admin") adminLink.classList.remove("hidden");
  else adminLink.classList.add("hidden");
}
if (profileLink && me.role === "admin") {
  profileLink.classList.add("hidden");
}

const list = document.getElementById("list");
const qEl = document.getElementById("q");
const pageInfo = document.getElementById("pageInfo");
const cuisineList = document.getElementById("cuisineList");
const sortOptions = document.getElementById("sortOptions");
const hasMenuOnlyEl = document.getElementById("hasMenuOnly");
const featuredStage = document.getElementById("featuredStage");
const featuredBand = document.querySelector(".featured-band");
const filterBtn = document.getElementById("filterBtn");
const filterPopover = document.getElementById("filterPopover");
const applyFiltersBtn = document.getElementById("applyFiltersBtn");
const appearanceToggleBtn = document.getElementById("appearanceToggleBtn");

const restaurantModal = document.getElementById("restaurantModal");
const modalBody = document.getElementById("modalBody");
const modalBackdrop = document.getElementById("modalBackdrop");
const closeModalBtn = document.getElementById("closeModalBtn");

let page = 1;
let pages = 1;
let currentCuisineId = "";
let currentSort = "name_asc";
let featuredItems = [];
let featuredIndex = 0;
let featuredTimer = null;
let featuredTransitionTimer = null;

function syncAppearanceToggle() {
  if (!appearanceToggleBtn) return;
  appearanceToggleBtn.innerHTML = '<span class="appearance-symbol" aria-hidden="true">&#9681;</span>';
  appearanceToggleBtn.setAttribute(
    "aria-label",
    getAppearance() === "dark" ? "Switch to light mode" : "Switch to dark mode",
  );
}

function syncFeaturedVisibility() {
  if (!featuredBand || !qEl) return;
  const hasSearch = qEl.value.trim().length > 0;
  const hasActiveSort = currentSort !== "name_asc";
  const hasCuisineFilter = currentCuisineId !== "";
  featuredBand.classList.toggle("hidden", hasSearch || hasActiveSort || hasCuisineFilter);
}

async function loadCuisines() {
  if (!cuisineList) return;

  const data = await api("/cuisines");
  const items = data.items || [];

  cuisineList.innerHTML = '<button type="button" class="filter-list-item active" data-cuisine-id="">All cuisines</button>';

  for (const cuisine of items) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "filter-list-item";
    button.dataset.cuisineId = String(cuisine.cuisine_id);
    button.textContent = cuisine.name || "Unknown";
    cuisineList.appendChild(button);
  }
}

async function load() {
  list.innerHTML = '<div class="muted">Loading...</div>';

  const q = qEl.value.trim();
  const hasMenu = hasMenuOnlyEl && hasMenuOnlyEl.checked ? "1" : "0";
  syncFeaturedVisibility();

  const data = await api(
    `/restaurants?q=${encodeURIComponent(q)}&cuisine_id=${encodeURIComponent(currentCuisineId)}&page=${page}&per_page=30&sort=${encodeURIComponent(currentSort)}&has_menu=${hasMenu}`
  );

  pages = data.pages || 1;
  pageInfo.textContent = `Page ${data.page} of ${pages} - ${data.total} total`;

  list.innerHTML = "";

  for (const restaurant of data.items) {
    const card = document.createElement("div");
    card.className = "card restaurant-card-clickable";

    const logoHtml = renderLogo(restaurant.logo_url, restaurant.name, "card");
    const ratingText = restaurant.avg_rating == null ? "No ratings yet" : `${Number(restaurant.avg_rating).toFixed(1)}`;
    const menuBadge = restaurant.has_menu ? '<div class="pill pill-rating">Menu available</div>' : "";

    card.innerHTML = `
      <div class="brand-header">
        ${logoHtml}
        <div>
          <div class="title">${escapeHtml(restaurant.name)}</div>
          <div class="muted">
            ${restaurant.branch_count === 1 ? "1 branch" : `${escapeHtml(String(restaurant.branch_count || 0))} branches`}
            ${restaurant.city ? " &bull; " + escapeHtml(restaurant.city) : ""}
            ${restaurant.postcode ? " &bull; " + escapeHtml(restaurant.postcode) : ""}
          </div>
          ${restaurant.cuisine_name ? `<div class="muted" style="margin-top:8px;">Cuisine: ${escapeHtml(restaurant.cuisine_name)}</div>` : ""}
        </div>
      </div>

      <div class="row" style="margin-top:10px; gap:10px; flex-wrap:wrap;">
        <div class="pill pill-rating">FHRS: ${escapeHtml(String(restaurant.hygiene_rating ?? "N/A"))}</div>
        <div class="pill pill-rating"><span class="rating-star">&#9733;</span>${escapeHtml(ratingText)}</div>
        ${menuBadge}
      </div>
    `;

    card.addEventListener("click", async () => {
      await openRestaurantGroupModal(restaurant.brand_name || restaurant.name);
    });

    list.appendChild(card);
  }
}

async function loadFeatured() {
  if (!featuredStage) return;

  featuredStage.innerHTML = '<div class="featured-empty muted">Loading featured restaurants...</div>';

  try {
    const data = await api("/restaurants/featured");
    featuredItems = data.items || [];
    featuredIndex = 0;
    renderFeatured(false);
    startFeaturedRotation();
  } catch (error) {
    featuredStage.innerHTML = `<div class="featured-empty muted">Could not load featured restaurants: ${escapeHtml(error.message)}</div>`;
  }
}

function startFeaturedRotation() {
  if (featuredTimer) {
    clearInterval(featuredTimer);
  }

  if (getFeaturedPageCount() <= 1) return;

  featuredTimer = window.setInterval(() => {
    goToFeatured((featuredIndex + 1) % getFeaturedPageCount());
  }, 5200);
}

function goToFeatured(nextIndex) {
  if (!featuredItems.length) return;

  const pageCount = getFeaturedPageCount();
  const normalizedIndex = (nextIndex + pageCount) % pageCount;
  featuredIndex = normalizedIndex;

  if (!featuredStage) return;

  featuredStage.classList.remove("is-visible");
  featuredStage.classList.add("is-transitioning");

  if (featuredTransitionTimer) {
    clearTimeout(featuredTransitionTimer);
  }

  featuredTransitionTimer = window.setTimeout(() => {
    renderFeatured(true);
  }, 170);
}

function renderFeatured(animateIn = true) {
  if (!featuredStage) return;

  if (!featuredItems.length) {
    if (featuredTimer) {
      clearInterval(featuredTimer);
      featuredTimer = null;
    }
    featuredStage.innerHTML = '<div class="featured-empty muted">No top-rated restaurants are available yet.</div>';
    return;
  }

  const visibleItems = featuredItems.slice(featuredIndex * 2, featuredIndex * 2 + 2);
  const pageCount = getFeaturedPageCount();

  featuredStage.innerHTML = `
    <article class="featured-slide">
      <div class="featured-grid">
        ${visibleItems.map((item, itemOffset) => renderFeaturedCard(item, itemOffset)).join("")}
      </div>

      <div class="featured-controls">
        <div class="featured-dots">
          ${Array.from({ length: pageCount }, (_unused, index) => `
            <button
              type="button"
              class="featured-dot ${index === featuredIndex ? "active" : ""}"
              data-featured-index="${index}"
              aria-label="Go to featured restaurant ${index + 1}"
            ></button>
          `).join("")}
        </div>

        <div class="featured-nav">
          <button type="button" class="featured-secondary" id="featuredPrevBtn">Prev</button>
          <button type="button" id="featuredNextBtn">Next</button>
        </div>
      </div>
    </article>
  `;

  featuredStage.classList.remove("is-transitioning");
  if (animateIn) {
    requestAnimationFrame(() => {
      featuredStage.classList.add("is-visible");
    });
  } else {
    featuredStage.classList.add("is-visible");
  }
}

function renderFeaturedCard(item, itemOffset) {
  const ratingText = item.avg_rating == null ? "No ratings yet" : Number(item.avg_rating).toFixed(1);
  const cuisineText = item.cuisine_name || "Various";
  const reviewCount = Number(item.review_count || 0);
  const branchCount = Number(item.branch_count || 0);
  const summaryParts = [
    `${branchCount} ${branchCount === 1 ? "branch" : "branches"} across Bristol`,
    `Cuisine: ${cuisineText}`,
    item.hygiene_rating == null ? "FHRS unavailable" : `FHRS ${item.hygiene_rating}`,
  ];
  const summary = summaryParts.join(" / ");
  const featuredReviews = (item.reviews || []).slice(0, 2);
  const reviewsHtml = featuredReviews.length
    ? `
      <div class="featured-review-strip">
        ${featuredReviews.map((review) => `
          <article class="featured-review">
            <div class="featured-review-head">
              <span class="featured-review-rating"><span class="rating-star">&#9733;</span>${escapeHtml(String(review.stars))}</span>
              <span class="muted">${escapeHtml(review.user_full_name || "Guest")}</span>
            </div>
            <p>${escapeHtml(trimReview(review.review_text || ""))}</p>
          </article>
        `).join("")}
      </div>
    `
    : "";
  const cardClasses = item.logo_url ? "featured-card has-logo-bg" : "featured-card";
  const cardStyle = item.logo_url
    ? ` style="--featured-bg-image: url('${escapeHtml(item.logo_url)}');"`
    : "";

  return `
    <article class="${cardClasses}"${cardStyle} data-featured-open="${featuredIndex * 2 + itemOffset}" role="button" tabindex="0" aria-label="Open featured restaurant details">
      <div>
        <div class="featured-spot">Top rated pick</div>
        <h3 class="featured-title">${escapeHtml(item.name || "Restaurant")}</h3>
        <div class="featured-meta">
          <div class="featured-pill"><span class="rating-star">&#9733;</span>${escapeHtml(ratingText)}</div>
          <div class="featured-pill">${escapeHtml(String(reviewCount))} review${reviewCount === 1 ? "" : "s"}</div>
          <div class="featured-pill">Menu available</div>
        </div>
        <p class="featured-summary">${escapeHtml(summary)}</p>
        ${reviewsHtml}
        <div class="featured-actions">
          <button type="button" data-featured-open-btn="${featuredIndex * 2 + itemOffset}">View full details</button>
        </div>
      </div>

      <div class="featured-brand-mark">
        ${renderLogo(item.logo_url, item.name, "brand")}
      </div>
    </article>
  `;
}

function getFeaturedPageCount() {
  return Math.max(1, Math.ceil(featuredItems.length / 2));
}

async function openRestaurantGroupModal(brandName) {
  restaurantModal.classList.remove("hidden");
  modalBody.innerHTML = '<div class="muted">Loading...</div>';

  try {
    const data = await api(`/restaurant-groups/${encodeURIComponent(brandName)}`);
    renderRestaurantGroupModal(data);
  } catch (error) {
    modalBody.innerHTML = `<div class="muted">Could not load restaurant group: ${escapeHtml(error.message)}</div>`;
  }
}

function closeRestaurantModal() {
  restaurantModal.classList.add("hidden");
}

function renderRestaurantGroupModal(data) {
  const brandName = data.brand_name || "Restaurant";
  const branches = data.branches || [];
  const logoHtml = renderLogo(data.logo_url, brandName, "brand");

  modalBody.innerHTML = `
    <div class="brand-header" style="margin-bottom:12px;">
      ${logoHtml}
      <div>
        <h2 style="margin-top:0; margin-bottom:6px;">${escapeHtml(brandName)}</h2>
        <div class="muted">${branches.length} ${branches.length === 1 ? "branch" : "branches"}</div>
      </div>
    </div>

    <div style="margin-top:18px;">
      ${
        branches.length
          ? branches.map(renderBranchCard).join("")
          : '<div class="muted">No branches found.</div>'
      }
    </div>
  `;

  wireBranchActions(branches);
}

function renderBranchCard(branch) {
  const avg = branch.rating?.avg == null ? "-" : Number(branch.rating.avg).toFixed(1);
  const reviewCount = branch.rating?.review_count || 0;
  const reviews = branch.reviews || [];
  const mapUrl = buildMapUrl(branch);

  const menuHtml = branch.menu_url
    ? `<a href="${escapeHtml(branch.menu_url)}" target="_blank" rel="noopener noreferrer" class="menu-link-btn">
         ${branch.menu_source_type === "pdf" ? "View Menu PDF" : "View Menu"}
       </a>`
    : '<span class="muted">No menu link yet</span>';

  const websiteHtml = branch.website_url
    ? `<a href="${escapeHtml(branch.website_url)}" target="_blank" rel="noopener noreferrer" class="menu-link-btn">Website</a>`
    : "";

  const orderingHtml = branch.ordering_url
    ? `<a href="${escapeHtml(branch.ordering_url)}" target="_blank" rel="noopener noreferrer" class="menu-link-btn">Order Online</a>`
    : "";
  const mapHtml = mapUrl
    ? `<a href="${escapeHtml(mapUrl)}" target="_blank" rel="noopener noreferrer" class="menu-link-btn menu-link-btn-soft">View on map</a>`
    : "";

  const phoneHtml = branch.phone
    ? `<div><strong>Phone:</strong> ${escapeHtml(branch.phone)}</div>`
    : "";

  const emailHtml = branch.email
    ? `<div><strong>Email:</strong> ${escapeHtml(branch.email)}</div>`
    : "";

  const reviewsHtml = reviews.length
    ? `
        <div style="margin-top:16px;">
          <div class="title" style="font-size:1rem;">Recent reviews</div>
        ${reviews.map((review) => `
          <div class="card modal-review-card" style="margin-top:10px; margin-bottom:0; box-shadow:none;">
            <div class="row" style="justify-content:space-between; margin-top:0;">
              <div class="pill pill-rating"><span class="rating-star">&#9733;</span> ${escapeHtml(String(review.stars))}/5</div>
              <div class="muted">${escapeHtml(review.user_full_name || "User")}</div>
            </div>
            <div style="margin-top:10px; line-height:1.6;">${escapeHtml(review.review_text || "")}</div>
            ${review.reply ? `
              <div class="card modal-review-card" style="margin-top:12px; margin-bottom:0; box-shadow:none;">
                <div class="muted">Restaurant reply${review.reply.is_edited ? " (edited)" : ""}</div>
                <div style="margin-top:8px; line-height:1.7;">${escapeHtml(review.reply.reply_text || "")}</div>
              </div>
            ` : ""}
          </div>
        `).join("")}
      </div>
    `
    : '<div style="margin-top:16px;" class="muted">No published written reviews yet.</div>';

  return `
    <div class="card" style="margin-top:12px;">
      <div class="row" style="justify-content:space-between; gap:12px; align-items:flex-start;">
        <div>
          <div class="title">${escapeHtml(branch.name || branch.brand_name || "Branch")}</div>
          <div class="muted" style="margin-top:4px;">
            ${escapeHtml(branch.address_line1 || "")}
            ${branch.city ? ", " + escapeHtml(branch.city) : ""}
            ${branch.postcode ? " " + escapeHtml(branch.postcode) : ""}
          </div>
        </div>
        <div class="muted">${escapeHtml(branch.price_level || "")}</div>
      </div>

      <div class="row" style="margin-top:12px; gap:10px; flex-wrap:wrap;">
        <div class="pill pill-rating">FHRS: ${escapeHtml(String(branch.hygiene_rating ?? "N/A"))}</div>
        <div class="pill pill-rating"><span class="rating-star">&#9733;</span> ${escapeHtml(avg)}</div>
        <div class="pill pill-rating">${escapeHtml(String(reviewCount))} review${reviewCount === 1 ? "" : "s"}</div>
        ${branch.menu_verified ? '<div class="pill pill-rating">Menu verified</div>' : ""}
      </div>

      ${branch.description ? `<p style="margin-top:12px;">${escapeHtml(branch.description)}</p>` : ""}

      <div style="margin-top:12px;" class="muted">
        ${phoneHtml}
        ${emailHtml}
      </div>

      ${reviewsHtml}

      <div class="row" style="margin-top:12px; gap:10px; flex-wrap:wrap;">
        <button id="branchFavBtn_${branch.restaurant_id}" type="button">Save</button>
        <button id="branchReviewBtn_${branch.restaurant_id}" type="button">Write review</button>
        ${mapHtml}
        ${menuHtml}
        ${websiteHtml}
        ${orderingHtml}
      </div>

      <div id="branchReviewBox_${branch.restaurant_id}" class="reviewBox hidden" style="margin-top:12px;">
        <label>Rating (1-5)</label>
        <input id="branchRating_${branch.restaurant_id}" type="number" min="1" max="5" value="5" />

        <label>Comment</label>
        <textarea id="branchComment_${branch.restaurant_id}" rows="3" placeholder="Quick review..."></textarea>

        <div class="row" style="margin-top:8px;">
          <button id="branchSubmitReview_${branch.restaurant_id}" type="button">Submit for moderation</button>
          <div id="branchStatus_${branch.restaurant_id}" class="muted"></div>
        </div>
      </div>
    </div>
  `;
}

function wireBranchActions(branches) {
  for (const branch of branches) {
    const favBtn = document.getElementById(`branchFavBtn_${branch.restaurant_id}`);
    const reviewBtn = document.getElementById(`branchReviewBtn_${branch.restaurant_id}`);
    const reviewBox = document.getElementById(`branchReviewBox_${branch.restaurant_id}`);
    const submitBtn = document.getElementById(`branchSubmitReview_${branch.restaurant_id}`);
    const statusEl = document.getElementById(`branchStatus_${branch.restaurant_id}`);
    const ratingEl = document.getElementById(`branchRating_${branch.restaurant_id}`);
    const commentEl = document.getElementById(`branchComment_${branch.restaurant_id}`);

    if (favBtn) {
      favBtn.addEventListener("click", async () => {
        try {
          const out = await api(`/restaurants/${branch.restaurant_id}/favorite`, { method: "POST" });
          favBtn.textContent = out.favorited ? "Saved" : "Save";
        } catch (error) {
          alert(error.message);
        }
      });
    }

    if (reviewBtn && reviewBox) {
      reviewBtn.addEventListener("click", () => {
        reviewBox.classList.toggle("hidden");
      });
    }

    if (submitBtn && statusEl && ratingEl && commentEl) {
      submitBtn.addEventListener("click", async () => {
        statusEl.textContent = "Submitting...";

        const stars = Number(ratingEl.value);
        const review_text = commentEl.value.trim();

        if (!Number.isFinite(stars) || stars < 1 || stars > 5) {
          statusEl.textContent = "Stars must be between 1 and 5.";
          return;
        }

        if (review_text.length < 3) {
          statusEl.textContent = "Comment must be at least 3 characters.";
          return;
        }

        try {
          await api(`/restaurants/${branch.restaurant_id}/reviews`, {
            method: "POST",
            body: JSON.stringify({ stars, review_text }),
          });

          statusEl.textContent = "Submitted successfully (pending moderation)";
          commentEl.value = "";
          ratingEl.value = "5";
        } catch (error) {
          statusEl.textContent = error.message;
        }
      });
    }
  }
}

document.getElementById("searchBtn").addEventListener("click", () => {
  page = 1;
  load();
});

if (qEl) {
  qEl.addEventListener("input", () => {
    syncFeaturedVisibility();
  });

  qEl.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      page = 1;
      load();
    }
  });
}

function closeFilterPopover() {
  if (!filterPopover) return;
  filterPopover.classList.add("hidden");
}

function openFilterPopover() {
  if (!filterPopover) return;
  filterPopover.classList.remove("hidden");
}

if (filterBtn) {
  filterBtn.addEventListener("click", (event) => {
    event.stopPropagation();
    if (!filterPopover) return;
    filterPopover.classList.toggle("hidden");
  });
}

if (filterPopover) {
  filterPopover.addEventListener("click", (event) => {
    event.stopPropagation();
  });
}

if (applyFiltersBtn) {
  applyFiltersBtn.addEventListener("click", () => {
    page = 1;
    closeFilterPopover();
    load();
  });
}

if (sortOptions) {
  sortOptions.addEventListener("click", (event) => {
    const button = event.target.closest("[data-sort-value]");
    if (!button) return;

    currentSort = button.dataset.sortValue || "name_asc";
    for (const option of sortOptions.querySelectorAll("[data-sort-value]")) {
      option.classList.toggle("active", option === button);
    }
  });
}

if (cuisineList) {
  cuisineList.addEventListener("click", (event) => {
    const button = event.target.closest("[data-cuisine-id]");
    if (!button) return;

    currentCuisineId = button.dataset.cuisineId || "";
    for (const option of cuisineList.querySelectorAll("[data-cuisine-id]")) {
      option.classList.toggle("active", option === button);
    }
  });
}

document.getElementById("prevBtn").addEventListener("click", () => {
  if (page > 1) {
    page -= 1;
    load();
  }
});

document.getElementById("nextBtn").addEventListener("click", () => {
  if (page < pages) {
    page += 1;
    load();
  }
});

document.getElementById("logoutBtn").addEventListener("click", async () => {
  await api("/auth/logout", { method: "POST" });
  window.location.href = "/login";
});

if (appearanceToggleBtn) {
  appearanceToggleBtn.addEventListener("click", () => {
    toggleAppearance();
    syncAppearanceToggle();
  });
}

if (modalBackdrop) modalBackdrop.addEventListener("click", closeRestaurantModal);
if (closeModalBtn) closeModalBtn.addEventListener("click", closeRestaurantModal);

document.addEventListener("click", () => {
  closeFilterPopover();
});

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (char) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  }[char]));
}

function renderLogo(logoUrl, label, variant) {
  const initials = String(label || "")
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0])
    .join("")
    .toUpperCase() || "IR";

  const sizeClass = variant === "brand" ? "logo-mark logo-mark-lg" : "logo-mark";

  if (logoUrl) {
    return `<img src="${escapeHtml(logoUrl)}" alt="${escapeHtml(label)} logo" class="${sizeClass} brand-logo-image" />`;
  }

  return `<div class="${sizeClass} brand-logo-fallback">${escapeHtml(initials)}</div>`;
}

function trimReview(text) {
  const normalized = String(text || "").trim();
  if (normalized.length <= 120) return normalized;
  return `${normalized.slice(0, 117).trimEnd()}...`;
}

function buildMapUrl(branch) {
  const queryParts = [
    branch.name,
    branch.brand_name,
    branch.address_line1,
    branch.city,
    branch.postcode,
  ].filter(Boolean);

  const params = new URLSearchParams();
  if (branch.restaurant_id != null) {
    params.set("restaurant_id", String(branch.restaurant_id));
  }
  if (queryParts.length) {
    params.set("q", queryParts.join(" "));
  }
  return `/map?${params.toString()}`;
}

if (featuredStage) {
  featuredStage.addEventListener("click", async (event) => {
    const target = event.target.closest("button");

    if (!featuredItems.length) return;

    if (!target) {
      const slide = event.target.closest("[data-featured-open]");
      if (slide) {
        const itemIndex = Number(slide.dataset.featuredOpen || "0");
        const item = featuredItems[itemIndex];
        if (!item) return;
        await openRestaurantGroupModal(item.brand_name || item.name);
      }
      return;
    }

    if (target.dataset.featuredOpenBtn) {
      const itemIndex = Number(target.dataset.featuredOpenBtn || "0");
      const item = featuredItems[itemIndex];
      if (!item) return;
      await openRestaurantGroupModal(item.brand_name || item.name);
      return;
    }

    if (target.id === "featuredPrevBtn") {
      goToFeatured(featuredIndex - 1);
      startFeaturedRotation();
      return;
    }

    if (target.id === "featuredNextBtn") {
      goToFeatured(featuredIndex + 1);
      startFeaturedRotation();
      return;
    }

    if (target.dataset.featuredIndex) {
      goToFeatured(Number(target.dataset.featuredIndex || "0"));
      startFeaturedRotation();
    }
  });

  featuredStage.addEventListener("keydown", async (event) => {
    if (!featuredItems.length) return;

    const slide = event.target.closest("[data-featured-open]");
    if (!slide) return;

    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      const itemIndex = Number(slide.dataset.featuredOpen || "0");
      const item = featuredItems[itemIndex];
      if (!item) return;
      await openRestaurantGroupModal(item.brand_name || item.name);
    }
  });
}

await loadCuisines();
await loadFeatured();
syncAppearanceToggle();
syncFeaturedVisibility();
load();




