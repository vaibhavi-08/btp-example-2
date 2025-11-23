#!groovy

pipeline {
    // Run directly on the Jenkins node (host),
    // which already has Docker installed.
    agent any

    environment {
        IMAGE_NAME = "restalion/python-jenkins-pipeline"
        CONTAINER_NAME = "python-jenkins-pipeline"
        VENV_PATH = ".venv"
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Setup') {
            steps {
                sh '''
                    set -eux

                    # Create virtualenv if it doesn't exist
                    if [ ! -d ".venv" ]; then
                      python3 -m venv .venv
                    fi

                    . .venv/bin/activate

                    # Upgrade pip & install dependencies
                    pip install --upgrade pip
                    pip install --disable-pip-version-check -r requirements.txt
                '''
            }
        }

        stage('Build') {
            steps {
                sh '''
                    set -eux
                    . .venv/bin/activate

                    # Compile Python sources
                    python -m compileall .

                    # Ensure Docker network exists
                    docker network create ci || true

                    # Build Docker image (no push/deploy)
                    docker build -t restalion/python-jenkins-pipeline:${BUILD_NUMBER} .
                '''
            }
        }

        stage('Test') {
            steps {
                script {
                    def venvActivate = '. .venv/bin/activate'

                    // Start the app container once
                    sh """
                        set -eux

                        docker run --name ${CONTAINER_NAME} \\
                          --detach --rm \\
                          --network ci \\
                          -p 5001:5000 \\
                          ${IMAGE_NAME}:${BUILD_NUMBER}
                    """

                    try {
                        parallel(
                            Unit_and_Integration: {
                                sh """
                                    set -eux
                                    ${venvActivate}
                                    # Unit tests
                                    nosetests -v test
                                    # Integration tests
                                    nosetests -v int_test
                                """
                            },
                            Mutation_Tests: {
                                sh """
                                    set -eux
                                    ${venvActivate}
                                    cosmic-ray init config.yml jenkins_session
                                    cosmic-ray --verbose exec jenkins_session
                                    cosmic-ray dump jenkins_session | cr-report
                                """
                            },
                            Performance_Tests: {
                                sh """
                                    set -eux
                                    ${venvActivate}
                                    # Performance tests with Locust
                                    locust -f ./perf_test/locustfile.py \\
                                      --no-web -c 1000 -r 100 \\
                                      --run-time 1m \\
                                      -H http://172.18.0.3:5001
                                """
                            }
                        )
                    } finally {
                        // Always stop container
                        sh 'docker stop ${CONTAINER_NAME} || true'
                    }
                }
            }
        }

        stage('Quality') {
            steps {
                script {
                    def venvActivate = '. .venv/bin/activate'

                    parallel(
                        Dependency_Vulnerabilities: {
                            sh """
                                set -eux
                                ${venvActivate}
                                safety check
                            """
                        },
                        Code_Inspection: {
                            sh """
                                set -eux
                                ${venvActivate}
                                pylama
                            """
                        }
                    )
                }
            }
        }
    }
}
