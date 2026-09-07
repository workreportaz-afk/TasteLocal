import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useAuth } from "../context/AuthContext.jsx";

export default function Login() {
  const { t } = useTranslation();
  const [mode, setMode] = useState("login"); // "login" | "register"
  const [form, setForm] = useState({
    username: "", email: "", password: "", account_type: "tourist", business_name: "",
  });
  const [error, setError] = useState("");
  const navigate = useNavigate();
  const { login, register } = useAuth();

  function update(field) {
    return (e) => setForm({ ...form, [field]: e.target.value });
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    try {
      if (mode === "register") {
        await register(form);
      } else {
        await login(form.username, form.password);
      }
      navigate("/");
    } catch (err) {
      const backendError = err.response?.data;
      setError(
        (backendError && Object.values(backendError).flat().join(" ")) ||
        t("login.authError")
      );
    }
  }

  return (
    <form onSubmit={handleSubmit} className="auth-form">
      <h1>{mode === "login" ? t("login.loginTitle") : t("login.registerTitle")}</h1>
      <label>
        {t("login.username")}
        <input value={form.username} onChange={update("username")} required />
      </label>
      {mode === "register" && (
        <>
          <label>
            {t("login.email")}
            <input type="email" value={form.email} onChange={update("email")} required />
          </label>
          <label>
            {t("login.accountType")}
            <select value={form.account_type} onChange={update("account_type")}>
              <option value="tourist">{t("login.tourist")}</option>
              <option value="vendor">{t("login.vendor")}</option>
            </select>
          </label>
          {form.account_type === "vendor" && (
            <label>
              {t("login.businessName")}
              <input value={form.business_name} onChange={update("business_name")} required />
            </label>
          )}
        </>
      )}
      <label>
        {t("login.password")}
        <input type="password" value={form.password} onChange={update("password")} required />
      </label>
      <button type="submit">{mode === "login" ? t("login.loginButton") : t("login.registerButton")}</button>
      {mode === "register" && form.account_type === "vendor" && (
        <p className="muted">{t("login.vendorApprovalNote")}</p>
      )}
      {error && <p className="error">{error}</p>}
      <button type="button" className="link-button" onClick={() => setMode(mode === "login" ? "register" : "login")}>
        {mode === "login" ? t("login.needAccount") : t("login.haveAccount")}
      </button>
    </form>
  );
}
