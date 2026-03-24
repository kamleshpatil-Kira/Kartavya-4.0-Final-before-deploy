pipeline {
    agent any

    environment {
        DOCKER_COMPOSE_FILE = 'docker-compose.prod.yml'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Verify API Key') {
            steps {
                script {
                    // -------------------------------------------------------
                    // API KEY APPROACH 1 (PREFERRED for Seniors/Direct Server):
                    // Set GEMINI_API_KEY as a system-wide environment variable.
                    //   sudo vi /etc/environment
                    //   → Add line:  GEMINI_API_KEY=YOUR_KEY_HERE
                    //   source /etc/environment  (or reboot the server)
                    //
                    // Docker Compose reads GEMINI_API_KEY from the host shell
                    // automatically — no .env file needed on the server at all.
                    //
                    // APPROACH 2 (For Jenkins CI/CD only — optional fallback):
                    // Store key as a Jenkins "Secret File" credential with
                    // ID = 'kartavya-env-secrets'. If found, it is injected
                    // below and Docker Compose reads from the host via export.
                    // -------------------------------------------------------
                    def keyFromSystem = sh(script: 'echo $GEMINI_API_KEY', returnStdout: true).trim()
                    if (keyFromSystem) {
                        echo '✅ GEMINI_API_KEY found in system environment. Proceeding.'
                    } else {
                        echo '⚠️  GEMINI_API_KEY not found in system env. Trying Jenkins credentials...'
                        try {
                            withCredentials([file(credentialsId: 'kartavya-env-secrets', variable: 'SECRET_ENV')]) {
                                // Export into the current shell so Docker Compose picks it up
                                sh '''
                                    set -a
                                    source $SECRET_ENV
                                    set +a
                                    echo "✅ API key loaded from Jenkins credentials."
                                '''
                            }
                        } catch (e) {
                            error('❌ GEMINI_API_KEY not found in system env OR Jenkins credentials. Deployment aborted.')
                        }
                    }
                }
            }
        }

        stage('Build Docker Images') {
            steps {
                sh "DOCKER_BUILDKIT=1 docker compose -f ${DOCKER_COMPOSE_FILE} build backend"
                sh "DOCKER_BUILDKIT=1 docker compose -f ${DOCKER_COMPOSE_FILE} build frontend"
            }
        }

        stage('Stop Old Containers') {
            steps {
                sh "docker compose -f ${DOCKER_COMPOSE_FILE} down || true"
            }
        }

        stage('Start New Containers') {
            steps {
                sh "docker compose -f ${DOCKER_COMPOSE_FILE} up -d backend frontend"
            }
        }

        stage('Health Checks') {
            steps {
                script {
                    sleep time: 15, unit: 'SECONDS'

                    // Backend health check
                    sh 'curl --fail --silent --show-error http://127.0.0.1:8000/api/health || exit 1'
                    echo 'Backend health check passed!'

                    // Frontend health check
                    sh 'curl --fail --silent --show-error http://127.0.0.1:3000/ || exit 1'
                    echo 'Frontend health check passed!'
                }
            }
        }
    }

    post {
        success {
            echo '✅ Kartavya-3.0 deployed successfully!'
        }
        failure {
            echo '❌ Deployment failed. Fetching container logs...'
            sh "docker compose -f ${DOCKER_COMPOSE_FILE} logs --tail 80 || true"
        }
        always {
            // Clean up any .env file from workspace (security hygiene)
            sh 'rm -f .env'
        }
    }
}
