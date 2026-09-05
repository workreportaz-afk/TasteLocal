import { useAuth } from "../context/AuthContext.jsx";

/**
 * Wrap a page element to restrict it to specific roles, e.g.:
 *   <RequireRole allow={["vendor"]}><VendorDashboard /></RequireRole>
 * Admins can always pass, regardless of `allow` -- they're the superset role.
 */
export default function RequireRole({ allow, children }) {
  const { isAuthenticated, role, loading } = useAuth();

  if (loading) return <p>Loading...</p>;

  if (!isAuthenticated) {
    return <p>Please log in to view this page.</p>;
  }

  if (role !== "admin" && !allow.includes(role)) {
    return (
      <div className="role-blocked">
        <h2>Not available for your account</h2>
        <p className="muted">
          This page is only available to {allow.join(" or ")} accounts.
          You're logged in as a {role} account.
        </p>
      </div>
    );
  }

  return children;
}
