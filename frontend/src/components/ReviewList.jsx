import { useTranslation } from "react-i18next";

export default function ReviewList({ reviews }) {
  const { t } = useTranslation();
  if (!reviews?.length) return <p className="muted">{t("review.empty")}</p>;

  return (
    <ul className="review-list">
      {reviews.map((r) => (
        <li key={r.id}>
          <strong>{"★".repeat(r.rating)}</strong> {t("review.by", { name: r.tourist.username })}
          <p>{r.comment}</p>
        </li>
      ))}
    </ul>
  );
}
