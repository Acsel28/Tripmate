# TripMate Project Report Template

## 1. Project Title

TripMate: Travel Planning Web Application with CI/CD Pipeline

## 2. Technologies Used

1. Flask
2. Docker
3. Jenkins
4. SonarQube
5. Ansible
6. Pytest

## 3. Project Modules

1. User Authentication
2. Itinerary Management
3. Booking Management
4. Budget Tracking
5. Travel Reporting

## 4. Testing Approach

Automated testing is implemented using `pytest`.
The current test suite validates:

1. Redirect behavior for unauthenticated users
2. User registration flow
3. User login flow
4. Budget creation flow
5. Expense creation validation

## 5. CI/CD Pipeline Explanation

1. Developer pushes code to repository.
2. Jenkins triggers the pipeline using `Jenkinsfile`.
3. Dependencies are installed.
4. Automated tests run using `pytest`.
5. Code quality is scanned in SonarQube.
6. Docker image is built for the Flask application.
7. Ansible runs deployment steps using Docker Compose.
8. Updated services are available after successful deployment.

## 6. Screenshots to Attach

1. Application login/dashboard page
2. Pytest execution result
3. Jenkins pipeline success view
4. SonarQube analysis dashboard
5. Docker containers list
6. Ansible deployment output

## 7. Conclusion

The TripMate application was enhanced with a CI/CD-enabled workflow using testing, code quality analysis, containerization, and automated deployment. This makes the project easier to validate, package, deploy, and demonstrate in an academic setting.
