#!groovy

pipeline {
    // Run directly on the Jenkins node
    agent any

    environment {
        IMAGE_NAME     = "restalion/python-jenkins-pipeline"
        CONTAINER_NAME = "python-jenkins-pipeline"
        VENV_PATH      = ".venv"
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

                    # Create virtualenv (Python 3)
                    if [ ! -d ".venv" ]; then
                      python3 -m venv .venv
                    fi

                    . .venv/bin/activate

                    # Upgrade pip & install deps
                    pip install --upgrade pip
                    pip install --disable-pip-version-check -r requirements.txt

                    # Patch for nose + Python 3.10 (collections.Callable)
                    cat > sitecustomize.py << 'EOF'
import collections, collections.abc
if not hasattr(collections, "Callable"):
    collections.Callable = collections.abc.Callable
EOF
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
                    docker build -t ${IMAGE_NAME}:${BUILD_NUMBER} .
                '''
            }
        }

        stage('Test') {
            steps {
                script {
                    def venvActivate = '. .venv/bin/activate'

                    // Start app container once
                    sh """
                        set -eux
                        docker run --name ${CONTAINER_NAME} \\
                          --detach --rm \\
                          --network ci \\
                          -p 5001:5000 \\
                          ${IMAGE_NAME}:${BUILD_NUMBER}
                    """

                    try {
                        // For now: only unit + integration tests
                        sh """
                            set -eux
                            ${venvActivate}
                            nosetests -v test
                            nosetests -v int_test
                        """
                    } finally {
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
