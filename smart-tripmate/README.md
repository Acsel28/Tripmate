# TripMate - Smart Travel Planner (Microservices)

This is a modular microservices implementation of TripMate with automated trip planning logic, affordability checks, and event-style interactions.

## Folder Structure

smart-tripmate/
- api-gateway/
- auth-service/
- trip-service/
- planning-service/
- booking-service/
- expense-service/
- budget-service/
- notification-service/
- frontend/
- k8s/
- docker-compose.yml
- Jenkinsfile
- README.md

## Services and Ports

- api-gateway: 5000
- auth-service: 5001
- trip-service: 5003
- planning-service: 5004
- booking-service: 5005
- expense-service: 5006
- budget-service: 5007
- notification-service: 5008
- frontend (React/Vite): 3000

## Key Flows

1. Planning flow
- Frontend -> api-gateway /plan
- api-gateway -> planning-service /plan
- planning-service -> booking-service (/flights, /trains, /hotels, /activities)
- planning-service -> budget-service /evaluate
- budget-service -> notification-service /notify (if budget exceeded)

2. Expense flow
- expense-service /expenses -> budget-service /evaluate
- budget-service -> notification-service /notify (if budget exceeded)

3. Trip management flow
- trip-service stores trips and prevents overlapping trip date ranges per user.

## Planning Logic

- total_cost = travel_cost + stay_cost + activity_cost + buffer
- Generates 3 plans: cheapest, fastest, balanced
- Checks affordability with budget-service
- Suggests optimizations when all generated plans exceed budget

## Edge Cases Handled

- no travel/hotel options available
- budget too low
- invalid dates
- overlapping trips
- downstream API/service failures

## Run Locally with Docker

From smart-tripmate directory:

```bash
docker compose up -d --build
```

Open frontend:
- http://localhost:3000

Health checks:
- http://localhost:5000/health
- http://localhost:5004/health
- http://localhost:5005/health

Stop:

```bash
docker compose down
```

## Run Tests

```bash
cd planning-service
pytest -q
```

## Kubernetes Deployment

```bash
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
```

Frontend NodePort:
- http://<node-ip>:30080

## Jenkins Pipeline Stages

1. clone repository
2. install dependencies
3. run pytest
4. build docker images
5. deploy to kubernetes
