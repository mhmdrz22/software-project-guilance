class APIError extends Error {
  constructor(message, data) {
    super(message);
    this.name = "APIError";
    this.data = data;
  }
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api";
const AUTH_URL = `${API_BASE_URL}/auth`;
const TASKS_URL = `${API_BASE_URL}/tasks`;

function getStoredTokens() {
  return {
    access: localStorage.getItem("accessToken"),
    refresh: localStorage.getItem("refreshToken"),
  };
}

function storeTokens({ access, refresh }) {
  if (access) localStorage.setItem("accessToken", access);
  if (refresh) localStorage.setItem("refreshToken", refresh);
}

export function clearAuthTokens() {
  localStorage.removeItem("accessToken");
  localStorage.removeItem("refreshToken");
}

async function handleResponse(response) {
  let data = null;
  try {
    data = await response.json();
  } catch {
    // ignore parse errors
  }

  if (!response.ok) {
    const message =
      (data && (data.detail || data.message)) ||
      response.statusText ||
      "Something went wrong";
    throw new APIError(message, data);
  }

  if (response.status === 204) return null;
  return data;
}

async function refreshAccessToken() {
  const { refresh } = getStoredTokens();
  if (!refresh) throw new APIError("Not authenticated", null);

  const res = await fetch(`${AUTH_URL}/token/refresh/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh }),
  });

  const data = await handleResponse(res);
  storeTokens({ access: data.access, refresh: data.refresh ?? refresh });
  return data.access;
}

async function authFetch(url, options = {}) {
  const { access } = getStoredTokens();
  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
  };
  if (access) headers.Authorization = `Bearer ${access}`;

  const res = await fetch(url, { ...options, headers });
  if (res.status !== 401) {
    return handleResponse(res);
  }

  // Try one refresh then retry once
  const newAccess = await refreshAccessToken();
  const retryHeaders = { ...headers, Authorization: `Bearer ${newAccess}` };
  const retryRes = await fetch(url, { ...options, headers: retryHeaders });
  return handleResponse(retryRes);
}

// Auth endpoints
export async function registerUser(data) {
  const res = await fetch(`${AUTH_URL}/register/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return handleResponse(res);
}

export async function loginUser(credentials) {
  const res = await fetch(`${AUTH_URL}/token/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(credentials),
  });
  const data = await handleResponse(res);
  storeTokens({ access: data.access, refresh: data.refresh });
  return data;
}

export async function fetchCurrentUser() {
  return authFetch(`${AUTH_URL}/me/`);
}

// Task endpoints (auth required)
export async function fetchTasks() {
  return authFetch(`${TASKS_URL}/`);
}

export async function createTask(data) {
  return authFetch(`${TASKS_URL}/`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function updateTask(id, data) {
  return authFetch(`${TASKS_URL}/${id}/`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export async function deleteTask(id) {
  return authFetch(`${TASKS_URL}/${id}/`, {
    method: "DELETE",
  });
}
