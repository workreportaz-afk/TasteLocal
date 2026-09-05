export default function ReviewList({ reviews }) {
  if (!reviews?.length) return <p className="muted">No reviews yet — be the first!</p>;

  return (
    <ul className="review-list">
      {reviews.map((r) => (
        <li key={r.id}>
          <strong>{"★".repeat(r.rating)}</strong> by {r.tourist.username}
          <p>{r.comment}</p>
        </li>
      ))}
    </ul>
  );
}
