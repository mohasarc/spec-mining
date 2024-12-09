FROM python:3.10.14-slim-bullseye

# Install dependencies
RUN apt-get update && \
    apt-get install -y git zip && \
    pip install --upgrade pip setuptools wheel && \
    pip install pytest && \
    pip install git+https://github.com/se2p/pynguin.git@0.39.0

# Environment variables
ENV PYNGUIN_DANGER_AWARE=true

# Set working directory and copy script
COPY run.sh .
RUN chmod +x run.sh

# Entrypoint
ENTRYPOINT ["bash", "run.sh"]