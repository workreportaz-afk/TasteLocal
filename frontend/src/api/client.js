import axios from "axios";
import i18n from "../i18n/index.js";

// In dev, talk directly to the local Django server. In production, this is
// overridden by VITE_API_BASE_URL (see .env.production) to a relative "/api",
// which nginx reverse-proxies to the backend container -- no hardcoded host.
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000/api";

const client = axios.create({ baseURL: API_BASE_URL });

// Attach the access token, and the current UI language, to every request.
// The backend uses ?lang= to return machine-translated titles/descriptions
// for experiences (see core/translation.py) -- harmless for endpoints that
// don't look at it.
client.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  if (config.method === "get") {
    config.params = { ...config.params, lang: i18n.language };
  }
  return config;
});

// On a 401, try refreshing the access token once, then retry the request.
client.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config;
    if (error.response?.status === 401 && !original._retry) {
      original._retry = true;
      const refresh = localStorage.getItem("refresh_token");
      if (refresh) {
        try {
          const { data } = await axios.post(`${API_BASE_URL}/auth/token/refresh/`, { refresh });
          localStorage.setItem("access_token", data.access);
          original.headers.Authorization = `Bearer ${data.access}`;
          return client(original);
        } catch {
          localStorage.removeItem("access_token");
          localStorage.removeItem("refresh_token");
        }
      }
    }
    return Promise.reject(error);
  }
);

export default client;

export async function login(username, password) {
  const { data } = await client.post("/auth/login/", { username, password });
  localStorage.setItem("access_token", data.access);
  localStorage.setItem("refresh_token", data.refresh);
  return data;
}

export async function register(payload) {
  const { data } = await client.post("/auth/register/", payload);
  return data;
}

export function logout() {
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
}
