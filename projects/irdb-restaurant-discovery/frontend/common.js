const APPEARANCE_KEY = "irdb_appearance";

export function getAppearance() {
  const saved = window.localStorage.getItem(APPEARANCE_KEY);
  if (saved === "dark" || saved === "light") return saved;

  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

export function setAppearance(theme) {
  const normalized = theme === "dark" ? "dark" : "light";
  document.documentElement.dataset.theme = normalized;
  window.localStorage.setItem(APPEARANCE_KEY, normalized);
  return normalized;
}

export function toggleAppearance() {
  return setAppearance(getAppearance() === "dark" ? "light" : "dark");
}

export function initAppearance() {
  return setAppearance(getAppearance());
}

initAppearance();

export async function api(path, options = {}) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    credentials: "include",
    ...options,
  });

  let data = null;
  const ct = res.headers.get("content-type") || "";
  if (ct.includes("application/json")) data = await res.json();

  if (!res.ok) {
    const msg = (data && (data.error || data.message)) || `HTTP ${res.status}`;
    const err = new Error(msg);
    err.status = res.status;
    err.data = data;
    throw err;
  }
  return data;
}

export async function requireLogin() {
  try {
    return await api("/auth/me");
  } catch (e) {
    if (e.status === 401) window.location.href = "/login";
    throw e;
  }
}
