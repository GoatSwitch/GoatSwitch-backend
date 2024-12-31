# Use the official Windows Server Core image with .NET Framework 4.8 SDK
FROM mcr.microsoft.com/dotnet/framework/sdk:4.8.1
# this base image includes .NET 8 and NuGet
# add dotnet path
ENV PATH="${PATH};C:\\Program Files\\dotnet\\;C:\\Users\\ContainerAdministrator\\.dotnet\\tools;C:\\Program Files\\NuGet"
# add msbuild path
ENV PATH="${PATH};C:\\Program Files (x86)\\Microsoft Visual Studio\\2022\\BuildTools\\MSBuild\\Current\\Bin\\amd64;C:\\Program Files (x86)\\Microsoft SDKs\\Windows\\v10.0A\\bin\\NETFX 4.8.1 Tools"
# add powershell path
ENV PATH="${PATH};C:\\Windows\\system32;C:\\Windows;C:\\Windows\\System32\\Wbem;C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\"

# enable long paths
RUN reg add "HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\FileSystem" /v LongPathsEnabled /t REG_DWORD /d 1 /f

WORKDIR /app

### Install nuget packages
RUN powershell -Command \
    $ErrorActionPreference = 'Stop'; \
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12 ; \
    nuget install NUnit -Version 3.14.0 ; \
    nuget install Moq -Version 4.20.69 ; \
    nuget install Newtonsoft.Json -Version 13.0.3 ; \
    nuget install NUnit3TestAdapter -Version 4.5.0 ; \
    nuget install NUnitXml.TestLogger -Version 3.1.15 ; \
    nuget install NUnit.ConsoleRunner -Version 3.16.3

### Install .NET global tools
ENV DOTNET_UPGRADEASSISTANT_TELEMETRY_OPTOUT=true
ENV DOTNET_UPGRADEASSISTANT_SKIP_FIRST_TIME_EXPERIENCE=true
# more recent versions of UA do not work on my linux
RUN dotnet tool install --global upgrade-assistant --version 0.5.586	
RUN dotnet tool install --global roslynator.dotnet.cli --version 0.8.4

### prepare templates
WORKDIR /app
COPY templates /app/templates
# Prepare the .Net Framework environment
WORKDIR /app/templates/csharp/DotnetFramework
RUN msbuild /t:restore
WORKDIR /app/templates/csharp
RUN powershell -Command "Remove-Item -Path C:\\app\\templates\\csharp\\DotnetFramework -Recurse -Force"
# Prepare the .Net 8 environment
WORKDIR /app/templates/csharp/Dotnet8
RUN dotnet restore
WORKDIR /app/templates/csharp
RUN powershell -Command "Remove-Item -Path C:\\app\\templates\\csharp\\Dotnet8 -Recurse -Force"

### Install Python and Pip (Windows)
# TODO: use python 3.11 like linux dockers
WORKDIR /app
RUN powershell -Command \
    $ErrorActionPreference = 'Stop'; \
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12 ; \
    Invoke-WebRequest https://www.python.org/ftp/python/3.9.0/python-3.9.0-amd64.exe -OutFile C:\\app\\python39.exe ; \
    Start-Process C:\\app\\python39.exe -ArgumentList '/quiet InstallAllUsers=1 PrependPath=1' -Wait ; \
    Remove-Item C:\\app\\python39.exe -Force
ENV PATH="${PATH};C:\\Program Files\\Python39\\Scripts\\;C:\\Program Files\\Python39\\"

### Install Vim for debugging
RUN powershell -Command \
    Set-ExecutionPolicy Bypass -Scope Process -Force ; \
    [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072 ; \
    iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))
ENV PATH="${PATH};C:\\ProgramData\\chocolatey\\bin"
RUN powershell -Command \
    choco install vim -y

### Install Python dependencies
RUN pip install --upgrade pip 
RUN pip install --upgrade setuptools
COPY tools/ ./tools
COPY requirements.txt .
RUN pip install -r requirements.txt

### Copy repo and start
COPY src/code_executor/ ./src/code_executor
ENV PYTHONPATH=.
ARG OPENAI_API_KEY
ENV OPENAI_API_KEY=$OPENAI_API_KEY
ARG AZURE_OPENAI_API_KEY
ENV AZURE_OPENAI_API_KEY=$AZURE_OPENAI_API_KEY
ENV ENABLE_OTEL_LOG_HANDLER="true"
COPY config.yaml .

# Define the entry point for the container
CMD ["python", "src/code_executor/main.py"]
