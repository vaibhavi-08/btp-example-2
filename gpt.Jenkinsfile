pipeline {
    agent any

    environment {
        REGISTRY_CREDS   = 'dockerhub-credentials'
        DEPLOY_SSH_CREDS = 'deploy-server-ssh'
        DOCKER_REGISTRY  = 'registry-1.docker.io'
    }

    stages {

        stage('Checkout') {
            steps {
                git 'https://github.com/vaibhavi-08/btp-example-2'
            }
        }

        stage('Setup') {
            steps {
                script {

                    // Read values from pipeline.config
                    def config = readProperties file: 'pipeline.config'

                    env.DOCKER_IMAGE   = config.DOCKER_IMAGE
                    env.DEPLOY_HOST    = config.DEPLOY_HOST
                    env.DEPLOY_USER    = config.DEPLOY_USER
                    env.DEPLOY_BRANCH  = config.DEPLOY_BRANCH
                    env.CONTAINER_NAME = config.CONTAINER_NAME
                }

                sh '''
                    python3 -m venv venv
                    . venv/bin/activate

                    pip install --upgrade pip

                    # Install dependencies from requirements.txt
                    if [ -f "requirements.txt" ]; then
                        pip install -r requirements.txt
                    fi
                '''
            }
        }

        stage('Build') {
            when {
                branch env.DEPLOY_BRANCH
            }

            steps {
                script {
                    dockerImage = docker.build("${DOCKER_IMAGE}:${BUILD_NUMBER}")
                }
            }
        }

        stage('Quality') {
            steps {
                sh '''
                    echo "flake8 not configured for this repository"
                '''
            }
        }

        stage('Test') {
            steps {
                sh '''
                    echo "No tests configured for this repository"
                '''
            }
        }

        stage('Deploy') {
            when {
                branch env.DEPLOY_BRANCH
            }

            steps {

                script {

                    // Push Docker image
                    docker.withRegistry("https://${DOCKER_REGISTRY}", REGISTRY_CREDS) {
                        dockerImage.push('latest')
                        dockerImage.push("${BUILD_NUMBER}")
                    }
                }

                sshagent(credentials: [DEPLOY_SSH_CREDS]) {

                    sh """
                    ssh -o StrictHostKeyChecking=no ${DEPLOY_USER}@${DEPLOY_HOST} '

                        docker pull ${DOCKER_IMAGE}:latest

                        docker stop ${CONTAINER_NAME} || true
                        docker rm ${CONTAINER_NAME} || true

                        docker run -d \
                            --name ${CONTAINER_NAME} \
                            ${DOCKER_IMAGE}:latest
                    '
                    """
                }
            }
        }
    }

    post {

        success {
            echo 'Pipeline executed successfully!'
        }

        failure {
            echo 'Pipeline failed!'
        }
    }
}