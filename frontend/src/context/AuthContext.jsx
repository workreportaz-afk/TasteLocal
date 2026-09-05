import { createContext, useContext, useEffect, useState } from "react";
import client, { login as apiLogin, register as apiRegister, logout as apiLogout } from "../api/client.js";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // On first load, if we have a token, fetch who it belongs to.
  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      setLoading(false);
      return;
    }
    client
      .get("/auth/me/")
      .then(({ data }) => setUser(data))
      .catch(() => setUser(null))
      .finally(() => setLoading(false));
  }, []);

  async function login(username, password) {
    await apiLogin(username, password);
    const { data } = await client.get("/auth/me/");
    setUser(data);
    return data;
  }

  async function register(payload) {
    await apiRegister(payload);
    return login(payload.username, payload.password);
  }

  function logout() {
    apiLogout();
    setUser(null);
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        loading,
        role: user?.role ?? null, // "admin" | "vendor" | "tourist" | null (logged out)
        vendorId: user?.vendor_id ?? null,
        vendorIsApproved: user?.vendor_is_approved ?? null,
        login,
        register,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside an AuthProvider");
  return ctx;
}
