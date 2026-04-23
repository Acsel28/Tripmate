# TripMate Professor Demo Guide

## What this integration shows

This project demonstrates a web application integrated with a DevOps workflow using:

1. Flask for the application
2. Pytest for automated testing
3. Docker for containerization
4. Jenkins for CI/CD
5. SonarQube for code quality analysis
6. Ansible for deployment automation

## Architecture you can explain

1. The TripMate web app is now a gateway service that keeps the same pages and user flows.
2. Authentication logic runs in `auth-service`.
3. Itinerary and booking logic run in `travel-service`.
4. Budget and expense logic run in `finance-service`.
5. Services are containerized and orchestrated together with Docker Compose.
6. The shared SQLite volume is used for this lab implementation to keep behavior unchanged while showing microservice separation.
7. Jenkins acts as the CI/CD controller.
8. Pytest validates important user flows before deployment.
9. SonarQube checks code quality and coverage.
10. Ansible runs deployment automation after the build succeeds.

## Before the demo

### Software to install on your machine

1. Docker Desktop
2. Git
3. Python 3.12 or compatible Python 3

### First-time project setup

1. Open a terminal in the project root.
2. Initialize Git if needed:

```powershell
git init
git add .
git commit -m "Initial TripMate CI/CD integration"
```

3. Create and activate a virtual environment if you want to run tests outside Docker:

```powershell
python -m venv .venv
.venv\Scripts\activate
cd tripmate
pip install -r requirements.txt
```

4. Run tests once locally:
```powershell
pytest --cov=. --cov-report=term --cov-report=xml
```

5. Go back to the project root and start the DevOps stack:
```powershell
cd ..
docker compose up -d --build
```

## Jenkins setup steps

Open `http://localhost:8080`

### If Jenkins asks for an initial admin password

Run:

```powershell
docker exec tripmate-jenkins cat /var/jenkins_home/secrets/initialAdminPassword
```

### Create the pipeline job

1. Click `New Item`
2. Enter name: `tripmate-pipeline`
3. Choose `Pipeline`
4. In pipeline definition, choose `Pipeline script from SCM`
5. Choose `Git`
6. Enter your repository URL
7. Script Path: `Jenkinsfile`
8. Save

## SonarQube setup steps

Open `http://localhost:9000`

### Default login

1. Username: `admin`
2. Password: `admin`

SonarQube will ask you to change the password on first login.

### Create a project token

1. Go to `My Account`
2. Open `Security`
3. Generate a token for TripMate
4. Copy the token

## Connect SonarQube with Jenkins

In Jenkins:

1. Go to `Manage Jenkins`
2. Open `System`
3. Find `SonarQube servers`
4. Add a server with the name `sonarqube-server`
5. Server URL: `http://sonarqube:9000`
6. Add the token as a Jenkins secret text credential
7. Save

## How to run the full pipeline during demo

1. Show the running application at `http://localhost:8000`
2. Open Jenkins and click `Build Now` for `tripmate-pipeline`
3. Open the running build and show the stages:
4. Explain each stage:
   Checkout source code
   Install Python dependencies
   Run Pytest test suite
   Run SonarQube analysis
   Build Docker image
   Deploy using Ansible
5. After success, open SonarQube and show the analysis dashboard
6. Open terminal and show:

```powershell
docker compose ps
```

7. Show the application still running after deployment

## Exact explanation to give your professor

You can say:

`This project uses Flask as the application layer. Pytest is used as the mandatory testing tool in the CI pipeline. Jenkins is used to automate the CI/CD stages. SonarQube is integrated to check code quality and test coverage. Docker is used to containerize the application and DevOps services. Ansible is used in the final stage to automate deployment using Docker Compose.`

You can also add:

`To satisfy microservice expectations, the app is split into gateway, authentication, travel, and finance services while preserving the same end-user functionality.`

## Screenshots you should capture

1. TripMate login page
2. TripMate dashboard after login
3. Pytest results in terminal or Jenkins console
4. Jenkins stage view
5. SonarQube project dashboard
6. Docker containers from `docker compose ps`
7. Ansible deployment stage logs in Jenkins

## Free vs risky vs paid items

### Free for local academic demo

1. Docker Desktop personal/student use
2. Jenkins running locally in Docker
3. SonarQube Community Edition locally in Docker
4. Ansible locally
5. Git local repository

### Credentials needed only if you use remote integration

1. GitHub or GitLab repository URL for Jenkins SCM
2. SonarQube token for Jenkins integration
3. Docker Hub credentials only if you want to push images online
4. Cloud VM credentials only if you want Ansible to deploy to another machine

### Risk notes

1. SonarQube token is sensitive and should not be committed into source code.
2. GitHub personal access tokens are sensitive and should only be stored in Jenkins credentials.
3. Docker Hub credentials are sensitive and only needed if you push images to a registry.
4. Cloud credentials or SSH private keys are sensitive and should never be pasted into project files.

## Best local-only demo path

If you want the safest and cheapest demo:

1. Keep everything local on your laptop
2. Use local Git repository or a private GitHub repo
3. Run Jenkins, SonarQube, and the app using Docker Compose
4. Let Jenkins build and deploy locally with Ansible

This avoids paid cloud usage and reduces credential risk.
