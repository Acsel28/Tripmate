# TripMate API Documentation

Base URL through the gateway:

- Docker/local: `http://localhost:8000`
- Kubernetes gateway NodePort: `http://<minikube-ip>:30081`

## Auth

### `POST /api/auth/register`

Request:

```json
{
  "name": "Travel Demo",
  "email": "demo@tripmate.ai",
  "password": "secret123"
}
```

### `POST /api/auth/login`

Request:

```json
{
  "email": "demo@tripmate.ai",
  "password": "secret123"
}
```

## Trips

### `POST /api/users/{user_id}/trips`

Creates a trip request and fetches recommendations.

```json
{
  "source_city": "Delhi",
  "destination_city": "Goa",
  "start_date": "2026-06-18",
  "end_date": "2026-06-22",
  "budget": 1600,
  "traveler_count": 2,
  "preferences": {
    "activity_level": "medium"
  }
}
```

## Planning

### `POST /api/users/{user_id}/plan`

Generates `cheapest`, `fastest`, and `balanced` plans.

Response fields:

1. `request`
2. `budget_summary`
3. `plans`
4. `cheaper_alternatives`

Each plan contains:

1. `plan_type`
2. `title`
3. `affordable`
4. `summary`
5. `transport`
6. `hotel`
7. `activities`
8. `cost_breakdown`
9. `suggestions`

## Budget

### `POST /api/users/{user_id}/budget`

```json
{
  "total_budget": 1600
}
```

## Expenses

### `POST /api/users/{user_id}/expenses`

```json
{
  "category": "Meals",
  "amount": 140,
  "date": "2026-06-19",
  "description": "Beachside dinner"
}
```

## Dashboard

### `GET /api/users/{user_id}/dashboard`

Returns:

1. `trips`
2. `notifications`
3. `budget`
4. `report`

## Health endpoints

Every microservice exposes `GET /health`.

## Common failure responses

1. `400` for invalid dates, missing fields, or no routes.
2. `401` for invalid login.
3. `409` for duplicate registration.
4. `503` for downstream service failure.
