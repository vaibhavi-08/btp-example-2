cat << 'EOF' > Jenkinsfile
pipeline {
    agent any

    options {
        skipDefaultCheckout()
    }

    environment {
        REGISTRY_CREDS   = 'dockerhub-credentials'
        DEPLOY_SSH_CREDS = 'deploy-server-ssh'
        DOCKER_REGISTRY  = 'registry-1.docker.io'
    }

    stages {
        stage('Checkout') {
            steps {
                // Checkout from the explicit repository URL provided
                git url: 'https://github.com/vaibhavi-08/btp-example-2', branch: 'main'
            }
        }

        stage('Setup') {
            steps {
                script {
                    def props = readProperties file: 'pipeline.config'
                    env.DOCKER_IMAGE   = props.DOCKER_IMAGE
                    env.DEPLOY_HOST    = props.DEPLOY_HOST
                    env.DEPLOY_USER    = props.DEPLOY_USER
                    env.DEPLOY_BRANCH  = props.DEPLOY_BRANCH
                    env.CONTAINER_NAME = props.CONTAINER_NAME
                }
                
                sh '''
                    python3 -m venv venv
                    . venv/bin/activate
                    pip install --upgrade pip
                    pip install -r requirements.txt
                '''
            }
        }

        stage('Build') {
            steps {
                script {
                    dockerImage = docker.build("${env.DOCKER_IMAGE}:${env.BUILD_NUMBER}")
                }
            }
        }

        // Quality and Test stages omitted as per configuration

        stage('Deploy') {
            when {
                branch "${env.DEPLOY_BRANCH}"
            }
            steps {
                script {
                    docker.withRegistry("https://${env.DOCKER_REGISTRY}", env.REGISTRY_CREDS) {
                        dockerImage.push("${env.BUILD_NUMBER}")
                        dockerImage.push("latest")
                    }

                    sshagent(credentials: [env.DEPLOY_SSH_CREDS]) {
                        sh """
                            ssh -o StrictHostKeyChecking=no ${env.DEPLOY_USER}@${env.DEPLOY_HOST} '
                                # Silent check and installation for environments missing Docker
                                if ! command -v docker &> /dev/null; then
                                    echo "Docker not found. Installing..."
                                    sudo apt-get update && sudo apt-get install -y docker.io
                                    sudo systemctl start docker
                                    sudo systemctl enable docker
                                    sudo usermod -aG docker \$USER
                                fi

                                docker pull ${env.DOCKER_IMAGE}:${env.BUILD_NUMBER}
                                
                                docker stop ${env.CONTAINER_NAME} || true
                                docker rm ${env.CONTAINER_NAME} || true
                                
                                docker run -d --name ${env.CONTAINER_NAME} ${env.DOCKER_IMAGE}:${env.BUILD_NUMBER}
                            '
                        """
                    }
                }
            }
        }
    }
    
    post {
        always {
            cleanWs()
        }
    }
}
EOF