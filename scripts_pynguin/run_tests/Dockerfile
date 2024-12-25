FROM python:3.10.14-slim-bullseye

# Install dependencies
RUN apt-get update && \
    apt-get install -y git zip curl wget gcc g++ && \
    pip install --upgrade pip setuptools wheel && \
    pip install pytest pytest-json-report pytest-cov pytest-env pytest-rerunfailures pytest-socket pytest-django

# Set working directory and copy script
COPY run_tests.sh .
RUN chmod +x run_tests.sh

# Entrypoint
ENTRYPOINT ["bash", "run_tests.sh"]
