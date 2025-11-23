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
        // avoid double checkout
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
                echo "==> Create virtualenv and install dependencies (no root needed)"
                sh '''
                    set -e

                    # Create venv in the workspace
                    python -m venv .venv

                    # Activate venv
                    . .venv/bin/activate

                    # Upgrade pip inside venv (this writes only into .venv)
                    pip install --upgrade pip

                    # Install project dependencies
                    pip install -r requirements.txt
                '''
            }
        }

        // ==================== build ====================
        stage('build') {
            steps {
                echo "==> Compile Python sources and build Docker image"

                // Compile using venv Python
                sh '''
                    set -e
                    . .venv/bin/activate
                    python -m compileall .
                '''

                // Build Docker image (no push)
                sh '''
                    set -e
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
                    . .venv/bin/activate

                    # Run app container for tests
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

                    # Always try to stop container at the end
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
                    . .venv/bin/activate

                    safety check
                    pylama
                '''
            }
        }
    }
}
