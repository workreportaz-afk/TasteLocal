import { Routes, Route } from "react-router-dom";
import NavBar from "./components/NavBar.jsx";
import Home from "./pages/Home.jsx";
import ExperienceDetail from "./pages/ExperienceDetail.jsx";
import Bookings from "./pages/Bookings.jsx";
import Login from "./pages/Login.jsx";
import VendorDashboard from "./pages/VendorDashboard.jsx";
import Saved from "./pages/Saved.jsx";
import PlanMyTrip from "./pages/PlanMyTrip.jsx";

export default function App() {
  return (
    <div className="app-shell">
      <NavBar />
      <main className="app-content">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/experiences/:id" element={<ExperienceDetail />} />
          <Route path="/bookings" element={<Bookings />} />
          <Route path="/login" element={<Login />} />
          <Route path="/vendor" element={<VendorDashboard />} />
          <Route path="/saved" element={<Saved />} />
          <Route path="/trip" element={<PlanMyTrip />} />
        </Routes>
      </main>
    </div>
  );
}
