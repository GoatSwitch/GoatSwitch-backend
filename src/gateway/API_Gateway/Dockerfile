FROM mcr.microsoft.com/dotnet/sdk:8.0 AS build
ARG TARGETARCH=amd64
RUN echo "Building for ARCH $TARGETARCH"
WORKDIR /app

RUN apt update
RUN apt install certbot -y

# Build gateway
COPY src/gateway/ .
COPY tools/gs_common/gs_common/proto /tools/gs_common/gs_common/proto
WORKDIR /app/API_Gateway/
RUN dotnet publish -c Release --self-contained true -a $TARGETARCH  -o /app/publish
SHELL ["/bin/bash", "--login", "-c"]

# Build final image with gateway executable and examples
FROM mcr.microsoft.com/dotnet/runtime:8.0 AS final
WORKDIR /app/API_Gateway

COPY src/gateway/API_Gateway/API_Gateway/Misc ./Misc

ARG AZ_TABLES_CONNECTION_STRING
ENV AZ_TABLES_CONNECTION_STRING=$AZ_TABLES_CONNECTION_STRING

ENV ASPNETCORE_ENVIRONMENT=Development
ENV ASPNETCORE_URLS=http://+:5000

EXPOSE 5000
COPY --from=build /app/publish .
CMD ["./API_Gateway"]