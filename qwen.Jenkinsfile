pipeline {
    agent any

    environment {
        CONFIG_FILE = 'pipeline.config'
        REGISTRY_CREDS = 'dockerhub-credentials'
        DEPLOY_SSH_CREDS = 'deploy-server-ssh'
        DOCKER_REGISTRY = 'registry-1.docker.io'
    }

    stages {
        stage('checkout') {
            steps {
                checkout scm
                script {
                    // Parse pipeline.config (KEY=VALUE format)
                    def configLines = readFile(CONFIG_FILE).readLines()
                    def config = [:]
                    configLines.each { line ->
                        if (line && !line.trim().startsWith('#') && line.contains('=')) {
                            def parts = line.split('=', 2)
                            config[parts[0].trim()] = parts[1].trim()
                        }
                    }
                    env.DOCKER_IMAGE = config.DOCKER_IMAGE
                    env.DEPLOY_HOST = config.DEPLOY_HOST
                    env.DEPLOY_USER = config.DEPLOY_USER
                    env.DEPLOY_BRANCH = config.DEPLOY_BRANCH
                    env.CONTAINER_NAME = config.CONTAINER_NAME
                    echo "✅ Loaded config: Image=${env.DOCKER_IMAGE}, Host=${env.DEPLOY_HOST}, Branch=${env.DEPLOY_BRANCH}"
                }
            }
        }

        stage('setup') {
            steps {
                script {
                    // Create virtual environment and install dependencies (if requirements.txt exists)
                    sh '''
                        python3 -m venv venv
                        . venv/bin/activate
                        pip install --upgrade pip
                        if [ -f requirements.txt ]; then
                            echo "📦 Installing dependencies from requirements.txt..."
                            pip install -r requirements.txt
                        else
                            echo "⚠️ No requirements.txt found, skipping dependency install"
                        fi
                    '''
                }
            }
        }

        stage('build') {
            steps {
                script {
                    // Build Docker image with build number and latest tag
                    echo "🔨 Building Docker image: ${DOCKER_REGISTRY}/${DOCKER_IMAGE}:${BUILD_NUMBER}"
                    sh "docker build -t ${DOCKER_REGISTRY}/${DOCKER_IMAGE}:${BUILD_NUMBER} -t ${DOCKER_REGISTRY}/${DOCKER_IMAGE}:latest ."
                }
            }
        }

        stage('quality') {
            steps {
                script {
                    // flake8 disabled per config - perform basic Python syntax validation only
                    echo "🔍 Quality check: flake8 disabled, running basic syntax validation..."
                    sh '''
                        . venv/bin/activate
                        # Basic syntax check on .py files (non-fatal, for logging)
                        find . -name "*.py" -not -path "./venv/*" -exec python3 -m py_compile {} \\; 2>&1 | tee syntax-check.log || true
                        echo "✅ Syntax validation complete"
                    '''
                }
            }
        }

        stage('test') {
            steps {
                script {
                    // tests disabled per config - stage kept for pipeline structure
                    echo "🧪 Test stage: No tests configured, skipping execution"
                    // Optional: Add a placeholder to keep stage visible in Jenkins UI
                    sh 'echo "⏭️ Tests skipped - no test suite configured"'
                }
            }
        }

        stage('deploy') {
            when {
                branch "${env.DEPLOY_BRANCH}"
            }
            steps {
                script {
                    echo "🚀 Deploying to ${DEPLOY_HOST} as ${DEPLOY_USER}..."
                    
                    // Push Docker image to registry
                    withCredentials([usernamePassword(
                        credentialsId: REGISTRY_CREDS,
                        usernameVariable: 'DOCKER_USER',
                        passwordVariable: 'DOCKER_PASS'
                    )]) {
                        sh "echo ${DOCKER_PASS} | docker login ${DOCKER_REGISTRY} -u ${DOCKER_USER} --password-stdin"
                        sh "docker push ${DOCKER_REGISTRY}/${DOCKER_IMAGE}:${BUILD_NUMBER}"
                        sh "docker push ${DOCKER_REGISTRY}/${DOCKER_IMAGE}:latest"
                        sh "docker logout ${DOCKER_REGISTRY}"
                    }

                    // Deploy to your laptop via SSH
                    sshagent(credentials: [DEPLOY_SSH_CREDS]) {
                        sh """
                            ssh -o StrictHostKeyChecking=no -o ConnectTimeout=30 ${DEPLOY_USER}@${DEPLOY_HOST} \\
                                "echo '${DOCKER_PASS}' | docker login ${DOCKER_REGISTRY} -u '${DOCKER_USER}' --password-stdin && \\
                                docker pull ${DOCKER_REGISTRY}/${DOCKER_IMAGE}:${BUILD_NUMBER} && \\
                                docker stop ${CONTAINER_NAME} 2>/dev/null || true && \\
                                docker rm ${CONTAINER_NAME} 2>/dev/null || true && \\
                                docker run -d --name ${CONTAINER_NAME} ${DOCKER_REGISTRY}/${DOCKER_IMAGE}:${BUILD_NUMBER} && \\
                                docker image prune -f && \\
                                docker logout ${DOCKER_REGISTRY}"
                        """
                    }
                    echo "✅ Deployment complete: ${CONTAINER_NAME} running on ${DEPLOY_HOST}"
                }
            }
        }
    }

    post {
        always {
            // Cleanup local Docker artifacts to save disk space
            sh 'docker rmi ${DOCKER_REGISTRY}/${DOCKER_IMAGE}:${BUILD_NUMBER} 2>/dev/null || true'
            cleanWs()
        }
        failure {
            echo '❌ Pipeline FAILED - Check console output for details'
        }
        success {
            echo "🎉 Pipeline SUCCESS - ${DOCKER_IMAGE}:${BUILD_NUMBER} deployed to ${DEPLOY_HOST}"
        }
    }
}