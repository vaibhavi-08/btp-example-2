#!groovy

pipeline {
    // 🔴 OLD (causing the error):
    // agent {
    //     docker {
    //         image 'python:3.7'
    //         args '-u root:root -v /var/run/docker.sock:/var/run/docker.sock'
    //     }
    // }

    // ✅ NEW: use a modern Python version compatible with Werkzeug>=3, locust, safety, etc.
    agent {
        docker {
            image 'python:3.10-slim'
            // or 'python:3.11-slim' if you like
            args '-u root:root -v /var/run/docker.sock:/var/run/docker.sock'
        }
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

                    if [ ! -d ".venv" ]; then
                      python -m venv .venv
                    fi

                    . .venv/bin/activate

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

                    python -m compileall .

                    docker network create ci || true

                    docker build -t restalion/python-jenkins-pipeline:${BUILD_NUMBER} .
                '''
            }
        }

        stage('Test') {
            steps {
                script {
                    def venvActivate = '. .venv/bin/activate'

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
                                    nosetests -v test
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
                                    locust -f ./perf_test/locustfile.py \\
                                      --no-web -c 1000 -r 100 \\
                                      --run-time 1m \\
                                      -H http://172.18.0.3:5001
                                """
                            }
                        )
                    } finally {
                        sh 'docker stop python-jenkins-pipeline || true'
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
