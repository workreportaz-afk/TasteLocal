import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useAuth } from "../context/AuthContext.jsx";

export default function Login() {
  const { t } = useTranslation();
  const [form, setForm] = useState({ username: "", password: "" });
  const [error, setError] = useState("");
  const navigate = useNavigate();
  const { login } = useAuth();

  function update(field) {
    return (e) => setForm({ ...form, [field]: e.target.value });
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    try {
      await login(form.username, form.password);
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
        <span className="auth-tab active">{t("login.loginTitle")}</span>
        <Link to="/register" className="auth-tab">{t("login.registerTitle")}</Link>
      </div>
      <h1>{t("login.loginTitle")}</h1>
      <label>
        {t("login.username")}
        <input value={form.username} onChange={update("username")} required />
      </label>
      <label>
        {t("login.password")}
        <input type="password" value={form.password} onChange={update("password")} required />
      </label>
      <button type="submit">{t("login.loginButton")}</button>
      {error && <p className="error">{error}</p>}
      <p className="muted">
        {t("login.needAccount")} <Link to="/register">{t("login.registerTitle")}</Link>
      </p>
    </form>
  );
}
