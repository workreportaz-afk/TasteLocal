import { useEffect, useState } from "react";
import client from "../api/client.js";

export default function Bookings() {
  const [bookings, setBookings] = useState([]);

  useEffect(() => {
    client.get("/bookings/").then(({ data }) => setBookings(data.results ?? data));
  }, []);

  return (
    <div>
      <h1>My Bookings</h1>
      <table className="bookings-table">
        <thead>
          <tr>
            <th>Experience</th>
            <th>Date</th>
            <th>Participants</th>
            <th>Total</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {bookings.map((b) => (
            <tr key={b.id}>
              <td>{b.experience_title}</td>
              <td>{new Date(b.booking_date).toLocaleString()}</td>
              <td>{b.number_of_participants}</td>
              <td>${b.total_price}</td>
              <td><span className={`status status-${b.status}`}>{b.status}</span></td>
            </tr>
          ))}
        </tbody>
      </table>
      {bookings.length === 0 && <p>You haven't booked any experiences yet.</p>}
    </div>
  );
}
