# Requirements for building and development
- [.NET SDK 7.0](https://dotnet.microsoft.com/en-us/download/dotnet/7.0)
- [npm](https://nodejs.org/en/download)

*INFO: The installation of .NET SDK is only needed on the machine building the application. A release build will be shipped out with all the dependencies it needs so no further installations have to be done on the target machine.*

# [CLI] How to build for production use
## Linux (64 bit)
* Go to source directory where .csproj is located
* Run `dotnet publish -r linux-x64 -c Release --sc true`
* The results are then located in `bin/Release/net8.0/linux-x64/publish`
* The application can be run by directly calling the executable `./API_Gateway`

# [CLI] How to run during development on local machine
## Start server 
* Go to source directory where **API_Gateway.csproj** is located
* Run `dotnet run`
* The application can be accessed at https://localhost:5050
