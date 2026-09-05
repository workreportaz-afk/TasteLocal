import { useEffect, useState } from "react";
import client from "../api/client.js";
import ExperienceCard from "../components/ExperienceCard.jsx";

const CATEGORIES = [
  ["", "All categories"],
  ["street_food", "Street Food Tour"],
  ["fine_dining", "Fine Dining"],
  ["cooking_class", "Cooking Class"],
  ["market_tour", "Market Tour"],
  ["tasting", "Tasting Session"],
];

export default function Home() {
  const [experiences, setExperiences] = useState([]);
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [nearMe, setNearMe] = useState(null); // {lat, lng} once located
  const [locating, setLocating] = useState(false);
  const [locateError, setLocateError] = useState("");

  useEffect(() => {
    const params = {};
    if (search) params.search = search;
    if (category) params.category = category;
    if (nearMe) {
      params.near = `${nearMe.lat},${nearMe.lng}`;
      params.radius_km = 5;
    }

    setLoading(true);
    client
      .get("/experiences/", { params })
      .then(({ data }) => setExperiences(data.results ?? data))
      .catch(() => setError("Could not load experiences. Is the Django server running?"))
      .finally(() => setLoading(false));
  }, [search, category, nearMe]);

  function handleNearMe() {
    if (nearMe) {
      setNearMe(null); // toggle off
      return;
    }
    if (!navigator.geolocation) {
      setLocateError("Your browser doesn't support location — try searching by name instead.");
      return;
    }
    setLocating(true);
    setLocateError("");
    navigator.geolocation.getCurrentPosition(
      (position) => {
        setNearMe({ lat: position.coords.latitude, lng: position.coords.longitude });
        setLocating(false);
      },
      () => {
        setLocateError("Couldn't get your location — check your browser's location permission.");
        setLocating(false);
      }
    );
  }

  return (
    <div>
      <section className="hero">
        <h1>Discover authentic local food experiences</h1>
        <p>Street food tours, cooking classes, and tastings — booked directly with local vendors.</p>
      </section>

      <div className="filters">
        <input
          type="search"
          placeholder="Search experiences or vendors..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <select value={category} onChange={(e) => setCategory(e.target.value)}>
          {CATEGORIES.map(([value, label]) => (
            <option key={value} value={value}>{label}</option>
          ))}
        </select>
        <button type="button" onClick={handleNearMe} className={nearMe ? "active" : ""}>
          {locating ? "Locating..." : nearMe ? "📍 Near me (on)" : "📍 Near me"}
        </button>
      </div>
      {locateError && <p className="error">{locateError}</p>}

      {loading && <p>Loading experiences...</p>}
      {error && <p className="error">{error}</p>}

      <div className="experience-grid">
        {experiences.map((exp) => (
          <ExperienceCard key={exp.id} experience={exp} />
        ))}
        {!loading && !error && experiences.length === 0 && <p>No experiences match your search.</p>}
      </div>
    </div>
  );
}
