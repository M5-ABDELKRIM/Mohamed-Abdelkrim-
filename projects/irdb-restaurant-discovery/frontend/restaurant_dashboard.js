import { api, getAppearance, requireLogin, toggleAppearance } from "./common.js";

const brandTitle = document.getElementById("brandTitle");
const summary = document.getElementById("summary");
const branchesDiv = document.getElementById("branches");
const reviewsDiv = document.getElementById("reviews");
const logoutBtn = document.getElementById("logoutBtn");
const appearanceToggleBtn = document.getElementById("appearanceToggleBtn");

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (char) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  }[char]));
}

function syncAppearanceLabel() {
  if (!appearanceToggleBtn) return;
  appearanceToggleBtn.innerHTML = '<span class="appearance-symbol" aria-hidden="true">&#9681;</span>';
  appearanceToggleBtn.setAttribute(
    "aria-label",
    getAppearance() === "dark" ? "Switch to light mode" : "Switch to dark mode",
  );
}

async function loadDashboard() {
  const data = await api("/restaurant/dashboard");

  brandTitle.textContent = data.brand_name || "Restaurant Portal";

  summary.innerHTML = `
    <div class="stat-card">
      <div class="muted">Average rating</div>
      <div class="title" style="margin-top:8px;">${data.average_rating ?? "N/A"}</div>
    </div>
    <div class="stat-card">
      <div class="muted">Published reviews</div>
      <div class="title" style="margin-top:8px;">${escapeHtml(String(data.published_reviews_count ?? 0))}</div>
    </div>
    <div class="stat-card">
      <div class="muted">Branches</div>
      <div class="title" style="margin-top:8px;">${escapeHtml(String(data.branch_count ?? 0))}</div>
    </div>
  `;

  const branches = data.branches || [];
  branchesDiv.innerHTML = "";

  if (!branches.length) {
    branchesDiv.innerHTML = '<div class="card"><div class="muted">No branches linked to this brand yet.</div></div>';
    return;
  }

  branches.forEach((branch) => {
    const el = document.createElement("div");
    el.className = "card";
    el.innerHTML = `
      <div class="title">${escapeHtml(branch.name || "Branch")}</div>
      <div class="muted">${escapeHtml([branch.city, branch.postcode].filter(Boolean).join(" ")) || "Location pending"}</div>
      <div class="row" style="margin-top:12px;">
        <div class="pill">${branch.menu_verified ? "Menu linked" : "Menu pending"}</div>
        ${branch.website_url ? '<div class="pill">Website added</div>' : ""}
        ${branch.phone ? '<div class="pill">Phone listed</div>' : ""}
      </div>
      <div class="inline-form" style="margin-top:14px;">
        <button data-branch-edit-toggle="${branch.restaurant_id}" type="button">Edit details</button>
      </div>
      <div id="branchEdit_${branch.restaurant_id}" class="inline-form hidden" style="margin-top:14px;">
        <label for="branchDescription_${branch.restaurant_id}">Description</label>
        <textarea id="branchDescription_${branch.restaurant_id}" rows="3" placeholder="Tell people about this branch...">${escapeHtml(branch.description || "")}</textarea>

        <label for="branchPhone_${branch.restaurant_id}">Phone</label>
        <input id="branchPhone_${branch.restaurant_id}" value="${escapeHtml(branch.phone || "")}" placeholder="Phone number" />

        <label for="branchWebsite_${branch.restaurant_id}">Website</label>
        <input id="branchWebsite_${branch.restaurant_id}" value="${escapeHtml(branch.website_url || "")}" placeholder="https://..." />

        <label for="branchOrdering_${branch.restaurant_id}">Ordering link</label>
        <input id="branchOrdering_${branch.restaurant_id}" value="${escapeHtml(branch.ordering_url || "")}" placeholder="https://..." />

        <label for="branchMenu_${branch.restaurant_id}">Menu link</label>
        <input id="branchMenu_${branch.restaurant_id}" value="${escapeHtml(branch.menu_url || "")}" placeholder="https://..." />

        <label for="branchEmail_${branch.restaurant_id}">Email</label>
        <input id="branchEmail_${branch.restaurant_id}" value="${escapeHtml(branch.email || "")}" placeholder="contact@example.com" />

        <div class="row" style="margin-top:8px;">
          <button data-branch-save="${branch.restaurant_id}" type="button">Save changes</button>
          <div id="branchEditStatus_${branch.restaurant_id}" class="muted"></div>
        </div>
      </div>
    `;
    branchesDiv.appendChild(el);
  });
}

async function loadReviews() {
  const data = await api("/restaurant/reviews");
  const reviews = data.reviews || [];

  reviewsDiv.innerHTML = "";

  if (!reviews.length) {
    reviewsDiv.innerHTML = '<div class="muted">No published reviews yet for this brand.</div>';
    return;
  }

  reviews.forEach((review) => {
    const el = document.createElement("div");
    el.className = "card";
    el.innerHTML = `
      <div class="row" style="justify-content:space-between; align-items:flex-start;">
        <div>
          <div class="title">${escapeHtml(review.branch_name || "Branch")}</div>
          <div class="muted">${escapeHtml(review.created_at || "")}</div>
        </div>
        <div class="pill">${escapeHtml(String(review.stars))}/5 stars</div>
      </div>
      <p style="margin:14px 0 0; line-height:1.7;">${escapeHtml(review.review_text || "")}</p>
      ${review.reply ? `
        <div class="card modal-review-card" style="margin-top:14px; margin-bottom:0; box-shadow:none;">
          <div class="muted">Restaurant reply</div>
          <div style="margin-top:8px; line-height:1.7;">${escapeHtml(review.reply.reply_text)}</div>
          <div class="inline-form" style="margin-top:12px;">
            <button data-reply-edit-toggle="${review.reply.reply_id}" type="button">Edit reply</button>
          </div>
          <div id="replyEdit_${review.reply.reply_id}" class="inline-form hidden" style="margin-top:12px;">
            <label for="replyEditText_${review.reply.reply_id}">Update reply</label>
            <textarea id="replyEditText_${review.reply.reply_id}" placeholder="Improve your response...">${escapeHtml(review.reply.reply_text)}</textarea>
            <div class="row" style="margin-top:8px;">
              <button data-reply-save="${review.reply.reply_id}" type="button">Save reply</button>
              <div id="replyStatus_${review.reply.reply_id}" class="muted"></div>
            </div>
          </div>
        </div>
      ` : `
        <div class="inline-form" style="margin-top:14px;">
          <label for="reply_${review.review_id}">Reply to this review</label>
          <textarea id="reply_${review.review_id}" placeholder="Write a thoughtful response..."></textarea>
          <button data-id="${review.review_id}" type="button">Publish Reply</button>
        </div>
      `}
    `;
    reviewsDiv.appendChild(el);
  });
}

reviewsDiv.addEventListener("click", async (event) => {
  const editToggle = event.target.closest("button[data-reply-edit-toggle]");
  if (editToggle) {
    const replyId = editToggle.dataset.replyEditToggle;
    const panel = document.getElementById(`replyEdit_${replyId}`);
    if (panel) panel.classList.toggle("hidden");
    return;
  }

  const saveReplyBtn = event.target.closest("button[data-reply-save]");
  if (saveReplyBtn) {
    const replyId = saveReplyBtn.dataset.replySave;
    const textarea = document.getElementById(`replyEditText_${replyId}`);
    const statusEl = document.getElementById(`replyStatus_${replyId}`);
    const text = textarea?.value.trim() || "";

    if (!text) {
      if (statusEl) statusEl.textContent = "Write a reply first";
      return;
    }

    saveReplyBtn.disabled = true;
    saveReplyBtn.textContent = "Saving...";

    try {
      await api(`/restaurant/replies/${replyId}`, {
        method: "PUT",
        body: JSON.stringify({ reply_text: text }),
      });
      await loadReviews();
    } catch (error) {
      if (statusEl) statusEl.textContent = error.message;
    } finally {
      saveReplyBtn.disabled = false;
      saveReplyBtn.textContent = "Save reply";
    }
    return;
  }

  const button = event.target.closest("button[data-id]");
  if (!button) return;

  const reviewId = button.dataset.id;
  const textarea = document.getElementById(`reply_${reviewId}`);
  const text = textarea.value.trim();

  if (!text) {
    alert("Write a reply first");
    return;
  }

  button.disabled = true;
  button.textContent = "Publishing...";

  try {
    await api(`/restaurant/reviews/${reviewId}/reply`, {
      method: "POST",
      body: JSON.stringify({ reply_text: text }),
    });
    await loadReviews();
  } finally {
    button.disabled = false;
    button.textContent = "Publish Reply";
  }
});

branchesDiv.addEventListener("click", async (event) => {
  const toggleBtn = event.target.closest("button[data-branch-edit-toggle]");
  if (toggleBtn) {
    const restaurantId = toggleBtn.dataset.branchEditToggle;
    const panel = document.getElementById(`branchEdit_${restaurantId}`);
    if (panel) panel.classList.toggle("hidden");
    return;
  }

  const saveBtn = event.target.closest("button[data-branch-save]");
  if (!saveBtn) return;

  const restaurantId = saveBtn.dataset.branchSave;
  const statusEl = document.getElementById(`branchEditStatus_${restaurantId}`);
  const payload = {
    description: document.getElementById(`branchDescription_${restaurantId}`)?.value ?? "",
    phone: document.getElementById(`branchPhone_${restaurantId}`)?.value ?? "",
    website_url: document.getElementById(`branchWebsite_${restaurantId}`)?.value ?? "",
    ordering_url: document.getElementById(`branchOrdering_${restaurantId}`)?.value ?? "",
    menu_url: document.getElementById(`branchMenu_${restaurantId}`)?.value ?? "",
    email: document.getElementById(`branchEmail_${restaurantId}`)?.value ?? "",
  };

  saveBtn.disabled = true;
  saveBtn.textContent = "Saving...";
  if (statusEl) statusEl.textContent = "";

  try {
    await api(`/restaurant/branches/${restaurantId}`, {
      method: "PUT",
      body: JSON.stringify(payload),
    });
    if (statusEl) statusEl.textContent = "Saved";
    await loadDashboard();
  } catch (error) {
    if (statusEl) statusEl.textContent = error.message;
  } finally {
    saveBtn.disabled = false;
    saveBtn.textContent = "Save changes";
  }
});

if (logoutBtn) {
  logoutBtn.addEventListener("click", async () => {
    await api("/auth/logout", { method: "POST" });
    window.location.href = "/login";
  });
}

if (appearanceToggleBtn) {
  appearanceToggleBtn.addEventListener("click", () => {
    toggleAppearance();
    syncAppearanceLabel();
  });
}

async function init() {
  await requireLogin();
  syncAppearanceLabel();
  await loadDashboard();
  await loadReviews();
}

init();
