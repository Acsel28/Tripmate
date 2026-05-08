# TripMate Smart Travel Planning Platform

TripMate is now structured as a Docker-first travel optimization platform with Jenkins CI/CD, SonarQube quality checks, and Prometheus/Grafana monitoring built on top of the existing Flask microservices foundation.

## Current service map

1. `frontend`
2. `api-gateway`
3. `auth-service`
4. `trip-service`
5. `planning-service`
6. `booking-service`
7. `expense-service`
8. `budget-service`
9. `notification-service`
10. `recommendation-service`
11. `itinerary-service`
12. `reporting-service`
13. `prometheus`
14. `grafana`

## What changed

1. Added a modern React dashboard frontend served as its own service.
2. Added planning, trip, notification, recommendation, and expense microservices.
3. Preserved the original Docker and Ansible integration and extended them.
4. Added health checks, service networking, and new CI/CD flow in Jenkins.
5. Replaced the active Minikube/Kubernetes workflow with Prometheus and Grafana monitoring.
6. Added smarter planning logic for affordability, cheapest, fastest, and balanced trip modes.

## Website workflow

1. User registers or logs in.
2. User enters source, destination, dates, travelers, budget, and activity level.
3. Frontend can do an instant budget preview before any backend planning call.
4. `trip-service` stores the trip and fetches destination advice from `recommendation-service`.
5. `planning-service` fetches transport and hotel options from `booking-service`.
6. `planning-service` computes `cheapest`, `fastest`, and `balanced` plans.
7. Frontend highlights the recommended trip and lets the user choose one.
8. User can add real expenses and `expense-service` updates the budget picture.
9. `notification-service` warns the user when plans or expenses exceed budget.

## DevOps flow

1. Jenkins checks out the latest Git code.
2. Jenkins installs Python dependencies.
3. Jenkins runs `pytest`.
4. Jenkins runs SonarQube scanning.
5. Jenkins builds Docker images for the application services.
6. Jenkins runs the Ansible deployment entrypoint.
7. Ansible refreshes Docker Compose.
8. Jenkins verifies health of the app, Prometheus, and Grafana.
9. Jenkins shuts the stack down on deployment failure.

## Monitoring URLs

1. Frontend: `http://localhost:3000`
2. API gateway: `http://localhost:8000`
3. Jenkins: `http://localhost:8080`
4. SonarQube: `http://localhost:9000`
5. Prometheus: `http://localhost:9090`
6. Grafana: `http://localhost:3001`
