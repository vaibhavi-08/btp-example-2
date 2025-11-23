#!groovy

pipeline {
    // Use a Docker agent with Python and access to host Docker
    agent {
        docker {
            image 'python:3.7'
            // Allow Docker CLI inside the container (adjust socket path if needed)
            args '-u root:root -v /var/run/docker.sock:/var/run/docker.sock'
        }
    }

    stages {

        stage('Checkout') {
            steps {
                // === Checkout ===
                // From your JSON: "checkout scm"
                checkout scm
            }
        }

        stage('Setup') {
            steps {
                // === Setup ===
                // Prepare venv + install deps (with pip upgrade)
                sh '''
                    set -eux

                    # Create virtualenv if it doesn't exist
                    if [ ! -d ".venv" ]; then
                      python -m venv .venv
                    fi

                    . .venv/bin/activate

                    # Upgrade pip & install dependencies
                    pip install --upgrade pip
                    # Disable version check for a tiny speedup
                    pip install --disable-pip-version-check -r requirements.txt
                '''
            }
        }

        stage('Build') {
            steps {
                // === Build ===
                sh '''
                    set -eux
                    . .venv/bin/activate

                    # Compile Python sources (from original "Compile" stage)
                    python -m compileall .

                    # Ensure a dedicated Docker network exists (used later for tests)
                    docker network create ci || true

                    # Build Docker image but do NOT push/deploy
                    docker build -t restalion/python-jenkins-pipeline:${BUILD_NUMBER} .
                '''
            }
        }

        stage('Test') {
            steps {
                script {
                    // We'll reuse this in all sh calls in this stage
                    def venvActivate = '. .venv/bin/activate'

                    // Start the container once, then run tests in parallel
                    sh """
                        set -eux

                        docker run --name python-jenkins-pipeline \\
                          --detach --rm \\
                          --network ci \\
                          -p 5001:5000 \\
                          restalion/python-jenkins-pipeline:${BUILD_NUMBER}
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
                                    # Mutation tests with cosmic-ray
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
                                    # (IP/port from your original command)
                                    locust -f ./perf_test/locustfile.py \\
                                      --no-web -c 1000 -r 100 \\
                                      --run-time 1m \\
                                      -H http://172.18.0.3:5001
                                """
                            }
                        )
                    } finally {
                        // Always stop container even if tests fail
                        sh 'docker stop python-jenkins-pipeline || true'
                    }
                }
            }
        }

        stage('Quality') {
            steps {
                script {
                    def venvActivate = '. .venv/bin/activate'

                    // Run safety + pylama in parallel to save time
                    parallel(
                        Dependency_Vulnerabilities: {
                            sh """
                                set -eux
                                ${venvActivate}
                                # Dependency vulnerability scan
                                safety check
                            """
                        },
                        Code_Inspection: {
                            sh """
                                set -eux
                                ${venvActivate}
                                # Lint / quality gate
                                pylama
                            """
                        }
                    )
                }
            }
        }
    }
}
