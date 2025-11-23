pipeline {
    agent {
        docker {
            image 'python:3.7'
            args  '-u root:root'
        }
    }

    environment {
        IMAGE_NAME    = 'restalion/python-jenkins-pipeline'
        PIP_CACHE_DIR = "${WORKSPACE}/.pip-cache"
    }

    options {
        timestamps()
        wrap([$class: 'AnsiColorBuildWrapper', 'colorMapName': 'xterm'])
    }

    stages {
        stage('checkout') {
            steps {
                checkout scm
            }
        }

        stage('setup') {
            steps {
                sh 'mkdir -p .pip-cache'
                sh """
                    export PIP_CACHE_DIR=${PIP_CACHE_DIR}
                    python -m pip install --upgrade pip --disable-pip-version-check
                    pip install --no-input -r requirements.txt
                """
            }
        }

        stage('build') {
            steps {
                sh 'python -m compileall .'
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
                    def appImage = "${IMAGE_NAME}:${env.BUILD_NUMBER}"

                    sh 'docker network create ci || true'

                    sh """
                        docker run \
                          --name python-jenkins-pipeline \
                          --detach --rm \
                          --network ci \
                          -p 5001:5000 \
                          ${appImage}
                    """

                    try {
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

                                    locust -f ./perf_test/locustfile.py \
                                      --no-web \
                                      -c 1000 -r 100 \
                                      --run-time 1m \
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

        stage('quality') {
            steps {
                sh """
                    export PIP_CACHE_DIR=${PIP_CACHE_DIR}
                    safety check
                """
                sh 'pylama'
            }
        }
    }

    post {
        always {
            sh 'docker network rm ci || true'
        }
    }
}
