# Jenkins + GitHub + SonarQube Exact Setup

## 1. Start Jenkins and SonarQube

```bash
docker compose up -d jenkins sonarqube
```

Open:

1. Jenkins: `http://localhost:8080`
2. SonarQube: `http://localhost:9000`

## 2. Create the SonarQube token

In SonarQube:

1. Log in.
2. Click your profile icon.
3. Open `My Account`.
4. Open `Security`.
5. In the token box, type `jenkins-tripmate-token`.
6. Click `Generate`.
7. Copy the token.

## 3. Store the SonarQube token in Jenkins

In Jenkins:

1. Go to `Manage Jenkins`.
2. Go to `Credentials`.
3. Open `(global)`.
4. Click `Add Credentials`.
5. Kind: `Secret text`
6. Secret: paste the SonarQube token
7. ID: `sonarqube-token`
8. Description: `TripMate SonarQube token`
9. Click `Create`

## 4. Configure SonarQube in Jenkins

1. Go to `Manage Jenkins`.
2. Go to `System`.
3. Find `SonarQube servers`.
4. Click `Add SonarQube`.
5. Name: `sonarqube-server`
6. Server URL: `http://sonarqube:9000`
7. Server authentication token: choose `sonarqube-token`
8. Save

## 5. Configure Sonar Scanner in Jenkins

1. Go to `Manage Jenkins`.
2. Go to `Tools`.
3. Find `SonarQube Scanner`.
4. Click `Add SonarQube Scanner`.
5. Name: `sonar-scanner`
6. Check `Install automatically`
7. Save

## 6. Create GitHub token

In GitHub:

1. Go to `Settings`.
2. Go to `Developer settings`.
3. Go to `Personal access tokens`.
4. Create a token.
5. Give it:
6. `repo`
7. `admin:repo_hook`
8. Copy the token.

## 7. Store the GitHub token in Jenkins

1. Go to `Manage Jenkins`.
2. Go to `Credentials`.
3. Open `(global)`.
4. Click `Add Credentials`.
5. Kind: `Username with password`
6. Username: your GitHub username
7. Password: paste the GitHub token
8. ID: `github-tripmate-token`
9. Description: `TripMate GitHub token`
10. Save

## 8. Create the pipeline job

1. Click `New Item`.
2. Enter `tripmate-pipeline`.
3. Choose `Pipeline`.
4. Click `OK`.
5. Tick `GitHub hook trigger for GITScm polling`.
6. Under `Pipeline`, choose `Pipeline script from SCM`.
7. SCM: `Git`
8. Repository URL: `https://github.com/Acsel28/Tripmate.git`
9. Credentials: `github-tripmate-token`
10. Branch Specifier: `*/main`
11. Script Path: `Jenkinsfile`
12. Save

## 9. Add the GitHub webhook

In GitHub repository settings:

1. Go to `Settings`.
2. Open `Webhooks`.
3. Click `Add webhook`.
4. Payload URL:

```text
http://YOUR-JENKINS-PUBLIC-URL/github-webhook/
```

5. Content type: `application/json`
6. Choose `Just the push event`
7. Save

## 10. If Jenkins is only on localhost

Use a public tunnel such as:

1. Ngrok
2. Cloudflare Tunnel

Then use the public URL in the GitHub webhook.
