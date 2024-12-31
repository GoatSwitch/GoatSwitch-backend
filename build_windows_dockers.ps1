# don't build gateway docker on windows. just start it with dapr run
#docker build --pull --rm -f "src/goat_service/Dockerfiles/windows.Dockerfile" -t goatswitch_goat_service:latest ./ --build-arg OPENAI_API_KEY=$env:OPENAI_API_KEY --build-arg AZURE_OPENAI_API_KEY=$env:AZURE_OPENAI_API_KEY
docker build --pull --rm -f "src/code_executor/Dockerfiles/windows.Dockerfile" -t goatswitch_code_executor:latest ./ 
