import { api, requireLogin, getAppearance, toggleAppearance } from "./common.js";

const meRoleEl = document.getElementById("meRole");
const meEmailEl = document.getElementById("meEmail");
const reviewsEl = document.getElementById("reviews");
const favsEl = document.getElementById("favs");
const adminLink = document.getElementById("adminQueueLink");
const appearanceToggleBtn = document.getElementById("appearanceToggleBtn");
const reviewSummaryValueEl = document.getElementById("reviewSummaryValue");
const reviewSummaryCopyEl = document.getElementById("reviewSummaryCopy");
const favsSummaryValueEl = document.getElementById("favsSummaryValue");
const favsSummaryCopyEl = document.getElementById("favsSummaryCopy");

const me = await requireLogin();
syncAccountCard(me);
if (adminLink) {
  if (me.role === "admin") adminLink.classList.remove("hidden");
  else adminLink.classList.add("hidden");
}

function syncAppearanceToggle() {
  if (!appearanceToggleBtn) return;
  appearanceToggleBtn.innerHTML = '<span class="appearance-symbol" aria-hidden="true">&#9681;</span>';
  appearanceToggleBtn.setAttribute(
    "aria-label",
    getAppearance() === "dark" ? "Switch to light mode" : "Switch to dark mode",
  );
}

function escapeHtml(s) {
  return (s ?? "").replace(/[&<>"']/g, (c) => ({
    "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"
  }[c]));
}

function titleCaseRole(role) {
  return String(role || "customer")
    .replace(/_/g, " ")
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

function syncAccountCard(account) {
  if (meRoleEl) meRoleEl.textContent = titleCaseRole(account.role);
  if (meEmailEl) meEmailEl.textContent = account.email || "";
}

async function loadReviews() {
  reviewsEl.innerHTML = `<div class="muted">Loading...</div>`;
  const data = await api("/me/reviews");
  const items = data.items || [];

  const groups = {};
  for (const r of items) {
    (groups[r.status] ||= []).push(r);
  }

  if (reviewSummaryValueEl) {
    reviewSummaryValueEl.textContent = `${items.length} total`;
  }
  if (reviewSummaryCopyEl) {
    const pendingCount = (groups.pending || []).length;
    const publishedCount = (groups.published || []).length;
    reviewSummaryCopyEl.textContent = pendingCount
      ? `${pendingCount} waiting for moderation and ${publishedCount} already live.`
      : publishedCount
        ? `${publishedCount} published review${publishedCount === 1 ? "" : "s"} currently visible.`
        : "No review activity yet.";
  }

  const order = ["pending", "published", "needs_edit", "rejected"];
  reviewsEl.innerHTML = "";

  for (const st of order) {
    const items = groups[st] || [];
    const section = document.createElement("div");
    section.innerHTML = `<h3>${st} (${items.length})</h3>`;

    if (!items.length) {
      section.innerHTML += `<div class="muted">None</div>`;
    } else {
      for (const rv of items) {
        const name = rv.restaurant_name
          ? rv.restaurant_name
          : `Restaurant #${rv.restaurant_id}`;

        const row = document.createElement("div");
        row.className = "item";
        row.innerHTML = `
          <div><b>${escapeHtml(name)}</b> — ${rv.stars}/5</div>
          <div class="muted">${escapeHtml(rv.review_text || "")}</div>
          <div class="muted">${escapeHtml(rv.created_at || "")}</div>
        `;
        section.appendChild(row);
      }
    }

    reviewsEl.appendChild(section);
  }
}

async function loadFavs() {
  favsEl.innerHTML = `<div class="muted">Loading...</div>`;
  const data = await api("/me/favorites");
  const items = data.items || [];

  if (favsSummaryValueEl) {
    favsSummaryValueEl.textContent = `${items.length} saved`;
  }
  if (favsSummaryCopyEl) {
    favsSummaryCopyEl.textContent = items.length
      ? `Quick access to ${items.length === 1 ? "your saved restaurant" : "your saved restaurants"}.`
      : "Nothing saved yet.";
  }

  favsEl.innerHTML = "";
  if (!items.length) {
    favsEl.innerHTML = `<div class="muted">No favourites yet.</div>`;
    return;
  }

  for (const r of items) {
    const row = document.createElement("div");
    row.className = "item";
    row.innerHTML = `
      <div><b>${escapeHtml(r.name)}</b></div>
      <div class="muted">${escapeHtml(r.address_line1 || "")}, ${escapeHtml(r.city || "")} ${escapeHtml(r.postcode || "")}</div>
      <div class="muted">FHRS: ${escapeHtml(String(r.hygiene_rating ?? "N/A"))}</div>
    `;
    favsEl.appendChild(row);
  }
}

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

syncAppearanceToggle();
await loadReviews();
await loadFavs();
