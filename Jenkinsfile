pipeline {
    agent any

    environment {
        IMAGE_NAME = 'tripmate-app'
        IMAGE_TAG = "${env.BUILD_NUMBER}"
        SONARQUBE_SERVER = 'sonarqube-server'
        SONAR_SCANNER_TOOL = 'sonar-scanner'
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
                            sh '''
                                python3 -m venv .venv
                                . .venv/bin/activate
                                python -m pip install --upgrade pip
                                pip install -r requirements.txt
                            '''
                        } else {
                            bat '''
                                python -m venv .venv
                                call .venv\\Scripts\\activate
                                python -m pip install --upgrade pip
                                pip install -r requirements.txt
                            '''
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
                            sh '''
                                . .venv/bin/activate
                                pytest --cov=. --cov-report=xml --cov-report=term
                            '''
                        } else {
                            bat '''
                                call .venv\\Scripts\\activate
                                pytest --cov=. --cov-report=xml --cov-report=term
                            '''
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
                            def scannerHome = tool "${SONAR_SCANNER_TOOL}"
                            if (isUnix()) {
                                withEnv(["PATH+SONAR=${scannerHome}/bin"]) {
                                    sh '''
                                        . .venv/bin/activate
                                        sonar-scanner
                                    '''
                                }
                            } else {
                                withEnv(["PATH+SONAR=${scannerHome}\\bin"]) {
                                    bat '''
                                        call .venv\\Scripts\\activate
                                        sonar-scanner
                                    '''
                                }
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
