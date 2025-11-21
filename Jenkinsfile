pipeline {
    agent any

    options {
        timestamps()
        disableConcurrentBuilds()
    }

    environment {
        PYTHONUNBUFFERED = '1'
        // Optional: customize these for Docker image
        IMAGE_NAME = 'my-python-app'
        IMAGE_TAG  = "${env.BRANCH_NAME}-${env.BUILD_NUMBER}"
    }

    stages {

        stage('Checkout') {
            steps {
                // Simple checkout; no submodules/LFS according to JSON
                checkout scm
            }
        }

        stage('Setup') {
            steps {
                sh '''
                    set -e

                    # Create and reuse local virtualenv for faster builds
                    if [ ! -d ".venv" ]; then
                      python3 -m venv .venv
                    fi

                    . .venv/bin/activate

                    # Optional: compile requirements if pip-compile is available
                    if command -v pip-compile >/dev/null 2>&1; then
                      echo "[Setup] Running pip-compile for locked dependencies..."
                      pip-compile
                    else
                      echo "[Setup] pip-compile not available; skipping lockfile compilation."
                    fi

                    echo "[Setup] Upgrading pip and installing dependencies..."
                    pip install --upgrade pip
                    pip install -r requirements.txt
                '''
            }
        }

        stage('Build') {
            steps {
                sh '''
                    set -e
                    . .venv/bin/activate

                    echo "[Build] Running application build step (python run.py)..."
                    python run.py
                '''
            }
        }

        stage('Test') {
            when {
                expression {
                    // Only run if we have a test directory
                    return fileExists('test') || fileExists('tests')
                }
            }
            steps {
                sh '''
                    set -e
                    . .venv/bin/activate

                    TEST_DIR="test"
                    if [ ! -d "$TEST_DIR" ] && [ -d "tests" ]; then
                      TEST_DIR="tests"
                    fi

                    echo "[Test] Using test directory: $TEST_DIR"

                    if command -v pytest >/dev/null 2>&1; then
                      echo "[Test] Detected pytest, running pytest..."
                      pytest "$TEST_DIR"
                    else
                      echo "[Test] pytest not found; falling back to unittest..."
                      python -m unittest discover -s "$TEST_DIR"
                    fi
                '''
            }
        }

        stage('Quality') {
            steps {
                sh '''
                    set +e
                    . .venv/bin/activate

                    echo "[Quality] Running lint and security checks where available..."

                    # Lint: pylama
                    if command -v pylama >/dev/null 2>&1; then
                      echo "[Quality] Running pylama..."
                      pylama .
                      PYLAMA_STATUS=$?
                    else
                      echo "[Quality] pylama not installed; skipping lint."
                      PYLAMA_STATUS=0
                    fi

                    # Security: safety
                    if command -v safety >/dev/null 2>&1; then
                      echo "[Quality] Running safety dependency scan..."
                      safety check
                      SAFETY_STATUS=$?
                    else
                      echo "[Quality] safety not installed; skipping dependency vulnerability scan."
                      SAFETY_STATUS=0
                    fi

                    # Security: snyk (requires auth token configured in env)
                    if command -v snyk >/dev/null 2>&1; then
                      echo "[Quality] Running Snyk security test..."
                      snyk test
                      SNYK_STATUS=$?
                    else
                      echo "[Quality] snyk not installed; skipping Snyk security scan."
                      SNYK_STATUS=0
                    fi

                    # Fail stage only if any tool explicitly fails
                    if [ $PYLAMA_STATUS -ne 0 ] || [ $SAFETY_STATUS -ne 0 ] || [ $SNYK_STATUS -ne 0 ]; then
                      echo "[Quality] One or more quality checks failed."
                      exit 1
                    else
                      echo "[Quality] All available quality checks passed."
                    fi
                '''
            }
        }

        stage('Package') {
            when {
                expression {
                    // No explicit packaging info in JSON; keep light and skippable
                    return false
                }
            }
            steps {
                echo "No packaging configuration defined; skipping Package stage."
            }
        }

        stage('Deploy') {
            when {
                expression {
                    // Only allow deploy on main/master and keep it manual
                    return env.BRANCH_NAME == 'main' || env.BRANCH_NAME == 'master'
                }
            }
            steps {
                script {
                    input message: "Deploy by building Docker image?", ok: "Deploy"
                }
                sh '''
                    set -e

                    . .venv/bin/activate || true

                    echo "[Deploy] Building Docker image ${IMAGE_NAME}:${IMAGE_TAG} ..."
                    docker build -t "${IMAGE_NAME}:${IMAGE_TAG}" .
                '''
            }
        }
    }
}