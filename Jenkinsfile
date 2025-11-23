// Jenkinsfile for https://github.com/vaibhavi-08/btp-example-2

pipeline {
    agent {
        docker {
            image 'python:3.7'
            // Docker socket so we can build/run Docker from inside the container
            args '-v /var/run/docker.sock:/var/run/docker.sock'
        }
    }

    options {
        skipDefaultCheckout()
        timestamps()
    }

    environment {
        IMAGE_NAME = 'restalion/python-jenkins-pipeline'
        IMAGE_TAG  = "${env.BUILD_NUMBER}"
    }

    stages {

        // ==================== checkout ====================
        stage('checkout') {
            steps {
                echo "==> Checkout the source code for the Python Jenkins pipeline project"
                checkout scm
            }
        }

        // ==================== setup ====================
        stage('setup') {
            steps {
                echo "==> Install dependencies in user site-packages (no root, no venv)"
                sh '''
                    set -e

                    # Make sure HOME is a writable directory (the workspace)
                    export HOME="$PWD"

                    # Upgrade pip for this user only
                    python -m pip install --user --upgrade pip

                    # Install project dependencies into $HOME/.local
                    python -m pip install --user -r requirements.txt
                '''
            }
        }

        // ==================== build ====================
        stage('build') {
            steps {
                echo "==> Compile Python sources and build Docker image"
                sh '''
                    set -e
                    export HOME="$PWD"
                    export PATH="$HOME/.local/bin:$PATH"

                    # Compile sources
                    python -m compileall .

                    # Build Docker image (no push)
                    docker build -t $IMAGE_NAME:$BUILD_NUMBER .
                '''
            }
        }

        // ==================== test ====================
        stage('test') {
            steps {
                echo "==> Run unit, mutation, integration and performance tests"
                sh '''
                    set -e
                    export HOME="$PWD"
                    export PATH="$HOME/.local/bin:$PATH"

                    # Start Docker container for tests
                    docker run --name python-jenkins-pipeline \
                               --detach --rm \
                               --network ci \
                               -p 5001:5000 \
                               $IMAGE_NAME:$BUILD_NUMBER

                    # Unit tests
                    nosetests -v test

                    # Mutation tests
                    cosmic-ray init config.yml jenkins_session
                    cosmic-ray --verbose exec jenkins_session
                    cosmic-ray dump jenkins_session | cr-report

                    # Integration tests
                    nosetests -v int_test

                    # Performance tests
                    locust -f ./perf_test/locustfile.py --no-web \
                           -c 1000 -r 100 --run-time 1m \
                           -H http://172.18.0.3:5001

                    # Stop container (ignore errors)
                    docker stop python-jenkins-pipeline || true
                '''
            }
        }

        // ==================== quality ====================
        stage('quality') {
            steps {
                echo "==> Dependency vulnerability checks and code inspection"
                sh '''
                    set -e
                    export HOME="$PWD"
                    export PATH="$HOME/.local/bin:$PATH"

                    safety check
                    pylama
                '''
            }
        }
    }
}
