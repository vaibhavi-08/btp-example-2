pipeline {
    agent any

    environment {
        REGISTRY_CREDS = 'dockerhub-credentials'
        DEPLOY_SSH_CREDS = 'deploy-server-ssh'
        DOCKER_REGISTRY = 'registry-1.docker.io'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
                echo "✅ Checkout completed"
            }
        }

        stage('Setup') {
            steps {
                script {
                    // Load configuration from pipeline.config
                    def config = readProperties file: 'pipeline.config'
                    env.DOCKER_IMAGE    = config.DOCKER_IMAGE
                    env.DEPLOY_HOST     = config.DEPLOY_HOST
                    env.DEPLOY_USER     = config.DEPLOY_USER
                    env.DEPLOY_BRANCH   = config.DEPLOY_BRANCH
                    env.CONTAINER_NAME  = config.CONTAINER_NAME
                    
                    echo "✅ Configuration loaded successfully"
                    echo "📦 Image      : ${env.DOCKER_IMAGE}"
                    echo "🖥️  Host       : ${env.DEPLOY_HOST}"
                    echo "📦 Container   : ${env.CONTAINER_NAME}"
                }

                // Install Python dependencies
                sh '''
                    python3 -m venv venv || true
                    . venv/bin/activate
                    pip install --upgrade pip
                    pip install -r requirements.txt
                '''
                echo "✅ Setup completed (Virtual Env + dependencies)"
            }
        }

        stage('Build') {
            steps {
                script {
                    // Build using the project's Dockerfile
                    docker.build("${DOCKER_IMAGE}:${env.BUILD_NUMBER}")
                    docker.build("${DOCKER_IMAGE}:latest")
                }
                echo "✅ Docker image built successfully using Dockerfile"
            }
        }

        stage('Push to Registry') {
            steps {
                script {
                    docker.withRegistry("https://${DOCKER_REGISTRY}", REGISTRY_CREDS) {
                        docker.image("${DOCKER_IMAGE}:${env.BUILD_NUMBER}").push()
                        docker.image("${DOCKER_IMAGE}:latest").push()
                    }
                }
                echo "✅ Image pushed to Docker Registry"
            }
        }

        stage('Deploy') {
            when {
                branch "${env.DEPLOY_BRANCH}"
            }
            steps {
                script {
                    sshagent(credentials: [DEPLOY_SSH_CREDS]) {
                        sh '''
                            ssh -o StrictHostKeyChecking=no ${DEPLOY_USER}@${DEPLOY_HOST} '
                                echo "Pulling latest image..." &&
                                docker pull ${DOCKER_IMAGE}:latest &&
                                
                                echo "Stopping old container..." &&
                                docker stop ${CONTAINER_NAME} || true &&
                                docker rm ${CONTAINER_NAME} || true &&
                                
                                echo "Starting new container..." &&
                                docker run -d --name ${CONTAINER_NAME} \
                                    --restart unless-stopped \
                                    ${DOCKER_IMAGE}:latest
                            '
                        '''
                    }
                }
                echo "✅ Deployment completed successfully on ${DEPLOY_HOST}"
            }
        }
    }

    post {
        success {
            echo "🎉 Pipeline executed successfully!"
        }
        failure {
            echo "❌ Pipeline failed at some stage"
        }
    }
}