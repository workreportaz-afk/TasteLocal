import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";

export default function NavBar() {
  const { isAuthenticated, user, role, logout } = useAuth();
  const navigate = useNavigate();

  function handleLogout() {
    logout();
    navigate("/");
  }

  return (
    <header className="navbar">
      <Link to="/" className="brand">TasteLocal</Link>
      <nav>
        <Link to="/">Explore</Link>

        {/* Tourist-only pages (admins can still see them, since RequireRole lets admins through everywhere) */}
        {(role === "tourist" || role === "admin") && <Link to="/saved">Saved</Link>}
        {(role === "tourist" || role === "admin") && <Link to="/trip">Plan My Trip</Link>}
        {(role === "tourist" || role === "admin") && <Link to="/bookings">My Bookings</Link>}

        {/* Vendor-only page */}
        {(role === "vendor" || role === "admin") && <Link to="/vendor">Vendor Dashboard</Link>}

        {/* Admin gets a direct link to the Django admin for vendor approvals etc. */}
        {role === "admin" && (
          <a href="http://localhost:8000/admin/" target="_blank" rel="noreferrer">Admin Panel</a>
        )}

        {isAuthenticated ? (
          <>
            <span className="nav-username">Hi, {user.username} ({role})</span>
            <button type="button" className="link-button nav-logout" onClick={handleLogout}>
              Log out
            </button>
          </>
        ) : (
          <Link to="/login">Login</Link>
        )}
      </nav>
    </header>
  );
}
