// Jenkinsfile

pipeline {
    agent {
        docker {
            image 'python:3.7'
            // Run as root (default) so pip can install system packages
            // and allow Docker-in-Docker via socket.
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

        // ------------------ checkout ------------------
        stage('checkout') {
            steps {
                echo "==> Checkout the source code for the Python Jenkins pipeline project"
                checkout scm
            }
        }

        // ------------------ setup ------------------
        stage('setup') {
            steps {
                echo "==> Prepare Python environment and install dependencies"
                // Upgrading pip is optional; it should now work as root.
                sh 'python -m pip install --upgrade pip'
                sh 'python -m pip install -r requirements.txt'
            }
        }

        // ------------------ build ------------------
        stage('build') {
            steps {
                echo "==> Compile Python sources"
                sh 'python -m compileall .'

                echo "==> Build Docker image (no push, just local use)"
                script {
                    def fullImage = "${IMAGE_NAME}:${IMAGE_TAG}"
                    sh "docker build -t ${fullImage} ."
                }
            }
        }

        // ------------------ test ------------------
        stage('test') {
            steps {
                script {
                    def fullImage = "${IMAGE_NAME}:${IMAGE_TAG}"

                    echo "==> Start Docker container for tests"
                    sh """
                        docker run --name python-jenkins-pipeline \
                                   --detach --rm \
                                   --network ci \
                                   -p 5001:5000 \
                                   ${fullImage}
                    """

                    echo "==> Run unit tests"
                    sh "nosetests -v test"

                    echo "==> Run mutation tests (cosmic-ray)"
                    sh """
                        cosmic-ray init config.yml jenkins_session && \
                        cosmic-ray --verbose exec jenkins_session && \
                        cosmic-ray dump jenkins_session | cr-report
                    """

                    echo "==> Run integration tests"
                    sh "nosetests -v int_test"

                    echo "==> Run performance tests (locust)"
                    sh "locust -f ./perf_test/locustfile.py --no-web -c 1000 -r 100 --run-time 1m -H http://172.18.0.3:5001"

                    echo "==> Stop test container"
                    sh "docker stop python-jenkins-pipeline || true"
                }
            }
        }

        // ------------------ quality ------------------
        stage('quality') {
            steps {
                echo "==> Dependency vulnerability checks (safety)"
                sh "safety check"

                echo "==> Code inspection & quality gate (pylama)"
                sh "pylama"
            }
        }
    }
}
