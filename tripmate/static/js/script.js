document.addEventListener('DOMContentLoaded', function() {
    console.log('TripMate loaded successfully');
    
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 300);
        }, 3000);
    });

    const kpiTrips = document.getElementById('kpi-total-trips');
    const kpiTripCost = document.getElementById('kpi-total-trip-cost');
    const kpiExpenses = document.getElementById('kpi-total-expenses');
    const kpiRemaining = document.getElementById('kpi-remaining-budget');
    const notificationList = document.getElementById('notification-list');

    if (!kpiTrips || !notificationList) {
        return;
    }

    const toMoney = (value) => `$${Number(value || 0).toFixed(2)}`;

    const renderNotifications = (notifications) => {
        if (!Array.isArray(notifications) || notifications.length === 0) {
            notificationList.innerHTML = '<p id="no-notification-text">No alerts yet.</p>';
            return;
        }

        notificationList.innerHTML = notifications
            .map((note) => {
                const severity = note.severity || 'info';
                return `
                    <div class="notification-item notification-${severity}">
                        <strong>${note.title || 'Notification'}</strong>
                        <p>${note.message || ''}</p>
                    </div>
                `;
            })
            .join('');
    };

    const refreshDashboard = async () => {
        try {
            const response = await fetch('/api/dashboard/summary', {
                method: 'GET',
                headers: { 'Accept': 'application/json' },
            });
            if (!response.ok) {
                return;
            }

            const data = await response.json();
            const metrics = data.metrics || {};

            kpiTrips.textContent = metrics.total_trips ?? 0;
            kpiTripCost.textContent = toMoney(metrics.total_trip_cost ?? 0);
            kpiExpenses.textContent = toMoney(metrics.total_expenses ?? 0);
            kpiRemaining.textContent = metrics.has_budget ? toMoney(metrics.remaining_budget ?? 0) : 'Not set';

            renderNotifications(data.notifications || []);
        } catch (error) {
            console.warn('Dashboard refresh failed', error);
        }
    };

    setInterval(refreshDashboard, 10000);
});
