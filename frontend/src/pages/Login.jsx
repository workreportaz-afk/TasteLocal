import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";

export default function Login() {
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
        "Could not authenticate. Check your details and try again."
      );
    }
  }

  return (
    <form onSubmit={handleSubmit} className="auth-form">
      <h1>{mode === "login" ? "Log in" : "Create an account"}</h1>
      <label>
        Username
        <input value={form.username} onChange={update("username")} required />
      </label>
      {mode === "register" && (
        <>
          <label>
            Email
            <input type="email" value={form.email} onChange={update("email")} required />
          </label>
          <label>
            Account type
            <select value={form.account_type} onChange={update("account_type")}>
              <option value="tourist">Tourist — explore & book food experiences</option>
              <option value="vendor">Vendor — list my food business</option>
            </select>
          </label>
          {form.account_type === "vendor" && (
            <label>
              Business name
              <input value={form.business_name} onChange={update("business_name")} required />
            </label>
          )}
        </>
      )}
      <label>
        Password
        <input type="password" value={form.password} onChange={update("password")} required />
      </label>
      <button type="submit">{mode === "login" ? "Log in" : "Register"}</button>
      {mode === "register" && form.account_type === "vendor" && (
        <p className="muted">
          Vendor accounts need admin approval before listings appear publicly —
          you can still set up your listings right away, they just won't be
          visible to tourists until approved.
        </p>
      )}
      {error && <p className="error">{error}</p>}
      <button type="button" className="link-button" onClick={() => setMode(mode === "login" ? "register" : "login")}>
        {mode === "login" ? "Need an account? Register" : "Already have an account? Log in"}
      </button>
    </form>
  );
}
