import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";

export default function ExperienceCard({ experience }) {
  const { t } = useTranslation();
  return (
    <Link to={`/experiences/${experience.id}`} className="experience-card">
      {experience.image && <img src={experience.image} alt={experience.title} />}
      <div className="experience-card-body">
        <h3>{experience.title}</h3>
        <p className="muted">{experience.vendor_name}</p>
        <p className="category-tag">{t(`category.${experience.category}`)}</p>
        <div className="experience-card-footer">
          <span>${experience.price}</span>
          <span>{experience.average_rating ? `★ ${experience.average_rating}` : t("home.noReviewsYet")}</span>
        </div>
        {experience.distance_km != null && (
          <p className="muted distance-badge">{t("home.distanceAway", { distance: experience.distance_km })}</p>
        )}
      </div>
    </Link>
  );
}
