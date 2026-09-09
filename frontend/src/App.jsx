import { Routes, Route } from "react-router-dom";
import NavBar from "./components/NavBar.jsx";
import RequireRole from "./components/RequireRole.jsx";
import Home from "./pages/Home.jsx";
import ExperienceDetail from "./pages/ExperienceDetail.jsx";
import Bookings from "./pages/Bookings.jsx";
import Login from "./pages/Login.jsx";
import VendorDashboard from "./pages/VendorDashboard.jsx";
import Saved from "./pages/Saved.jsx";
import PlanMyTrip from "./pages/PlanMyTrip.jsx";
import TripPlanner from "./pages/TripPlanner.jsx";

export default function App() {
  return (
    <div className="app-shell">
      <NavBar />
      <main className="app-content">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/experiences/:id" element={<ExperienceDetail />} />
          <Route path="/bookings" element={<RequireRole allow={["tourist"]}><Bookings /></RequireRole>} />
          <Route path="/login" element={<Login />} />
          <Route path="/vendor" element={<RequireRole allow={["vendor"]}><VendorDashboard /></RequireRole>} />
          <Route path="/saved" element={<RequireRole allow={["tourist"]}><Saved /></RequireRole>} />
          <Route path="/trip" element={<RequireRole allow={["tourist"]}><PlanMyTrip /></RequireRole>} />
          <Route path="/trip-planner" element={<RequireRole allow={["tourist"]}><TripPlanner /></RequireRole>} />
        </Routes>
      </main>
    </div>
  );
}
