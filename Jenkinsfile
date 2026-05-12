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
                checkout scm
                script {
                    echo "Branch name: ${env.BRANCH_NAME}"
                    echo "GIT_BRANCH: ${env.GIT_BRANCH}"
                    def config = readFile('pipeline.config')
                    config.readLines().each { line ->
                        line = line.trim()
                        if (line && !line.startsWith('#')) {
                            def parts = line.split('=', 2)
                            if (parts.length == 2) {
                                env[parts[0].trim()] = parts[1].trim()
                            }
                        }
                    }
                    env.IMAGE_TAG = env.BUILD_NUMBER
                }
            }
        }
        stage('Build') {
            steps {
                script {
                    dockerImage = docker.build(
                        "${env.DOCKER_IMAGE}:${env.IMAGE_TAG}"
                    )
                }
            }
        }
         stage('Test') {
            steps {
                script {
                    dockerImage.inside {
                        sh 'python -m unittest discover -p "test*.py" -v'
                    }
                }
            }
        }
        stage('Deploy') {
            when {
                expression {
                    return env.GIT_BRANCH == "origin/${env.DEPLOY_BRANCH}" ||
                        env.GIT_BRANCH == env.DEPLOY_BRANCH
                }
            }
            steps {
                script {
                    docker.withRegistry(
                        "https://${env.DOCKER_REGISTRY}",
                        env.REGISTRY_CREDS
                    ) {
                        dockerImage.push("${env.IMAGE_TAG}")
                        dockerImage.push('latest')
                    }
                }
                withCredentials([sshUserPrivateKey(
                    credentialsId: env.DEPLOY_SSH_CREDS,
                    keyFileVariable: 'SSH_KEY',
                    usernameVariable: 'SSH_USER'
                )]) {
                    sh """
                        ssh -i \$SSH_KEY -o StrictHostKeyChecking=no \$SSH_USER@${env.DEPLOY_HOST} 'docker pull ${env.DOCKER_IMAGE}:${env.IMAGE_TAG} ; docker stop ${env.CONTAINER_NAME} || true ; docker rm ${env.CONTAINER_NAME} || true ; docker run -d --name ${env.CONTAINER_NAME} --restart unless-stopped ${env.DOCKER_IMAGE}:${env.IMAGE_TAG}'
                    """
                }
            }
            post {
                always {
                    script {
                        sh "docker rmi ${env.DOCKER_IMAGE}:${env.IMAGE_TAG} || true"
                    }
                    cleanWs()
                }
                success {
                    echo "Container deployed successfully on ${env.DEPLOY_HOST}"
                }
                failure {
                    echo "Pipeline failed at Push & Deploy. Check logs above."
                }
            }
        }
    }
}