import { useTranslation } from "react-i18next";
import { useAuth } from "../context/AuthContext.jsx";

/**
 * Wrap a page element to restrict it to specific roles, e.g.:
 *   <RequireRole allow={["vendor"]}><VendorDashboard /></RequireRole>
 * Admins can always pass, regardless of `allow` -- they're the superset role.
 */
export default function RequireRole({ allow, children }) {
  const { t } = useTranslation();
  const { isAuthenticated, role, loading } = useAuth();

  if (loading) return <p>{t("common.loading")}</p>;

  if (!isAuthenticated) {
    return <p>{t("roleBlocked.loginPrompt")}</p>;
  }

  if (role !== "admin" && !allow.includes(role)) {
    return (
      <div className="role-blocked">
        <h2>{t("roleBlocked.title")}</h2>
        <p className="muted">{t("roleBlocked.message", { roles: allow.join(" / "), role })}</p>
      </div>
    );
  }

  return children;
}
