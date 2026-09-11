import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import client from "../api/client.js";
import { useAuth } from "../context/AuthContext.jsx";

/**
 * Shows a "write a review" form only when the logged-in tourist has at
 * least one completed booking for this experience that they haven't
 * reviewed yet -- matching the backend rule in ReviewSerializer.validate_booking.
 * Previously there was no UI for this at all, so a tourist could never
 * submit a review even after logging in and completing a booking.
 */
export default function ReviewForm({ experienceId, onReviewAdded }) {
  const { t } = useTranslation();
  const { isAuthenticated } = useAuth();
  const [eligibleBooking, setEligibleBooking] = useState(null);
  const [rating, setRating] = useState(5);
  const [comment, setComment] = useState("");
  const [message, setMessage] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!isAuthenticated) {
      setEligibleBooking(null);
      return;
    }
    client
      .get("/bookings/", { params: { experience: experienceId, status: "completed" } })
      .then(({ data }) => {
        const bookings = data.results ?? data;
        const unreviewed = bookings.find((b) => !b.has_review);
        setEligibleBooking(unreviewed ?? null);
      });
  }, [experienceId, isAuthenticated]);

  async function handleSubmit(e) {
    e.preventDefault();
    setMessage("");
    setSubmitting(true);
    try {
      await client.post("/reviews/", {
        booking: eligibleBooking.id,
        rating,
        comment,
      });
      setEligibleBooking(null);
      setComment("");
      setRating(5);
      onReviewAdded?.();
    } catch (err) {
      setMessage(
        err.response?.data?.booking?.[0] ||
        err.response?.data?.non_field_errors?.[0] ||
        t("review.submitFailed")
      );
    } finally {
      setSubmitting(false);
    }
  }

  if (!isAuthenticated || !eligibleBooking) return null;

  return (
    <form onSubmit={handleSubmit} className="review-form">
      <h3>{t("review.writeReview")}</h3>
      <label>
        {t("review.rating")}
        <select value={rating} onChange={(e) => setRating(Number(e.target.value))}>
          {[5, 4, 3, 2, 1].map((n) => (
            <option key={n} value={n}>{"★".repeat(n)} ({n})</option>
          ))}
        </select>
      </label>
      <label>
        {t("review.comment")}
        <textarea value={comment} onChange={(e) => setComment(e.target.value)} rows={3} />
      </label>
      <button type="submit" disabled={submitting}>{t("review.submit")}</button>
      {message && <p className="error">{message}</p>}
    </form>
  );
}
