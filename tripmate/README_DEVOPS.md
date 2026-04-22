# TripMate CI/CD and DevOps Integration

This project now includes a baseline DevOps toolchain using:

1. Flask for the web application
2. Pytest for automated testing
3. Docker for containerization
4. Jenkins for CI/CD orchestration
5. SonarQube for static code quality analysis
6. Ansible for deployment automation

## Recommended integration order

1. Put the project in a Git repository.
2. Verify the app locally with `pytest`.
3. Build the container with Docker.
4. Start SonarQube and Jenkins using Docker Compose.
5. Create a Jenkins pipeline job connected to your repository.
6. Configure the SonarQube server in Jenkins with the name `sonarqube-server`.
7. Run the pipeline so Jenkins tests, scans, builds, and deploys the app.

## Jenkins setup notes

Install these Jenkins plugins:

1. Pipeline
2. Git
3. SonarQube Scanner
4. Docker Pipeline
5. Ansible

If you run Jenkins in Docker, also make sure the Jenkins environment has:

1. Python and pip
2. Docker CLI access
3. Ansible installed
4. Sonar Scanner installed or configured as a Jenkins tool

## How to run locally

From the repository root:

```powershell
docker compose up --build
```

Application URL: `http://localhost:8000`

Jenkins URL: `http://localhost:8080`

SonarQube URL: `http://localhost:9000`

## How the pipeline works

1. Jenkins checks out the source code.
2. Jenkins installs Python dependencies from `tripmate/requirements.txt`.
3. Jenkins runs `pytest` with coverage.
4. Jenkins triggers SonarQube analysis using `sonar-project.properties`.
5. Jenkins builds the Docker image.
6. Jenkins calls Ansible to deploy the updated application using Docker Compose.

## Commands for your report demo

### Run tests

```powershell
cd tripmate
pytest --cov=. --cov-report=xml --cov-report=term
```

### Start the full stack

```powershell
docker compose up -d --build
```

### Initialize a Git repository if you have not already

```powershell
git init
git add .
git commit -m "Initial TripMate CI/CD setup"
```

### Run the Flask app without Docker

```powershell
cd tripmate
python init_db.py
python app.py
```

## Suggested screenshots for submission

1. Home or login page of TripMate running in browser
2. Jenkins pipeline stage view showing successful build
3. SonarQube dashboard showing project analysis
4. Terminal or Jenkins console showing `pytest` execution
5. Docker containers running with `docker compose ps`
6. Ansible playbook output showing deployment success

## Microservices that can be split from this project later

1. Authentication service
2. Itinerary management service
3. Booking service
4. Budget and expense service
5. Report generation service
6. Notification service for booking or budget alerts
7. API gateway service
8. User profile service
9. Payment service if real bookings are added
10. Search and recommendation service for destinations or hotels
