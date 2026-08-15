//Axios HTTP client with a JWT request interceptor.
//
// WHY a shared client: instead of calling axios directly in every component and
// attaching the token by hand each item, we make ONE pre-configured instance.
// Every request through it points at the backend and carries the user's JWT.
import axios from "axios";

// One axios instance pointed at the backend (URL from .env).
const api = axios.create({
    baseURL: import.meta.env.VITE_API_URL,
});

// REQUEST INTERCEPTOR: runs before every request. Reads the saved JWT and, if
// present, adds "Authorization: Bearer <token>" -- so protected endpoints
// recognize the user without us wiring the header into every call.
api.interceptors.request.use((config) => {
    const token = localStorage.getItem("jwt_token");
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

// RESPONSE INTERCEPTOR: if the backend returns 401 (token missing/expired),
// clear the stored token so the app knows the session is invalid.
api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response && error.response.status === 401) {
            localStorage.removeItem("jwt_token");
        }
        return Promise.reject(error);
    }
);

export default api;