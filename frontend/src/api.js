// Pre-configured Axios client with JWT auth headers, 401 handling, and error formatting.
import axios from "axios";

// Base HTTP client pointing to the backend API URL.
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? "http://localhost:8000",
});

// Attach the JWT to every request once the user is logged in.
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("creatoriq_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Clear expired/invalid JWT on 401 and redirect to /login.
api.interceptors.response.use(
  (res) => res,
  (err) => {
    const status = err?.response?.status;
    const url = err?.config?.url || "";
    if (status === 401 && !url.includes("/auth/login")) {
      localStorage.removeItem("creatoriq_token");
      if (typeof window !== "undefined" && window.location.pathname !== "/login") {
        window.location.assign("/login");
      }
    }
    return Promise.reject(err);
  }
);

// Turn FastAPI errors (string or validation list) into one readable message.
export function errorMessage(err) {
  const detail = err?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((d) => d.msg.replace(/^Value error, /, ""))
      .join(". ");
  }
  if (err?.code === "ERR_NETWORK") return "Cannot reach the server. Is the backend running?";
  return "Something went wrong. Please try again.";
}

export default api;
