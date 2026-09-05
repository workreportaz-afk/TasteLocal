import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";

export default function NavBar() {
  const { isAuthenticated, user, logout } = useAuth();
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
        {isAuthenticated && <Link to="/saved">Saved</Link>}
        {isAuthenticated && <Link to="/trip">Plan My Trip</Link>}
        {isAuthenticated && <Link to="/bookings">My Bookings</Link>}
        {isAuthenticated && <Link to="/vendor">Vendor Dashboard</Link>}
        {isAuthenticated ? (
          <>
            <span className="nav-username">Hi, {user.username}</span>
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
