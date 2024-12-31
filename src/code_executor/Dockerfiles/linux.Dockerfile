# Use the official .NET 8 SDK image as the base image
FROM mcr.microsoft.com/dotnet/sdk:8.0
# based on debian 12

### Install Mono and nuget
RUN apt-get update \
    && apt-get install -y gnupg ca-certificates \
    && apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys 3FA7E0328081BFF6A14DA29AA6A19B38D3D831EF \
    && echo "deb https://download.mono-project.com/repo/debian stable-buster/snapshots/6.12.0.122 main" | tee /etc/apt/sources.list.d/mono-official-stable.list \
    && apt-get update \
    && apt-get install -y mono-devel nuget \
    && rm -rf /var/lib/apt/lists/*

### Install nuget packages
RUN nuget install NUnit -Version 3.14.0 && \
	nuget install Moq -Version 4.20.69 && \
    nuget install Newtonsoft.Json -Version 13.0.3 && \
    nuget install NUnit3TestAdapter -Version 4.5.0 && \
    nuget install NUnitXml.TestLogger -Version 3.1.15 && \
    nuget install NUnit.ConsoleRunner -Version 3.16.3

### Install .NET global tools
ENV DOTNET_UPGRADEASSISTANT_TELEMETRY_OPTOUT=true
ENV DOTNET_UPGRADEASSISTANT_SKIP_FIRST_TIME_EXPERIENCE=true
# more recent versions of UA do not work on my linux
RUN dotnet tool install --global upgrade-assistant --version 0.5.586	
RUN dotnet tool install --global roslynator.dotnet.cli --version 0.8.4
# set dotnet tools path
ENV PATH="${PATH}:/root/.dotnet/tools"

### Install Java 21
WORKDIR /app
RUN apt-get update \    
    && apt-get install -y curl

RUN curl -sL https://download.java.net/java/GA/jdk21.0.2/f2283984656d49d69e91c558476027ac/13/GPL/openjdk-21.0.2_linux-x64_bin.tar.gz -o /app/jdk-21_linux-x64_bin.tar.gz \
    && tar -xvf /app/jdk-21_linux-x64_bin.tar.gz -C /app \
    && rm /app/jdk-21_linux-x64_bin.tar.gz
# add java path
ENV JAVA_HOME="/app/jdk-21.0.2"
ENV PATH="${PATH}:${JAVA_HOME}/bin"


### Install Gradle 8.5
RUN apt-get update \
    && apt-get install -y unzip \
    && curl -sL https://services.gradle.org/distributions/gradle-8.5-bin.zip -o /app/gradle-8.5-bin.zip \
    && unzip /app/gradle-8.5-bin.zip -d /app \
    && rm /app/gradle-8.5-bin.zip
# add gradle path
ENV PATH="${PATH}:/app/gradle-8.5/bin"
RUN gradle --version

### prepare templates
WORKDIR /app
COPY templates /app/templates
# Prepare the .Net Framework environment
WORKDIR /app/templates/csharp/DotnetFramework
RUN msbuild /t:restore
# remove the folder
WORKDIR /app/templates/csharp
RUN rm -rf DotnetFramework
# Prepare the .Net 8 environment
WORKDIR /app/templates/csharp/Dotnet8
RUN dotnet restore
WORKDIR /app/templates/csharp
RUN rm -rf Dotnet8
# Prepare the Java 8 environment
WORKDIR /app/templates/java8/spring-boot-payroll-example
RUN gradle build
# remove the folder
WORKDIR /app/templates/java8
RUN rm -rf spring-boot-payroll-example
# Prepare the Java 21 environment
WORKDIR /app/templates/java21/spring-boot-payroll-example
RUN gradle build
# remove the folder
WORKDIR /app/templates/java21
RUN rm -rf spring-boot-payroll-example


### Install python and pip
WORKDIR /app
RUN apt-get update \
    && apt-get install -y python3.11 python3-pip python3-venv
# Create and activate virtual environment (needed since debian 12)
RUN python3.11 -m venv /app/venv
ENV PATH="/app/venv/bin:$PATH"

# Install Python dependencies
RUN pip install --upgrade pip 
RUN pip install --upgrade setuptools
COPY tools/ ./tools
COPY requirements.txt .
RUN pip install -r requirements.txt

### Copy repo and start
COPY src/code_executor/ ./src/code_executor
ENV PYTHONPATH=.
ENV ENABLE_OTEL_LOG_HANDLER="true"
COPY config.yaml .

# Define the entry point for the container
CMD ["python", "src/code_executor/main.py"]