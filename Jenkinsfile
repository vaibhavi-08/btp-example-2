// Jenkinsfile

pipeline {
    // Run everything inside a Python docker image, with access to host docker
    // and a shared pip cache for faster repeated builds.
    agent {
        docker {
            image 'python:3.7'
            args '-v /var/run/docker.sock:/var/run/docker.sock -v $HOME/.cache/pip:/root/.cache/pip'
        }
    }

    options {
        // Avoid doing an implicit checkout before the first stage.
        skipDefaultCheckout()
        // Timestamped logs are helpful for performance analysis.
        timestamps()
    }

    environment {
        IMAGE_NAME = 'restalion/python-jenkins-pipeline'
        IMAGE_TAG  = "${env.BUILD_NUMBER}"
    }

    stages {

        // ---------------------------------------------------------------------
        // checkout
        // ---------------------------------------------------------------------
        stage('checkout') {
            steps {
                echo "==> Checkout the source code for the Python Jenkins pipeline project"
                checkout scm
            }
        }

        // ---------------------------------------------------------------------
        // setup
        // ---------------------------------------------------------------------
        stage('setup') {
            steps {
                echo "==> Prepare Python environment and install dependencies (with pip cache)"
                // Keep pip itself up-to-date
                sh 'pip install --upgrade pip'
                // Use default pip cache directory, but mapped from host via -v in agent args.
                sh 'pip install -r requirements.txt'
            }
        }

        // ---------------------------------------------------------------------
        // build
        // ---------------------------------------------------------------------
        stage('build') {
            steps {
                echo "==> Compile Python sources"
                sh 'python -m compileall .'

                echo "==> Build Docker image (no push, just local cache)"
                script {
                    def fullImage = "${IMAGE_NAME}:${IMAGE_TAG}"
                    sh "docker build -t ${fullImage} ."
                }
            }
        }

        // ---------------------------------------------------------------------
        // test
        // ---------------------------------------------------------------------
        stage('test') {
            steps {
                echo "==> Start Docker container for tests"
                script {
                    def fullImage = "${IMAGE_NAME}:${IMAGE_TAG}"
                    // Need double quotes so ${env.BUILD_NUMBER} / env vars interpolate correctly
                    sh """
                        docker run --name python-jenkins-pipeline \
                                   --detach --rm \
                                   --network ci \
                                   -p 5001:5000 \
                                   ${fullImage}
                    """
                }

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

        // ---------------------------------------------------------------------
        // quality
        // ---------------------------------------------------------------------
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
