import { Link, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useAuth } from "../context/AuthContext.jsx";

const LANGUAGES = [
  ["en", "EN"],
  ["zh", "中文"],
  ["ms", "BM"],
];

export default function NavBar() {
  const { isAuthenticated, user, role, logout } = useAuth();
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();

  function handleLogout() {
    logout();
    navigate("/");
  }

  return (
    <header className="navbar">
      <Link to="/" className="brand">TasteLocal</Link>
      <nav>
        <Link to="/">{t("nav.explore")}</Link>

        {/* Tourist-only pages (admins can still see them, since RequireRole lets admins through everywhere) */}
        {(role === "tourist" || role === "admin") && <Link to="/saved">{t("nav.saved")}</Link>}
        {(role === "tourist" || role === "admin") && <Link to="/trip">{t("nav.planTrip")}</Link>}
        {(role === "tourist" || role === "admin") && <Link to="/trip-planner">{t("nav.tripPlannerChat")}</Link>}
        {(role === "tourist" || role === "admin") && <Link to="/bookings">{t("nav.myBookings")}</Link>}

        {/* Vendor-only page */}
        {(role === "vendor" || role === "admin") && <Link to="/vendor">{t("nav.vendorDashboard")}</Link>}

        {/* Admin gets a direct link to the Django admin for vendor approvals etc. */}
        {role === "admin" && (
          <a href="http://localhost:8000/admin/" target="_blank" rel="noreferrer">{t("nav.adminPanel")}</a>
        )}

        <select
          className="language-switcher"
          value={i18n.language}
          onChange={(e) => i18n.changeLanguage(e.target.value)}
          aria-label={t("language.label")}
        >
          {LANGUAGES.map(([code, label]) => (
            <option key={code} value={code}>{label}</option>
          ))}
        </select>

        {isAuthenticated ? (
          <>
            <span className="nav-username">{t("nav.hi", { name: user.username, role })}</span>
            <button type="button" className="link-button nav-logout" onClick={handleLogout}>
              {t("nav.logout")}
            </button>
          </>
        ) : (
          <>
            <Link to="/login">{t("nav.login")}</Link>
            <Link to="/register">{t("nav.register")}</Link>
          </>
        )}
      </nav>
    </header>
  );
}
