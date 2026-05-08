# TripMate Setup Guide

This guide is written for Ubuntu users working in VS Code.

## 1. Install prerequisites

```bash
sudo apt update
sudo apt install -y git docker.io docker-compose-plugin python3 python3-venv python3-pip ansible curl
sudo usermod -aG docker $USER
newgrp docker
```

## 2. Clone and open the project

```bash
git clone https://github.com/Acsel28/Tripmate.git
cd Tripmate
code .
```

## 3. Run tests locally

```bash
cd tripmate
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest --cov=. --cov-report=xml --cov-report=term
cd ..
```

## 4. Start the whole stack

```bash
docker compose up -d --build
docker compose ps
```

Open:

1. Frontend: `http://localhost:3000`
2. API gateway: `http://localhost:8000`
3. Jenkins: `http://localhost:8080`
4. SonarQube: `http://localhost:9000`
5. Prometheus: `http://localhost:9090`
6. Grafana: `http://localhost:3001`

## 5. Default Grafana login

1. Username: `admin`
2. Password: `admin123`

## 6. Rebuild after code changes

```bash
docker compose down
docker compose up -d --build
```

## 7. Deploy using Ansible

```bash
ansible-playbook ansible/deploy.yml -i ansible/inventory.ini
```

This rebuilds and verifies:

1. API gateway health
2. Planning service health
3. Prometheus health
4. Grafana health

## 8. Check monitoring

```bash
curl http://localhost:9090/api/v1/targets
curl http://localhost:3001/api/health
```

## 9. Common issues

1. If the website looks static, open `http://localhost:3000` and not the raw HTML file.
2. If buttons do nothing, check `http://localhost:8000/health`.
3. If Jenkins cannot use Docker, confirm `/var/run/docker.sock` is mounted.
4. If SonarQube starts slowly, wait a minute and refresh.
