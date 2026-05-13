
pipeline {
    agent any

    environment {
        REGISTRY_CREDS   = 'dockerhub-credentials'
        DEPLOY_SSH_CREDS = 'deploy-server-ssh'
        DOCKER_REGISTRY  = 'registry-1.docker.io'
    }

    stages {

        // ─────────────────────────────────────────────
        // STAGE 1 — CHECKOUT
        // ─────────────────────────────────────────────
        stage('Checkout') {
            steps {
                checkout scm
                echo "Checked out branch: ${env.BRANCH_NAME}"
            }
        }

        // ─────────────────────────────────────────────
        // STAGE 2 — SETUP
        // Read pipeline.config and create virtualenv
        // ─────────────────────────────────────────────
        stage('Setup') {
            steps {
                script {
                    // Parse pipeline.config into environment variables
                    def config = readFile('pipeline.config').trim()
                    config.readLines().each { line ->
                        line = line.trim()
                        if (line && !line.startsWith('#')) {
                            def (key, value) = line.tokenize('=')
                            env[key.trim()] = value.trim()
                        }
                    }

                    echo "Docker Image   : ${env.DOCKER_IMAGE}"
                    echo "Deploy Host    : ${env.DEPLOY_HOST}"
                    echo "Deploy User    : ${env.DEPLOY_USER}"
                    echo "Deploy Branch  : ${env.DEPLOY_BRANCH}"
                    echo "Container Name : ${env.CONTAINER_NAME}"
                }

                // Create a virtualenv and install dependencies
                sh '''
                    python3 -m venv .venv
                    . .venv/bin/activate
                    pip install --upgrade pip
                    pip install -r requirements.txt
                    pip install flake8
                '''
            }
        }

        // ─────────────────────────────────────────────
        // STAGE 3 — BUILD
        // Build and tag the Docker image
        // ─────────────────────────────────────────────
        stage('Build') {
            steps {
                script {
                    def imageTag = "${env.DOCKER_IMAGE}:${env.BUILD_NUMBER}"
                    def imageLatest = "${env.DOCKER_IMAGE}:latest"

                    echo "Building Docker image: ${imageTag}"

                    docker.build(imageTag)

                    // Tag as latest as well
                    sh "docker tag ${imageTag} ${imageLatest}"

                    // Store tag for later stages
                    env.IMAGE_TAG = imageTag
                }
            }
        }

        // ─────────────────────────────────────────────
        // STAGE 4 — QUALITY
        // Run flake8 linting on the source code
        // ─────────────────────────────────────────────
        stage('Quality') {
            steps {
                echo "Quality checks are not configured for this project. Skipping."
            }
        }

        // ─────────────────────────────────────────────
        // STAGE 5 — TEST
        // Run tests from the tests/ folder
        // ─────────────────────────────────────────────
        stage('Test') {
            steps {
                sh '''
                    . .venv/bin/activate
                    echo "Running tests..."
                    python -m unittest discover -s tests -p "*.py" -v
                '''
            }
            post {
                always {
                    // Archive test results if you switch to pytest-junit later
                    echo "Test stage complete."
                }
            }
        }

        // ─────────────────────────────────────────────
        // STAGE 6 — DEPLOY
        // Push image to Docker Hub, then SSH into laptop
        // to pull and restart the container
        // Only runs on the configured deploy branch
        // ─────────────────────────────────────────────
        stage('Deploy') {
            when {
                expression {
                    return env.BRANCH_NAME == env.DEPLOY_BRANCH
                }
            }
            steps {
                script {
                    def imageTag    = env.IMAGE_TAG
                    def imageLatest = "${env.DOCKER_IMAGE}:latest"

                    // ── Push image to Docker Hub ──────────────────
                    docker.withRegistry("https://${env.DOCKER_REGISTRY}", env.REGISTRY_CREDS) {
                        echo "Pushing ${imageTag} to registry..."
                        docker.image(imageTag).push()
                        docker.image(imageLatest).push()
                    }

                    // ── SSH into deploy server and update container ─
                    withCredentials([
                        sshUserPrivateKey(
                            credentialsId: env.DEPLOY_SSH_CREDS,
                            keyFileVariable: 'SSH_KEY'
                        )
                    ]) {
                        sh """
                            ssh -o StrictHostKeyChecking=no \
                                -i \$SSH_KEY \
                                ${env.DEPLOY_USER}@${env.DEPLOY_HOST} \
                                '
                                    echo "Pulling latest image: ${imageLatest}"
                                    docker pull ${imageLatest}

                                    echo "Stopping existing container (if running)..."
                                    docker stop ${env.CONTAINER_NAME} 2>/dev/null || true
                                    docker rm   ${env.CONTAINER_NAME} 2>/dev/null || true

                                    echo "Starting new container..."
                                    docker run -d \
                                        --name ${env.CONTAINER_NAME} \
                                        --restart unless-stopped \
                                        ${imageLatest}

                                    echo "Deployment complete."
                                '
                        """
                    }
                }
            }
        }

    } // end stages

    // ─────────────────────────────────────────────────
    // POST ACTIONS
    // ─────────────────────────────────────────────────
    post {
        success {
            echo "Pipeline succeeded for branch: ${env.BRANCH_NAME}"
        }
        failure {
            echo "Pipeline FAILED. Check the logs above for details."
        }
        always {
            // Clean up the local Docker image to save disk space
            script {
                try {
                    sh "docker rmi ${env.IMAGE_TAG} ${env.DOCKER_IMAGE}:latest || true"
                } catch (err) {
                    echo "Image cleanup skipped: ${err.message}"
                }
            }
            cleanWs()
        }
    }

}