pipeline {
    agent any

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

                    # Create virtualenv with python3 if not present
                    if [ ! -d ".venv" ]; then
                      python3 -m venv .venv
                    fi

                    . .venv/bin/activate

                    # Upgrade pip & install deps from requirements.txt
                    pip install --upgrade pip
                    pip install --disable-pip-version-check -r requirements.txt

                    # Create sitecustomize.py INSIDE THE VENV site-packages
                    python - << 'PYCODE'
import os, sysconfig

purelib = sysconfig.get_paths()["purelib"]
os.makedirs(purelib, exist_ok=True)
sc_path = os.path.join(purelib, "sitecustomize.py")

content = """import collections, collections.abc
# Patch for old libraries like nose on Python 3.10+
if not hasattr(collections, 'Callable'):
    collections.Callable = collections.abc.Callable
"""

with open(sc_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Wrote sitecustomize.py to:", sc_path)
PYCODE
                '''
            }
        }

        stage('Build') {
            environment {
                IMAGE_NAME='my-image-name'
            }
            stages {
                stage('Build Docker image') {
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
            }
        }

        stage('Test') {
            environment {
                CONTAINER_NAME='my-container-name'
            }
            stages {
                stage('Run app container and tests') {
                    steps {
                        script {
                            def venvActivate = '. .venv/bin/activate'

                            // Start app container once for all tests
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

                                            # Create a Cosmic-Ray TOML config for this run
                                            cat > cosmic_ray_config.toml << 'EOF'
[cosmic-ray]
module-path = "app"
timeout = 30.0
excluded-modules = []
test-command = "nosetests -v test int_test"

[cosmic-ray.distributor]
name = "local"
EOF

                                            # Init a new mutation session DB
                                            cosmic-ray init cosmic_ray_config.toml jenkins_session.sqlite

                                            # Run mutation tests
                                            cosmic-ray exec cosmic_ray_config.toml jenkins_session.sqlite

                                            # Report results
                                            cr-report jenkins_session.sqlite --show-pending
                                        """
                                    }
                                )
                            } finally {
                                sh 'docker stop ${CONTAINER_NAME} || true'
                            }
                        }
                    }
                }
            }
        }

        stage('Quality') {
            stages {
                stage('Check dependency vulnerabilities and code inspection') {
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
                                        # Only lint Python sources to avoid encoding issues
                                        pylama run.py app test int_test perf_test
                                    """
                                }
                            )
                        }
                    }
                }
            }
        }
    }

    post {
        always {
            cleanWs()
        }
    }
}