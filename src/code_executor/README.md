# Setup code_executor for .Net-Framework 4.8 to .Net8

- .Net8 should be already install from main README.md
- install .Net-Framework for wsl2 ubuntu22
- follow: https://www.mono-project.com/download/stable/#download-lin-ubuntu
- example

```
sudo apt install ca-certificates gnupg
sudo gpg --homedir /tmp --no-default-keyring --keyring /usr/share/keyrings/mono-official-archive-keyring.gpg --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys 3FA7E0328081BFF6A14DA29AA6A19B38D3D831EF
echo "deb [signed-by=/usr/share/keyrings/mono-official-archive-keyring.gpg] https://download.mono-project.com/repo/ubuntu stable-focal main" | sudo tee /etc/apt/sources.list.d/mono-official-stable.list
sudo apt update
sudo apt install mono-devel
```

- now install nuget and some basic packages

```
sudo apt install nuget
nuget install NUnit -Version 3.14.0
nuget install Moq -Version 4.20.69
nuget install Newtonsoft.Json -Version 13.0.3
nuget install NUnit3TestAdapter -Version 4.5.0
nuget install NUnitXml.TestLogger -Version 3.1.15
nuget install NUnit.ConsoleRunner -Version 3.16.3
```

- enable long paths in windows

```
reg add HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\FileSystem /v LongPathsEnabled /t REG_DWORD /d 1 /f
reg query HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\FileSystem /v LongPathsEnabled
```

# Setup code_executor for java 8 to java 21

- install java 21 jdk
- install gradle 8.5
- java8 not needed; gradle toolchain is backward compatible
- set JAVA_HOME to java 21 and add gradle to path

```
wget https://services.gradle.org/distributions/gradle-8.5-bin.zip
# unzip and move to ~
sudo apt install openjdk-21-jdk
# e.g. in $PROFILE
$env:JAVA_HOME = "C:\Program Files\Java\jdk-21\"
$env:Path += ";C:\Gradle\gradle-8.5\bin"
```

- PSA: java needs at least 8g memory in docker

# How to run tests

## Run in docker

- build language-pair specific docker image (see build_all.sh)
- run tests for specific language-pair, e.g. dotnetframework-dotnet8:

```
docker run --entrypoint "pytest" --rm -v ${PWD}\test:C:\app\test goatswitch_goat_service .\test\goat_service\test_ce\test_code_executor_dotnetframework_dotnet8.py
```

## Run locally

- pytest test/
- optional:
  - coverage run -m pytest
  - coverage report
- run tests for main.py
- dapr run pytest test_main.py
