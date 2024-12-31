#!/bin/bash 
set -e 

# docker build --pull --rm -f "src/gateway/API_Gateway/Dockerfile" -t goatswitch_gateway:latest ./ --build-arg AZ_TABLES_CONNECTION_STRING=$AZ_TABLES_CONNECTION_STRING
docker build --pull --rm -f "src/goat_service/Dockerfiles/linux.Dockerfile" -t goatswitch_goat_service:latest ./ --build-arg OPENAI_API_KEY=$OPENAI_API_KEY --build-arg AZURE_OPENAI_API_KEY=$AZURE_OPENAI_API_KEY
# docker build --pull --rm -f "src/code_executor/Dockerfiles/java.Dockerfile" -t goatswitch_code_executor_java:latest ./