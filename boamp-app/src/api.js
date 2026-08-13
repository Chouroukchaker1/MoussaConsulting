const TOKEN_KEY = "boamp_token";
const USERNAME_KEY = "boamp_username";

export function getToken() {
  return sessionStorage.getItem(TOKEN_KEY);
}

export function getUsername() {
  return sessionStorage.getItem(USERNAME_KEY);
}

export function setSession(token, username) {
  sessionStorage.setItem(TOKEN_KEY, token);
  sessionStorage.setItem(USERNAME_KEY, username);
}

export function clearSession() {
  sessionStorage.removeItem(TOKEN_KEY);
  sessionStorage.removeItem(USERNAME_KEY);
}

async function request(path, options = {}) {
  const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
  const token = getToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(path, { ...options, headers });
  const isJson = (res.headers.get("content-type") || "").includes("application/json");
  const body = isJson ? await res.json() : null;

  if (!res.ok) {
    if (res.status === 401) clearSession();
    throw new Error((body && body.error) || `Erreur ${res.status}`);
  }
  return body;
}

export function login(username, password) {
  return request("/api/login", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });
}

export function fetchSecteurs() {
  return request("/api/secteurs", { method: "GET" });
}

export function extract(dateDebut, dateFin, secteur, page = 1, perPage = 2000) {
  return request("/api/scrape", {
    method: "POST",
    body: JSON.stringify({ date_debut: dateDebut, date_fin: dateFin, secteur, page, per_page: perPage }),
  });
}
