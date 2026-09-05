import { Link } from "react-router-dom";

export default function ExperienceCard({ experience }) {
  return (
    <Link to={`/experiences/${experience.id}`} className="experience-card">
      {experience.image && <img src={experience.image} alt={experience.title} />}
      <div className="experience-card-body">
        <h3>{experience.title}</h3>
        <p className="muted">{experience.vendor_name}</p>
        <p className="category-tag">{experience.category.replace("_", " ")}</p>
        <div className="experience-card-footer">
          <span>${experience.price}</span>
          <span>{experience.average_rating ? `★ ${experience.average_rating}` : "No reviews yet"}</span>
        </div>
        {experience.distance_km != null && (
          <p className="muted distance-badge">{experience.distance_km} km away</p>
        )}
      </div>
    </Link>
  );
}
