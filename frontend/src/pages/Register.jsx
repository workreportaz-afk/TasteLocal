import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useAuth } from "../context/AuthContext.jsx";

export default function Register() {
  const { t } = useTranslation();
  const [form, setForm] = useState({
    username: "", email: "", password: "", account_type: "tourist", business_name: "",
  });
  const [error, setError] = useState("");
  const navigate = useNavigate();
  const { register } = useAuth();

  function update(field) {
    return (e) => setForm({ ...form, [field]: e.target.value });
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    try {
      await register(form);
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
      <div className="auth-tabs">
        <Link to="/login" className="auth-tab">{t("login.loginTitle")}</Link>
        <span className="auth-tab active">{t("login.registerTitle")}</span>
      </div>
      <h1>{t("login.registerTitle")}</h1>
      <label>
        {t("login.username")}
        <input value={form.username} onChange={update("username")} required />
      </label>
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
      <label>
        {t("login.password")}
        <input type="password" value={form.password} onChange={update("password")} required />
      </label>
      <button type="submit">{t("login.registerButton")}</button>
      {form.account_type === "vendor" && (
        <p className="muted">{t("login.vendorApprovalNote")}</p>
      )}
      {error && <p className="error">{error}</p>}
      <p className="muted">
        {t("login.haveAccount")} <Link to="/login">{t("login.loginTitle")}</Link>
      </p>
    </form>
  );
}
