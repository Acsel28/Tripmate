pipeline {
    agent any

    environment {
        SONARQUBE_SERVER = 'sonarqube-server'
        SONAR_SCANNER_TOOL = 'sonar-scanner'
        COMPOSE_PROJECT_NAME = 'tripmate'
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

        stage('Run Pytest') {
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
                                        sonar-scanner -Dproject.settings=../sonar-project.properties -Dsonar.projectBaseDir=.
                                    '''
                                }
                            } else {
                                withEnv(["PATH+SONAR=${scannerHome}\\bin"]) {
                                    bat '''
                                        call .venv\\Scripts\\activate
                                        sonar-scanner -Dproject.settings=..\\sonar-project.properties -Dsonar.projectBaseDir=.
                                    '''
                                }
                            }
                        }
                    }
                }
            }
        }

        stage('Build Docker Images') {
            steps {
                script {
                    def buildCommand = 'docker compose -p tripmate build api-gateway frontend auth-service trip-service planning-service booking-service expense-service budget-service notification-service recommendation-service itinerary-service reporting-service'
                    if (isUnix()) {
                        sh buildCommand
                    } else {
                        bat buildCommand
                    }
                }
            }
        }

        stage('Deploy Docker Stack With Ansible') {
            steps {
                script {
                    def deployCommand = 'ansible-playbook ansible/deploy.yml -i ansible/inventory.ini'
                    if (isUnix()) {
                        sh deployCommand
                    } else {
                        bat deployCommand
                    }
                }
            }
        }

        stage('Verify Docker Stack Health') {
            steps {
                script {
                    def healthCommand = '''
                        docker compose -p tripmate ps
                        curl -f http://localhost:8000/health
                        curl -f http://localhost:5006/health
                        curl -f http://localhost:9090/-/healthy
                        curl -f http://localhost:3001/api/health
                    '''
                    if (isUnix()) {
                        sh healthCommand
                    } else {
                        bat '''
                            docker compose -p tripmate ps
                            powershell -Command "Invoke-WebRequest http://localhost:8000/health -UseBasicParsing"
                            powershell -Command "Invoke-WebRequest http://localhost:5006/health -UseBasicParsing"
                            powershell -Command "Invoke-WebRequest http://localhost:9090/-/healthy -UseBasicParsing"
                            powershell -Command "Invoke-WebRequest http://localhost:3001/api/health -UseBasicParsing"
                        '''
                    }
                }
            }
        }
    }

    post {
        failure {
            script {
                def rollbackCommand = 'docker compose -p tripmate down'
                if (isUnix()) {
                    sh rollbackCommand
                } else {
                    bat rollbackCommand
                }
            }
        }
    }
}
