import { api, requireLogin, getAppearance, toggleAppearance } from "./common.js";

await requireLogin();

let me;
try {
  me = await api("/auth/me");
} catch (e) {
  document.body.innerHTML = `
    <div class="container">
      <div class="card">
        <h2>Auth error</h2>
        <div class="muted">${escapeHtml(e.message)}</div>
        <div style="margin-top:12px;">
          <a href="/login">Go to login</a>
        </div>
      </div>
    </div>
  `;
  throw e;
}

if (me.role !== "admin") {
  document.body.innerHTML = `
    <div class="container">
      <div class="card">
        <h2>Admin only</h2>
        <div class="muted">You must be an admin to view this page.</div>
        <div style="margin-top:12px;">
          <a href="/discovery">Back to Discovery</a>
        </div>
      </div>
    </div>
  `;
  throw new Error("admin only");
}

const list = document.getElementById("list");
const appearanceToggleBtn = document.getElementById("appearanceToggleBtn");
const pendingCountEl = document.getElementById("pendingCount");
const restaurantCountEl = document.getElementById("restaurantCount");
const avgStarsEl = document.getElementById("avgStars");
const oldestPendingEl = document.getElementById("oldestPending");

function syncAppearanceToggle() {
  if (!appearanceToggleBtn) return;
  appearanceToggleBtn.innerHTML = '<span class="appearance-symbol" aria-hidden="true">&#9681;</span>';
  appearanceToggleBtn.setAttribute(
    "aria-label",
    getAppearance() === "dark" ? "Switch to light mode" : "Switch to dark mode",
  );
}

function updateQueueStats(items) {
  const queue = Array.isArray(items) ? items : [];
  const pendingCount = queue.length;
  const restaurantCount = new Set(queue.map((item) => item.restaurant_id ?? item.restaurant_name ?? "")).size;

  const numericStars = queue
    .map((item) => Number(item.stars))
    .filter((value) => Number.isFinite(value));
  const avgStars = numericStars.length
    ? (numericStars.reduce((sum, value) => sum + value, 0) / numericStars.length).toFixed(1)
    : "-";

  const oldestItem = queue
    .map((item) => {
      const date = new Date(item.created_at || "");
      return Number.isNaN(date.getTime()) ? null : date;
    })
    .filter(Boolean)
    .sort((a, b) => a - b)[0];

  if (pendingCountEl) pendingCountEl.textContent = String(pendingCount);
  if (restaurantCountEl) restaurantCountEl.textContent = String(restaurantCount);
  if (avgStarsEl) avgStarsEl.textContent = avgStars === "-" ? "-" : `${avgStars}/5`;
  if (oldestPendingEl) oldestPendingEl.textContent = oldestItem ? formatShortDate(oldestItem) : "-";
}

function formatShortDate(date) {
  return new Intl.DateTimeFormat("en-GB", {
    day: "numeric",
    month: "short",
    year: "numeric",
  }).format(date);
}

async function load() {
  list.textContent = "Loading...";

  try {
    const data = await api("/admin/pending-reviews");

    if (!data || typeof data !== "object") {
      list.innerHTML = `<div class="muted">Unexpected response: ${escapeHtml(String(data))}</div>`;
      return;
    }

    const items = data.items || [];
    updateQueueStats(items);

    if (!items.length) {
      list.textContent = "No pending reviews";
      return;
    }

    list.innerHTML = "";

    for (const rv of items) {
      const div = document.createElement("div");
      div.className = "item";

      div.innerHTML = `
        <div><b>${escapeHtml(rv.restaurant_name)}</b> - ${Number(rv.stars)}/5</div>
        <div class="muted">by ${escapeHtml(rv.user_email)} - ${escapeHtml(rv.created_at || "")}</div>
        <div style="margin-top:8px;">${escapeHtml(rv.review_text)}</div>

        <label style="margin-top:10px;">Admin note (optional)</label>
        <input class="note" placeholder="Reason / feedback..." />

        <div class="row">
          <button class="publish">Publish</button>
          <button class="needs">Needs edit</button>
          <button class="reject">Reject</button>
          <div class="muted status"></div>
        </div>
      `;

      const noteEl = div.querySelector(".note");
      const statusEl = div.querySelector(".status");

      async function moderate(decision) {
        statusEl.textContent = "Saving...";

        try {
          await api(`/admin/reviews/${rv.review_id}/moderate`, {
            method: "POST",
            body: JSON.stringify({
              decision,
              admin_note: noteEl.value.trim(),
            }),
          });

          statusEl.textContent = `Done (${decision})`;
          div.remove();

          if (!list.children.length) list.textContent = "No pending reviews";
        } catch (e) {
          statusEl.textContent = e.message;
        }
      }

      div.querySelector(".publish").addEventListener("click", () => moderate("publish"));
      div.querySelector(".needs").addEventListener("click", () => moderate("needs_edit"));
      div.querySelector(".reject").addEventListener("click", () => moderate("reject"));

      list.appendChild(div);
    }
  } catch (e) {
    list.innerHTML = `
      <div class="muted">Failed to load queue.</div>
      <pre style="white-space:pre-wrap;margin-top:8px;">${escapeHtml(e.message)}</pre>
    `;
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

function escapeHtml(s) {
  return (s ?? "").replace(/[&<>"']/g, (c) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  }[c]));
}

syncAppearanceToggle();
load();
