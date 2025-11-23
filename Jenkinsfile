pipeline {
    agent {
        // Build and tests run inside a clean Python docker image
        docker {
            image 'python:3.7'          // or bump to a newer version if your code allows (more secure)
            args  '-u root:root'
        }
    }

    environment {
        IMAGE_NAME    = 'restalion/python-jenkins-pipeline'
        PIP_CACHE_DIR = "${WORKSPACE}/.pip-cache"  // simple pip cache to speed up builds
    }

    options {
        timestamps()
        ansiColor('xterm')
    }

    stages {
        stage('checkout') {
            steps {
                // --- Checkout stage ---
                checkout scm
            }
        }

        stage('setup') {
            steps {
                // --- Setup stage ---
                sh 'mkdir -p .pip-cache'
                // Use a cache and avoid re-downloading wheels every time
                sh """
                    export PIP_CACHE_DIR=${PIP_CACHE_DIR}
                    python -m pip install --upgrade pip --disable-pip-version-check
                    pip install --no-input -r requirements.txt
                """
            }
        }

        stage('build') {
            steps {
                // --- Build stage ---
                // Compile all Python sources (quick sanity check)
                sh 'python -m compileall .'

                // Build Docker image for integration & performance tests
                sh """
                    docker build \
                      --pull \
                      -t ${IMAGE_NAME}:${env.BUILD_NUMBER} \
                      .
                """
            }
        }

        stage('test') {
            steps {
                script {
                    // --- Test stage ---
                    def appImage = "${IMAGE_NAME}:${env.BUILD_NUMBER}"

                    // Ensure network exists for container
                    sh 'docker network create ci || true'

                    // Start container once and then run tests in parallel against it
                    sh """
                        docker run \
                          --name python-jenkins-pipeline \
                          --detach --rm \
                          --network ci \
                          -p 5001:5000 \
                          ${appImage}
                    """

                    try {
                        // Parallelize logically independent test groups
                        parallel(
                            unit_and_mutation: {
                                sh """
                                    nosetests -v test

                                    cosmic-ray init config.yml jenkins_session
                                    cosmic-ray --verbose exec jenkins_session
                                    cosmic-ray dump jenkins_session | cr-report
                                """
                            },
                            integration_and_performance: {
                                sh """
                                    nosetests -v int_test

                                    # Performance tests with locust
                                    locust -f ./perf_test/locustfile.py \
                                      --no-web \
                                      -c 1000 -r 100 \
                                      --run-time 1m \
                                      -H http://172.18.0.3:5001
                                """
                            }
                        )
                    } finally {
                        // Always stop container so the agent is clean
                        sh 'docker stop python-jenkins-pipeline || true'
                    }
                }
            }
        }

        stage('quality') {
            steps {
                // --- Quality stage ---
                // Dependency vulnerability scan
                sh """
                    export PIP_CACHE_DIR=${PIP_CACHE_DIR}
                    safety check
                """

                // Static code quality/linting
                sh 'pylama'
            }
        }
    }

    post {
        always {
            // Clean up docker network if it was created
            sh 'docker network rm ci || true'
        }
    }
}
