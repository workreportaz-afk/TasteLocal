import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import client from "../api/client.js";
import ExperienceCard from "../components/ExperienceCard.jsx";

const CATEGORY_VALUES = ["", "street_food", "fine_dining", "cooking_class", "market_tour", "tasting"];

export default function Home() {
  const { t } = useTranslation();
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
      .catch(() => setError(t("home.loadError")))
      .finally(() => setLoading(false));
  }, [search, category, nearMe, t]);

  function handleNearMe() {
    if (nearMe) {
      setNearMe(null); // toggle off
      return;
    }
    if (!navigator.geolocation) {
      setLocateError(t("home.locationUnsupported"));
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
        setLocateError(t("home.locationDenied"));
        setLocating(false);
      }
    );
  }

  return (
    <div>
      <section className="hero">
        <h1>{t("home.title")}</h1>
        <p>{t("home.subtitle")}</p>
      </section>

      <div className="filters">
        <input
          type="search"
          placeholder={t("home.searchPlaceholder")}
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <select value={category} onChange={(e) => setCategory(e.target.value)}>
          {CATEGORY_VALUES.map((value) => (
            <option key={value} value={value}>
              {value === "" ? t("home.allCategories") : t(`category.${value}`)}
            </option>
          ))}
        </select>
        <button type="button" onClick={handleNearMe} className={nearMe ? "active" : ""}>
          {locating ? t("home.locating") : nearMe ? t("home.nearMeOn") : t("home.nearMe")}
        </button>
      </div>
      {locateError && <p className="error">{locateError}</p>}

      {loading && <p>{t("home.loading")}</p>}
      {error && <p className="error">{error}</p>}

      <div className="experience-grid">
        {experiences.map((exp) => (
          <ExperienceCard key={exp.id} experience={exp} />
        ))}
        {!loading && !error && experiences.length === 0 && <p>{t("home.noResults")}</p>}
      </div>
    </div>
  );
}
