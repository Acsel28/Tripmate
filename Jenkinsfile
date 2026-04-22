pipeline {
    agent any

    environment {
        IMAGE_NAME = 'tripmate-app'
        IMAGE_TAG = "${env.BUILD_NUMBER}"
        SONARQUBE_SERVER = 'sonarqube-server'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Install Dependencies') {
            steps {
                dir('tripmate') {
                    script {
                        if (isUnix()) {
                            sh 'python3 -m pip install --upgrade pip'
                            sh 'pip3 install -r requirements.txt'
                        } else {
                            bat 'python -m pip install --upgrade pip'
                            bat 'pip install -r requirements.txt'
                        }
                    }
                }
            }
        }

        stage('Run Tests') {
            steps {
                dir('tripmate') {
                    script {
                        if (isUnix()) {
                            sh 'pytest --cov=. --cov-report=xml --cov-report=term'
                        } else {
                            bat 'pytest --cov=. --cov-report=xml --cov-report=term'
                        }
                    }
                }
            }
        }

        stage('SonarQube Analysis') {
            steps {
                dir('tripmate') {
                    withSonarQubeEnv("${SONARQUBE_SERVER}") {
                        script {
                            if (isUnix()) {
                                sh 'sonar-scanner'
                            } else {
                                bat 'sonar-scanner'
                            }
                        }
                    }
                }
            }
        }

        stage('Build Docker Image') {
            steps {
                script {
                    if (isUnix()) {
                        sh 'docker build -t ${IMAGE_NAME}:${IMAGE_TAG} .'
                    } else {
                        bat "docker build -t %IMAGE_NAME%:%IMAGE_TAG% ."
                    }
                }
            }
        }

        stage('Deploy With Ansible') {
            steps {
                script {
                    if (isUnix()) {
                        sh 'ansible-playbook ansible/deploy.yml -i ansible/inventory.ini'
                    } else {
                        bat 'ansible-playbook ansible/deploy.yml -i ansible/inventory.ini'
                    }
                }
            }
        }
    }
}
