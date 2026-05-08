# TripMate Project Structure

```text
tripmate1/
|-- ansible/
|-- frontend/
|-- jenkins/
|-- monitoring/
|-- tripmate/
|   |-- microservices/
|   |-- tests/
|   |-- api_gateway_app.py
|   |-- planning_engine.py
|   |-- catalog.py
|   |-- recommendation_engine.py
|   `-- schema.sql
|-- Dockerfile
|-- Dockerfile.service
|-- docker-compose.yml
|-- Jenkinsfile
`-- sonar-project.properties
```

## Key folders

1. `frontend/` contains the React dashboard service.
2. `tripmate/microservices/` contains Flask microservices.
3. `tripmate/tests/` contains pytest coverage for service flows and planning logic.
4. `monitoring/` contains Prometheus scrape config and Grafana provisioning.
5. `ansible/` contains the preserved deployment entrypoint extended for Docker and monitoring.
