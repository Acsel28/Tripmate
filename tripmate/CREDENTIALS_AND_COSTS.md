# Credentials, Risk, and Cost Notes

## You do not need these for a basic local demo

1. Docker Hub account
2. Cloud server account
3. Paid SonarQube plan
4. Paid Jenkins plan

## You may need these for an expanded demo

1. GitHub repository URL
2. GitHub username and token if the repo is private
3. SonarQube token for Jenkins
4. SSH key if deploying with Ansible to another machine
5. Docker Hub username and password if pushing images to a registry

## Recommended safe choices

1. Use a local Git repository or a private GitHub repo
2. Store secrets only in Jenkins Credentials
3. Use local Docker Compose deployment
4. Do not hardcode tokens in `Jenkinsfile`, `.env`, or Python files

## Paid services only if you choose them

1. GitHub itself can be free for private student repos
2. Docker Hub free tier is usually enough for student work
3. SonarQube Community Edition is free locally
4. Cloud VMs such as AWS, Azure, or DigitalOcean may cost money
5. Domain names and public hosting can cost money
