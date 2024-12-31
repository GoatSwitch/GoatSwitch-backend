FROM python:3.11.9-slim-bookworm
WORKDIR /app

# Install Python dependencies
RUN pip install --upgrade pip 
RUN pip install --upgrade setuptools
COPY tools/ ./tools
COPY requirements.txt .
RUN pip install -r requirements.txt

### Copy repo and start
# NOTE: we only need a few files for few shot examples; copying the whole repo is not necessary
COPY dataset/ ./dataset
COPY templates/ ./templates
COPY src/goat_service/ ./src/goat_service

ENV PYTHONPATH=.
ARG OPENAI_API_KEY
ENV OPENAI_API_KEY=$OPENAI_API_KEY
ARG AZURE_OPENAI_API_KEY
ENV AZURE_OPENAI_API_KEY=$AZURE_OPENAI_API_KEY
ENV ENABLE_OTEL_LOG_HANDLER="true"
ARG ANTHROPIC_API_KEY
ENV ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY
COPY config.yaml .

# Define the entry point for the container
CMD ["python", "src/goat_service/main.py"]
