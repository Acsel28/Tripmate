import React from 'react';

const API = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000';

const initialForm = {
  user_id: 'guest-1',
  source_city: 'Delhi',
  destination_city: 'Mumbai',
  start_date: '2026-05-01',
  end_date: '2026-05-05',
  budget: 9000,
  preferences: {
    transport_type: 'flight',
    hotel_type: 'budget',
  },
};

export default function App() {
  const [form, setForm] = React.useState(initialForm);
  const [result, setResult] = React.useState(null);
  const [error, setError] = React.useState('');
  const [loading, setLoading] = React.useState(false);
  const [notifications, setNotifications] = React.useState([]);

  const metrics = React.useMemo(() => {
    if (!result) {
      return { totalTrips: 0, totalExpense: 0, remaining: 0 };
    }
    const cheapest = result.plans?.find((p) => p.plan_type === 'cheapest') || result.plans?.[0];
    const totalExpense = cheapest ? cheapest.total_cost : 0;
    const remaining = result.budget_assessment ? result.budget_assessment.remaining : 0;
    return { totalTrips: 1, totalExpense, remaining };
  }, [result]);

  async function submit(e) {
    e.preventDefault();
    setLoading(true);
    setError('');
    setResult(null);
    try {
      const resp = await fetch(`${API}/plan`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      });
      const data = await resp.json();
      if (!resp.ok) {
        throw new Error(data.error || 'Failed to generate plans');
      }
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function loadNotifications() {
    try {
      const resp = await fetch(`${API}/notifications?user_id=${encodeURIComponent(form.user_id)}`);
      const data = await resp.json();
      if (resp.ok) {
        setNotifications(data.notifications || []);
      }
    } catch {
      // ignore polling errors in UI
    }
  }

  React.useEffect(() => {
    loadNotifications();
    const id = setInterval(loadNotifications, 8000);
    return () => clearInterval(id);
  }, [form.user_id]);

  return (
    <div className="page">
      <h1>TripMate Smart Travel Planner</h1>
      <div className="metrics">
        <div className="card"><h3>Total Trips</h3><p>{metrics.totalTrips}</p></div>
        <div className="card"><h3>Total Expenses</h3><p>{metrics.totalExpense}</p></div>
        <div className="card"><h3>Remaining Budget</h3><p>{metrics.remaining}</p></div>
      </div>

      <form className="planner-form" onSubmit={submit}>
        <input value={form.user_id} onChange={(e) => setForm({ ...form, user_id: e.target.value })} placeholder="User ID" />
        <input value={form.source_city} onChange={(e) => setForm({ ...form, source_city: e.target.value })} placeholder="Source city" />
        <input value={form.destination_city} onChange={(e) => setForm({ ...form, destination_city: e.target.value })} placeholder="Destination city" />
        <input type="date" value={form.start_date} onChange={(e) => setForm({ ...form, start_date: e.target.value })} />
        <input type="date" value={form.end_date} onChange={(e) => setForm({ ...form, end_date: e.target.value })} />
        <input type="number" value={form.budget} onChange={(e) => setForm({ ...form, budget: Number(e.target.value) })} placeholder="Budget" />
        <select value={form.preferences.transport_type} onChange={(e) => setForm({ ...form, preferences: { ...form.preferences, transport_type: e.target.value } })}>
          <option value="flight">Flight</option>
          <option value="train">Train</option>
        </select>
        <select value={form.preferences.hotel_type} onChange={(e) => setForm({ ...form, preferences: { ...form.preferences, hotel_type: e.target.value } })}>
          <option value="budget">Budget</option>
          <option value="standard">Standard</option>
          <option value="luxury">Luxury</option>
        </select>
        <button type="submit" disabled={loading}>{loading ? 'Planning...' : 'Generate Plans'}</button>
      </form>

      {error && <div className="error">{error}</div>}

      {result && (
        <section>
          <h2>Generated Plans</h2>
          <div className="plans">
            {(result.plans || []).map((plan) => (
              <div className="card" key={plan.plan_type}>
                <h3>{plan.plan_type}</h3>
                <p>Transport: {plan.travel.from_city} to {plan.travel.to_city} ({plan.travel.duration} mins)</p>
                <p>Hotel: {plan.hotel.type} ({plan.hotel.price_per_night}/night)</p>
                <p>Total cost: {plan.total_cost}</p>
                <p>Status: {plan.affordability}</p>
              </div>
            ))}
          </div>
          {result.suggestions?.length > 0 && (
            <div className="card">
              <h3>Optimization Suggestions</h3>
              <ul>
                {result.suggestions.map((s) => <li key={s}>{s}</li>)}
              </ul>
            </div>
          )}
        </section>
      )}

      <section>
        <h2>Alerts</h2>
        <div className="plans">
          {notifications.length === 0 && <p>No alerts yet.</p>}
          {notifications.map((n) => (
            <div className="card" key={n.id || `${n.user_id}-${n.message}`}>
              <p><strong>{n.level || 'info'}</strong></p>
              <p>{n.message}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
