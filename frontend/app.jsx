const { useEffect, useMemo, useRef, useState } = React;

const defaultApiBase = `${window.location.protocol}//${window.location.hostname}:8000`;
const api = axios.create({
  baseURL: window.TRIPMATE_API_URL || defaultApiBase,
});

function MetricCard({ label, value, accent }) {
  return (
    <div className="glass rounded-3xl border border-white/60 p-5 shadow-glow">
      <p className="text-sm uppercase tracking-[0.24em] text-slate-500">{label}</p>
      <p className={`mt-3 text-3xl font-display font-bold ${accent}`}>{value}</p>
    </div>
  );
}

function QuickEstimateCard({ estimate, onCalculate }) {
  return (
    <div className="rounded-3xl bg-white p-6 shadow-glow">
      <div className="flex items-center justify-between gap-4">
        <div>
          <p className="text-sm uppercase tracking-[0.24em] text-slate-400">Instant budget calculator</p>
          <h3 className="mt-2 text-2xl font-display font-bold">Know before you generate</h3>
        </div>
        <button type="button" onClick={onCalculate} className="rounded-2xl bg-ink px-4 py-3 text-sm font-semibold text-white">
          Calculate now
        </button>
      </div>
      <div className="mt-5 grid gap-4 md:grid-cols-4">
        <MetricCard label="Estimated total" value={`$${estimate.total}`} accent="text-coral" />
        <MetricCard label="Budget" value={`$${estimate.budget}`} accent="text-teal" />
        <MetricCard label="Gap" value={`$${estimate.gap}`} accent={estimate.affordable ? "text-emerald-600" : "text-rose-600"} />
        <MetricCard label="Status" value={estimate.affordable ? "Affordable" : "Over"} accent={estimate.affordable ? "text-emerald-600" : "text-rose-600"} />
      </div>
      <p className="mt-4 text-sm text-slate-600">{estimate.message}</p>
    </div>
  );
}

function PlanCard({ plan, isSelected, onChoose }) {
  return (
    <div className={`rounded-3xl bg-white p-6 shadow-glow ${isSelected ? "ring-2 ring-coral" : ""}`}>
      <div className="flex items-center justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-[0.24em] text-slate-400">{plan.plan_type}</p>
          <h3 className="mt-2 text-2xl font-display font-bold">{plan.title}</h3>
        </div>
        <div className="flex items-center gap-3">
          <span className={`rounded-full px-4 py-2 text-sm font-semibold ${plan.affordable ? "bg-emerald-100 text-emerald-700" : "bg-rose-100 text-rose-700"}`}>
            {plan.affordable ? "Affordable" : "Over budget"}
          </span>
          <button type="button" onClick={() => onChoose(plan)} className="rounded-2xl bg-coral px-4 py-3 text-sm font-semibold text-white">
            Choose this trip
          </button>
        </div>
      </div>

      <div className="mt-6 grid gap-3 md:grid-cols-2">
        <div className="rounded-2xl bg-slate-50 p-4">
          <p className="text-sm text-slate-500">Transport</p>
          <p className="mt-1 font-semibold">{plan.transport.mode} via {plan.transport.provider}</p>
          <p className="text-sm text-slate-500">{plan.transport.duration_hours} hrs</p>
        </div>
        <div className="rounded-2xl bg-slate-50 p-4">
          <p className="text-sm text-slate-500">Stay</p>
          <p className="mt-1 font-semibold">{plan.hotel.name}</p>
          <p className="text-sm text-slate-500">{plan.hotel.tier} tier | rating {plan.hotel.rating}</p>
        </div>
      </div>

      <div className="mt-6 grid gap-3 md:grid-cols-4">
        {Object.entries(plan.cost_breakdown).map(([key, value]) => (
          <div key={key} className="rounded-2xl border border-slate-100 p-4">
            <p className="text-xs uppercase tracking-[0.2em] text-slate-400">{key.replace("_", " ")}</p>
            <p className="mt-2 text-lg font-bold text-ink">${value}</p>
          </div>
        ))}
      </div>

      <div className="mt-6">
        <p className="text-sm font-semibold text-slate-600">Savings suggestions</p>
        <ul className="mt-3 space-y-2 text-sm text-slate-600">
          {plan.suggestions.map((item, index) => (
            <li key={index} className="rounded-2xl bg-sand px-4 py-3">{item}</li>
          ))}
        </ul>
      </div>
    </div>
  );
}

function NotificationList({ notifications }) {
  return (
    <div className="rounded-3xl bg-white p-6 shadow-glow">
      <h3 className="text-xl font-display font-bold">Real-time alerts</h3>
      <div className="mt-4 space-y-3">
        {notifications.length === 0 && <p className="text-slate-500">No alerts yet. Budget and planning warnings will appear here.</p>}
        {notifications.map((note) => (
          <div key={note.id} className="rounded-2xl border border-slate-100 p-4">
            <div className="flex items-center justify-between">
              <p className="font-semibold">{note.title}</p>
              <span className={`rounded-full px-3 py-1 text-xs font-semibold ${note.level === "warning" ? "bg-amber-100 text-amber-700" : "bg-sky-100 text-sky-700"}`}>{note.level}</span>
            </div>
            <p className="mt-2 text-sm text-slate-600">{note.message}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

function ExpenseTracker({ expenseForm, onChange, onSubmit }) {
  return (
    <div className="rounded-3xl bg-white p-6 shadow-glow">
      <div className="flex items-center justify-between gap-4">
        <div>
          <p className="text-sm uppercase tracking-[0.24em] text-slate-400">Expense tracking</p>
          <h3 className="mt-2 text-2xl font-display font-bold">Update budget in one click</h3>
        </div>
        <button type="button" onClick={onSubmit} className="rounded-2xl bg-teal px-4 py-3 text-sm font-semibold text-white">
          Add expense
        </button>
      </div>
      <div className="mt-5 grid gap-4 md:grid-cols-4">
        <input className="rounded-2xl border border-slate-200 px-4 py-3" placeholder="Category" value={expenseForm.category} onChange={(e) => onChange("category", e.target.value)} />
        <input className="rounded-2xl border border-slate-200 px-4 py-3" placeholder="Amount" type="number" value={expenseForm.amount} onChange={(e) => onChange("amount", Number(e.target.value))} />
        <input className="rounded-2xl border border-slate-200 px-4 py-3" type="date" value={expenseForm.date} onChange={(e) => onChange("date", e.target.value)} />
        <input className="rounded-2xl border border-slate-200 px-4 py-3" placeholder="Description" value={expenseForm.description} onChange={(e) => onChange("description", e.target.value)} />
      </div>
    </div>
  );
}

function App() {
  const [user, setUser] = useState(null);
  const [authForm, setAuthForm] = useState({ mode: "register", name: "Travel Demo", email: "demo@tripmate.ai", password: "secret123" });
  const [plannerForm, setPlannerForm] = useState({
    source_city: "Delhi",
    destination_city: "Goa",
    start_date: "2026-06-18",
    end_date: "2026-06-22",
    budget: 1600,
    traveler_count: 2,
    preferences: { activity_level: "medium" }
  });
  const [expenseForm, setExpenseForm] = useState({
    category: "Meals",
    amount: 120,
    date: "2026-06-19",
    description: "Dinner and taxi",
  });
  const [dashboard, setDashboard] = useState(null);
  const [planResult, setPlanResult] = useState(null);
  const [selectedPlan, setSelectedPlan] = useState(null);
  const [error, setError] = useState("");
  const [status, setStatus] = useState("");
  const [localEstimate, setLocalEstimate] = useState({
    total: 0,
    budget: 1600,
    gap: 0,
    affordable: true,
    message: "Use the calculator to preview affordability before generating a trip.",
  });
  const chartRef = useRef(null);
  const chartInstance = useRef(null);

  const loadDashboard = async (userId) => {
    const { data } = await api.get(`/api/users/${userId}/dashboard`);
    setDashboard(data);
  };

  const recommendedPlan = useMemo(() => {
    if (!planResult?.plans?.length) return null;
    return planResult.plans.find((plan) => plan.affordable && plan.plan_type === "balanced")
      || planResult.plans.find((plan) => plan.affordable)
      || planResult.plans.find((plan) => plan.plan_type === "cheapest")
      || planResult.plans[0];
  }, [planResult]);

  useEffect(() => {
    if (recommendedPlan) {
      setSelectedPlan(recommendedPlan);
    }
  }, [recommendedPlan]);

  useEffect(() => {
    if (!dashboard?.budget || !chartRef.current) return;
    const budget = dashboard.budget.budget?.total_budget || 0;
    const spent = dashboard.budget.total_expenses || 0;
    const remaining = Math.max((dashboard.budget.remaining || 0), 0);
    chartInstance.current?.destroy();
    chartInstance.current = new Chart(chartRef.current, {
      type: "doughnut",
      data: {
        labels: ["Spent", "Remaining"],
        datasets: [{
          data: [spent, remaining || Math.max(budget - spent, 0)],
          backgroundColor: ["#ff7a59", "#0d9488"],
          borderWidth: 0
        }]
      },
      options: {
        plugins: { legend: { position: "bottom" } },
        cutout: "68%"
      }
    });
  }, [dashboard]);

  const calculateEstimate = () => {
    const days = Math.max(1, Math.round((new Date(plannerForm.end_date) - new Date(plannerForm.start_date)) / (1000 * 60 * 60 * 24)) + 1);
    const activityRate = { low: 25, medium: 45, high: 75 }[plannerForm.preferences.activity_level] || 45;
    const transport = 140 * plannerForm.traveler_count;
    const hotel = 85 * Math.max(days - 1, 1);
    const activities = activityRate * days * plannerForm.traveler_count;
    const total = Math.round((transport + hotel + activities) * 1.12);
    const gap = Math.abs(total - plannerForm.budget);
    const affordable = total <= plannerForm.budget;

    setLocalEstimate({
      total,
      budget: plannerForm.budget,
      gap,
      affordable,
      message: affordable
        ? "This trip looks financially possible. Generate plans to compare cheapest, fastest, and balanced options."
        : "This preview is over budget. Try a lower activity level, fewer travelers, or a shorter trip.",
    });
  };

  const handleAuth = async (event) => {
    event.preventDefault();
    setError("");
    setStatus("");
    try {
      const path = authForm.mode === "register" ? "/api/auth/register" : "/api/auth/login";
      const payload = authForm.mode === "register" ? authForm : { email: authForm.email, password: authForm.password };
      const { data } = await api.post(path, payload);
      setUser(data);
      await api.post(`/api/users/${data.id}/budget`, { total_budget: plannerForm.budget });
      await loadDashboard(data.id);
      setStatus("Workspace ready. You can calculate budget, generate plans, and track expenses now.");
    } catch (err) {
      setError(err.response?.data?.error || "Authentication failed.");
    }
  };

  const handlePlan = async (event) => {
    event.preventDefault();
    setError("");
    setStatus("");
    if (!user) {
      setError("Register or log in before generating a trip.");
      return;
    }
    try {
      await api.post(`/api/users/${user.id}/trips`, plannerForm);
      const { data } = await api.post(`/api/users/${user.id}/plan`, plannerForm);
      setPlanResult(data);
      await loadDashboard(user.id);
      setStatus("Trip plans generated. Compare the cards and use 'Choose this trip' on the best one.");
    } catch (err) {
      setError(err.response?.data?.error || "Unable to build trip plan.");
    }
  };

  const handleExpense = async () => {
    if (!user) {
      setError("Log in first to track expenses.");
      return;
    }
    setError("");
    setStatus("");
    try {
      await api.post(`/api/users/${user.id}/expenses`, expenseForm);
      await loadDashboard(user.id);
      setStatus("Expense added and budget health refreshed.");
    } catch (err) {
      setError(err.response?.data?.error || "Expense update failed.");
    }
  };

  return (
    <div className="hero-grid min-h-screen px-4 py-6 md:px-8">
      <div className="mx-auto max-w-7xl">
        <section className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
          <div className="rounded-[2rem] bg-ink px-8 py-10 text-white shadow-glow">
            <p className="text-sm uppercase tracking-[0.3em] text-orange-200">Smart Travel Planning & Optimization</p>
            <h1 className="mt-4 max-w-2xl text-5xl font-display font-bold leading-tight">
              TripMate now tells you which trip to take, why, and whether your budget can survive it.
            </h1>
            <p className="mt-4 max-w-2xl text-base text-slate-200">
              The workflow is: create your workspace, calculate affordability, generate plans, compare options, choose a recommendation, and then track real expenses against the saved budget.
            </p>
            <div className="mt-8 grid gap-4 md:grid-cols-3">
              <MetricCard label="Microservices" value="10+" accent="text-orange-300" />
              <MetricCard label="DevOps Flow" value="CI/CD + Monitoring" accent="text-teal-300" />
              <MetricCard label="Decision Modes" value="3 Plans" accent="text-sky-300" />
            </div>
          </div>

          <form onSubmit={handleAuth} className="glass rounded-[2rem] border border-white/60 p-6 shadow-glow">
            <div className="flex gap-2 rounded-full bg-slate-100 p-1 text-sm">
              {["register", "login"].map((mode) => (
                <button type="button" key={mode} onClick={() => setAuthForm({ ...authForm, mode })} className={`flex-1 rounded-full px-4 py-2 font-semibold ${authForm.mode === mode ? "bg-white text-ink shadow" : "text-slate-500"}`}>
                  {mode}
                </button>
              ))}
            </div>
            <h2 className="mt-6 text-2xl font-display font-bold">Start your planning workspace</h2>
            {authForm.mode === "register" && (
              <input className="mt-4 w-full rounded-2xl border border-slate-200 px-4 py-3" placeholder="Your name" value={authForm.name} onChange={(e) => setAuthForm({ ...authForm, name: e.target.value })} />
            )}
            <input className="mt-4 w-full rounded-2xl border border-slate-200 px-4 py-3" placeholder="Email" value={authForm.email} onChange={(e) => setAuthForm({ ...authForm, email: e.target.value })} />
            <input type="password" className="mt-4 w-full rounded-2xl border border-slate-200 px-4 py-3" placeholder="Password" value={authForm.password} onChange={(e) => setAuthForm({ ...authForm, password: e.target.value })} />
            <button className="mt-4 w-full rounded-2xl bg-coral px-4 py-3 font-semibold text-white">{authForm.mode === "register" ? "Create workspace" : "Continue planning"}</button>
            {user && <p className="mt-4 text-sm text-emerald-700">Signed in as {user.name} (user #{user.id})</p>}
            {status && <p className="mt-4 text-sm text-emerald-700">{status}</p>}
            {error && <p className="mt-4 text-sm text-rose-600">{error}</p>}
          </form>
        </section>

        <section className="mt-6 space-y-6">
          <QuickEstimateCard estimate={localEstimate} onCalculate={calculateEstimate} />

          <div className="grid gap-6 xl:grid-cols-[0.95fr_1.05fr]">
            <form onSubmit={handlePlan} className="rounded-[2rem] bg-white p-6 shadow-glow">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm uppercase tracking-[0.24em] text-slate-400">Trip planner</p>
                  <h2 className="mt-2 text-3xl font-display font-bold">Generate optimized trip plans</h2>
                </div>
              </div>
              <div className="mt-6 grid gap-4 md:grid-cols-2">
                {[
                  ["source_city", "Source city"],
                  ["destination_city", "Destination"],
                  ["start_date", "Start date"],
                  ["end_date", "End date"],
                  ["budget", "Budget"],
                  ["traveler_count", "Traveler count"],
                ].map(([field, label]) => (
                  <label key={field} className="block">
                    <span className="mb-2 block text-sm font-medium text-slate-600">{label}</span>
                    <input
                      type={field.includes("date") ? "date" : field === "budget" || field === "traveler_count" ? "number" : "text"}
                      className="w-full rounded-2xl border border-slate-200 px-4 py-3"
                      value={plannerForm[field]}
                      onChange={(e) => setPlannerForm({ ...plannerForm, [field]: ["budget", "traveler_count"].includes(field) ? Number(e.target.value) : e.target.value })}
                    />
                  </label>
                ))}
              </div>
              <label className="mt-4 block">
                <span className="mb-2 block text-sm font-medium text-slate-600">Activity intensity</span>
                <select className="w-full rounded-2xl border border-slate-200 px-4 py-3" value={plannerForm.preferences.activity_level} onChange={(e) => setPlannerForm({ ...plannerForm, preferences: { activity_level: e.target.value } })}>
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                </select>
              </label>
              <div className="mt-6 flex gap-3">
                <button type="button" onClick={calculateEstimate} className="flex-1 rounded-2xl border border-ink px-4 py-3 font-semibold text-ink">Preview budget</button>
                <button className="flex-1 rounded-2xl bg-teal px-4 py-3 font-semibold text-white">Generate trip intelligence</button>
              </div>
            </form>

            <div className="grid gap-6">
              <div className="rounded-[2rem] bg-white p-6 shadow-glow">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm uppercase tracking-[0.24em] text-slate-400">Affordability analysis</p>
                    <h2 className="mt-2 text-3xl font-display font-bold">Budget health</h2>
                  </div>
                </div>
                <div className="mt-4 grid gap-4 md:grid-cols-[0.9fr_1.1fr]">
                  <div className="flex items-center justify-center">
                    <canvas ref={chartRef} height="220"></canvas>
                  </div>
                  <div className="grid gap-4">
                    <MetricCard label="Budget" value={`$${dashboard?.budget?.budget?.total_budget || plannerForm.budget}`} accent="text-coral" />
                    <MetricCard label="Tracked Expenses" value={`$${dashboard?.budget?.total_expenses || 0}`} accent="text-teal" />
                    <MetricCard label="Remaining" value={`$${dashboard?.budget?.remaining || plannerForm.budget}`} accent="text-sky-500" />
                  </div>
                </div>
              </div>
              <NotificationList notifications={dashboard?.notifications || []} />
            </div>
          </div>
        </section>

        <section className="mt-6">
          <ExpenseTracker
            expenseForm={expenseForm}
            onChange={(field, value) => setExpenseForm({ ...expenseForm, [field]: value })}
            onSubmit={handleExpense}
          />
        </section>

        {selectedPlan && (
          <section className="mt-6 rounded-[2rem] bg-ink p-6 text-white shadow-glow">
            <p className="text-sm uppercase tracking-[0.24em] text-orange-200">TripMate recommendation</p>
            <h2 className="mt-2 text-3xl font-display font-bold">Trip to take right now: {selectedPlan.title}</h2>
            <p className="mt-3 max-w-3xl text-slate-200">
              {selectedPlan.affordable
                ? `This is the best recommendation because it stays within budget and gives the strongest overall tradeoff between comfort, speed, and cost.`
                : `This is the best fallback recommendation because every plan is over budget, and this one keeps the cost closest to what you can afford.`}
            </p>
          </section>
        )}

        {planResult && (
          <section className="mt-6 space-y-6">
            <div className="rounded-[2rem] bg-white p-6 shadow-glow">
              <p className="text-sm uppercase tracking-[0.24em] text-slate-400">Cheaper alternatives</p>
              <div className="mt-4 grid gap-4 md:grid-cols-2">
                {planResult.cheaper_alternatives.map((item, index) => (
                  <div key={index} className="rounded-2xl bg-slate-50 p-4">
                    <p className="text-sm font-semibold capitalize">{item.type}</p>
                    <p className="mt-2 text-sm text-slate-600">{item.message}</p>
                  </div>
                ))}
              </div>
            </div>
            {planResult.plans.map((plan) => (
              <PlanCard
                key={plan.plan_type}
                plan={plan}
                isSelected={selectedPlan?.plan_type === plan.plan_type}
                onChoose={setSelectedPlan}
              />
            ))}
          </section>
        )}
      </div>
    </div>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(<App />);
