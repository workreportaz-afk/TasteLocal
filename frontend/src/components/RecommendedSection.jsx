import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import client from "../api/client.js";
import { useAuth } from "../context/AuthContext.jsx";
import ExperienceCard from "./ExperienceCard.jsx";

/**
 * "Recommended For You" -- content-based ranking from the tourist's own
 * saved/booked/itinerary history (see core/recommendations.py on the
 * backend). Not shown for logged-out visitors or non-tourist roles, since
 * there's no personal history to base anything on.
 */
export default function RecommendedSection() {
  const { t, i18n } = useTranslation();
  const { isAuthenticated, role } = useAuth();
  const [recommendations, setRecommendations] = useState([]);

  useEffect(() => {
    if (!isAuthenticated || (role !== "tourist" && role !== "admin")) return;
    client.get("/experiences/recommended/").then(({ data }) => setRecommendations(data));
  }, [isAuthenticated, role, i18n.language]);

  if (!isAuthenticated || (role !== "tourist" && role !== "admin") || recommendations.length === 0) {
    return null;
  }

  return (
    <section className="recommended-section">
      <h2>{t("recommended.title")} ✨</h2>
      <p className="muted">{t("recommended.subtitle")}</p>
      <div className="experience-grid">
        {recommendations.map((exp) => (
          <ExperienceCard key={exp.id} experience={exp} />
        ))}
      </div>
    </section>
  );
}
