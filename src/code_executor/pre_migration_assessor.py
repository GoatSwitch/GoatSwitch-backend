import io
import logging
import os
import re
import subprocess
import xml.etree.ElementTree as ET
import zipfile

import requests
from gs_common.CodeProject import CodeProject

"""
## Compatibility Checks
		Windows-Only Calls: Identify platform-specific calls to assess cross-platform compatibility.
		Package References Format: Identify if the project uses packages.config or PackageReference for NuGet dependencies. Recommend migration to PackageReference for better management in .NET 6.
		Interoperability Checks: Evaluate the use of COM interop, P/Invoke, and dynamic keyword usage for compatibility issues with .NET 6.
		Deprecated Security Protocols: Ensure the project does not rely on deprecated security protocols like SSL3 or TLS 1.0/1.1 and suggest moving to TLS 1.2 or higher.

## Project Structure and References
 		Project Type: Determine the project type: library, ASP.NET, WPF, WinForms, etc., as migration paths can vary.
		ASP.NET Specific Checks: For ASP.NET projects, check for WebForms usage, HTTP Modules, Handlers, and other legacy features that are not supported in .NET Core/.NET 6.

## Build and Configuration
		Configuration and Build Scripts: Review build configurations and scripts for compatibility with .NET 6, highlighting any custom MSBuild tasks or targets that might require updating.

"""

# https://learn.microsoft.com/en-us/dotnet/core/compatibility/unsupported-apis
OBSOLETE_METHODS = set(
    [
        "AppDomain.ExecuteAssembly",
        "AppDomain.Unload",
        "Console.CapsLock",
        "Console.NumberLock",
        "Delegate.GetObjectData",
        "Exception.SerializeObjectState",
        "MarshalByRefObject.GetLifetimeService",
        "MarshalByRefObject.InitializeLifetimeService",
        "OperatingSystem.GetObjectData",
        "Type.ReflectionOnlyGetType",
        "CodeDomProvider.CompileAssemblyFromDom",
        "CodeDomProvider.CompileAssemblyFromFile",
        "CodeDomProvider.CompileAssemblyFromSource",
        "NameObjectCollectionBase",
        "NameObjectCollectionBase.GetObjectData",
        "NameObjectCollectionBase.OnDeserialization",
        "System.Configuration.RsaProtectedConfigurationProvider",
        "Console.Beep",
        "Console.BufferHeight",
        "Console.BufferWidth",
        "Console.CursorSize",
        "Console.CursorVisible",
        "Console.MoveBufferArea",
        "Console.SetWindowPosition",
        "Console.SetWindowSize",
        "Console.Title",
        "Console.WindowHeight",
        "Console.WindowLeft",
        "Console.WindowTop",
        "Console.WindowWidth",
        "DbDataReader.GetSchemaTable",
        "Process.MaxWorkingSet",
        "Process.MinWorkingSet",
        "Process.ProcessorAffinity",
        "Process.MainWindowHandle",
        "Process.Start",
        "Process.Start",
        "ProcessStartInfo.UserName",
        "ProcessStartInfo.PasswordInClearText",
        "ProcessStartInfo.Domain",
        "ProcessStartInfo.LoadUserProfile",
        "ProcessThread.BasePriority",
        "ProcessThread.BasePriority",
        "ProcessThread.ProcessorAffinity",
        "FileSystemInfo",
        "FileSystemInfo.GetObjectData",
        "NamedPipeClientStream.NumberOfServerInstances",
        "NamedPipeServerStream.GetImpersonationUserName",
        "PipeStream.InBufferSize",
        "PipeStream.OutBufferSize",
        "PipeStream.ReadMode",
        "PipeStream.WaitForPipeDrain",
        "SoundPlayer",
        "AuthenticationManager.Authenticate",
        "AuthenticationManager.PreAuthenticate",
        "FileWebRequest",
        "FileWebRequest.GetObjectData",
        "FileWebResponse",
        "FileWebResponse.GetObjectData",
        "HttpWebRequest",
        "HttpWebRequest.GetObjectData",
        "HttpWebResponse",
        "HttpWebResponse.GetObjectData",
        "WebProxy",
        "WebProxy.GetDefaultProxy",
        "WebProxy.GetObjectData",
        "WebRequest",
        "WebRequest.GetObjectData",
        "WebResponse",
        "WebResponse.GetObjectData",
        "Ping.Send",
        "Socket",
        "Socket.DuplicateAndClose",
        "WebSocket.RegisterPrefixes",
        "Assembly.CodeBase",
        "Assembly.EscapedCodeBase",
        "Assembly.ReflectionOnlyLoad",
        "Assembly.ReflectionOnlyLoadFrom",
        "AssemblyName.GetObjectData",
        "AssemblyName.KeyPair",
        "AssemblyName.OnDeserialization",
        "StrongNameKeyPair",
        "StrongNameKeyPair.PublicKey",
        "DebugInfoGenerator.CreatePdbGenerator",
        "IDispatchImplAttribute",
        "Marshal.GetIDispatchForObject",
        "RuntimeEnvironment.SystemConfigurationFile",
        "RuntimeEnvironment.GetRuntimeInterfaceAsIntPtr",
        "RuntimeEnvironment.GetRuntimeInterfaceAsObject",
        "WindowsRuntimeMarshal.StringToHString",
        "WindowsRuntimeMarshal.PtrToStringHString",
        "WindowsRuntimeMarshal.FreeHString",
        "System.Runtime.Serialization.Formatters.Binary.BinaryFormatter.Serialize",
        "BinaryFormatter.Deserialize",
        "XsdDataContractExporter.Schemas",
        "CodeAccessPermission.Deny",
        "CodeAccessPermission.PermitOnly",
        "PermissionSet.ConvertPermissionSet",
        "PermissionSet.Deny",
        "PermissionSet.PermitOnly",
        "SecurityContext.Capture",
        "SecurityContext.CreateCopy",
        "SecurityContext.Dispose",
        "SecurityContext.IsFlowSuppressed",
        "SecurityContext.IsWindowsIdentityFlowSuppressed",
        "SecurityContext.RestoreFlow",
        "SecurityContext.Run",
        "SecurityContext.SuppressFlow",
        "SecurityContext.SuppressFlowWindowsIdentity",
        "ClaimsPrincipal",
        "ClaimsPrincipal.GetObjectData",
        "ClaimsIdentity",
        "ClaimsIdentity",
        "ClaimsIdentity.GetObjectData",
        "AsymmetricAlgorithm.Create",
        "System.Security.Cryptography.CngAlgorithm",
        "System.Security.Cryptography.CngAlgorithmGroup",
        "System.Security.Cryptography.CngKey",
        "System.Security.Cryptography.CngKeyBlobFormat",
        "System.Security.Cryptography.CngKeyCreationParameters",
        "System.Security.Cryptography.CngProvider",
        "System.Security.Cryptography.CngUIPolicy",
        "CryptoConfig.EncodeOID",
        "CspKeyContainerInfo",
        "CspKeyContainerInfo.Accessible",
        "CspKeyContainerInfo.Exportable",
        "CspKeyContainerInfo.HardwareDevice",
        "CspKeyContainerInfo.KeyContainerName",
        "CspKeyContainerInfo.KeyNumber",
        "CspKeyContainerInfo.MachineKeyStore",
        "CspKeyContainerInfo.Protected",
        "CspKeyContainerInfo.ProviderName",
        "CspKeyContainerInfo.ProviderType",
        "CspKeyContainerInfo.RandomlyGenerated",
        "CspKeyContainerInfo.Removable",
        "CspKeyContainerInfo.UniqueKeyContainerName",
        "ECDiffieHellmanCng.FromXmlString",
        "ECDiffieHellmanCng.ToXmlString",
        "ECDiffieHellmanCngPublicKey.FromXmlString",
        "ECDiffieHellmanCngPublicKey.ToXmlString",
        "ECDiffieHellmanPublicKey.ToByteArray",
        "ECDiffieHellmanPublicKey.ToXmlString",
        "ECDsaCng.FromXmlString",
        "ECDsaCng.ToXmlString",
        "HashAlgorithm.Create",
        "HMAC.Create",
        "HMAC.Create",
        "HMAC.HashCore",
        "HMAC.HashFinal",
        "HMAC.Initialize",
        "KeyedHashAlgorithm.Create",
        "KeyedHashAlgorithm.Create",
        "ProtectedData.Protect",
        "ProtectedData.Unprotect",
        "System.Security.Cryptography.RSACryptoServiceProvider.DecryptValue",
        "System.Security.Cryptography.RSACryptoServiceProvider.EncryptValue",
        "System.Security.Cryptography.RSA.DecryptValue",
        "System.Security.Cryptography.RSA.EncryptValue",
        "RSA.FromXmlString",
        "RSA.ToXmlString",
        "SymmetricAlgorithm.Create",
        "SymmetricAlgorithm.Create",
        "CmsSigner",
        "SignerInfo.ComputeCounterSignature",
        "X509Certificate",
        "X509Certificate.Import",
        "X509Certificate2",
        "X509Certificate2.PrivateKey",
        "ExtendedProtectionPolicy",
        "Hash.GetObjectData",
        "TimeoutException",
        "Regex.CompileToAssembly",
        "CompressedStack.GetObjectData",
        "ExecutionContext.GetObjectData",
        "Thread.Abort",
        "Thread.ResetAbort",
        "Thread.Resume",
        "Thread.Suspend",
        "XmlDictionaryReader.CreateMtomReader",
        "XmlDictionaryReader.CreateMtomReader",
        "XmlDictionaryWriter.CreateMtomWriter",
    ]
)


class PreMigrationAssessor:
    def __init__(self, source_project: CodeProject, save_dir: str):
        self.source_project = source_project
        self.save_dir = save_dir
        os.makedirs(self.save_dir, exist_ok=True)
        self.source_project.save_to_dir(self.save_dir)

        self.csproj_path, self.csproj_content = self._find_csproj()
        self.full_csproj_path = os.path.join(self.save_dir, self.csproj_path)
        self.csproj_root = self._parse_csproj()
        self._process_csproj()

    def _find_csproj(self) -> tuple[str, str]:
        for file in self.source_project.files:
            if file.file_name.endswith(".csproj"):
                return file.file_name, file.source_code
        raise FileNotFoundError("No csproj file found in the project")

    def _parse_csproj(self) -> ET.Element:
        # use xml parser to parse the csproj file
        root = ET.fromstring(self.csproj_content)
        # remove namespace from tags
        for elem in root.iter():
            if "}" in elem.tag:
                elem.tag = elem.tag.split("}", 1)[1]
        return root

    def _process_csproj(self) -> str:
        # target framework
        self.target_framework_version = self.csproj_root.find(
            ".//TargetFrameworkVersion"
        )
        # project type
        self.output_type = self.csproj_root.find(".//OutputType")
        # project references
        self.project_references = self.csproj_root.findall(".//ProjectReference")

        # add all references
        self.references = self.csproj_root.findall(".//Reference")

        # hardcoded dlls
        self.hardcoded_dlls_dict = {}
        for dll in self.references:
            hint_path = dll.find(".//HintPath")
            if hint_path is None:
                continue
            hint_path = hint_path.text

            # get all hardcoded dlls with "packages\" in the hint path
            # <Reference Include="NLog">
            #  <HintPath>packages\NLog.4.5.11\lib\net45\NLog.dll</HintPath>
            if "packages\\" in hint_path:
                if "Include" not in dll.attrib:
                    continue
                dll_name = dll.attrib["Include"]
                # normalize path with os.path.join
                hint_path = os.path.normpath(hint_path)
                # get version from path (without package name)
                version = hint_path.split("packages\\")[1].split("\\")[0]
                version_parts = version.split(".")
                if len(version_parts) < 4:
                    logging.warning(f"Could not extract version from {hint_path}")
                    continue
                elif len(version_parts) == 4:
                    version = ".".join(version_parts[-3:])
                else:
                    version = ".".join(version_parts[-4:])
                self.hardcoded_dlls_dict[dll_name] = version

        # find all package references with version
        # <PackageReference Include="Newtonsoft.Json">
        #  <Version>11.0.2</Version>
        # </PackageReference>
        self.package_references = self.csproj_root.findall(".//PackageReference")
        self.package_references_dict = {}
        for package in self.package_references:
            if "Include" not in package.attrib:
                logging.warning(f"No Include attribute found in package {package}")
            package_name = package.attrib["Include"]

            if "Version" in package.attrib:
                version = package.attrib["Version"]
            elif package.find(".//Version") is not None:
                version = package.find(".//Version").text
            else:
                logging.warning(f"No version found for {package_name}")
                continue

            self.package_references_dict[package_name] = version

    def assess(self) -> CodeProject:
        report = "# Migration Situation Explanation\n"
        try:
            report += self.analyze_csproj()
        except Exception as e:
            report += f"\nError analyzing csproj: {e}\n"
        try:
            report += self.analyze_nuget_packages()
        except Exception as e:
            report += f"\nError analyzing nuget packages: {e}\n"
        try:
            report += self.analyze_obsolete_methods()
        except Exception as e:
            report += f"\nError analyzing obsolete methods: {e}\n"
        try:
            report += self.analyze_source_code()
        except Exception as e:
            report += f"\nError analyzing source code: {e}\n"

        # convert to CodeProject
        assessment_project = CodeProject(
            display_name=self.source_project.display_name,
            files=[
                {
                    "file_name": "pre_migration_assessment.md",
                    "source_code": report,
                }
            ],
            source_language="markdown",
        )
        return assessment_project

    def analyze_csproj(self) -> str:
        report = "## CSProj Analysis\n"
        report += f"\nTarget Framework\n>{self.target_framework_version.text}\n"
        report += f"\nOutput Type\n>{self.output_type.text}\n"
        report += "\n\nProject References:\n"
        for ref in self.project_references:
            report += f"- {ref.attrib['Include']}\n"

        report += "\n\nReferences:\n"
        for dll in self.references:
            include = dll.attrib["Include"]
            hint_path = dll.find(".//HintPath")
            if hint_path is None:
                report += f"- {include}\n"
            else:
                hint_path = hint_path.text
                report += f"- {include}: {hint_path}\n"

        report += "\n\nPackage References:\n"
        for package_name, version in self.package_references_dict.items():
            report += f"- {package_name}: {version}\n"
        return report

    def analyze_source_code(self) -> str:
        # use roslynator to analyze the source code
        # count loc
        report = "\n## Source Code Analysis\n"
        command = f"roslynator loc {self.full_csproj_path}"
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.stderr != "":
            raise Exception(
                f"Failed to analyze the source code: stdout: {result.stdout}, stderr: {result.stderr}"
            )
        # remove first 3 lines and last 2 lines
        lines = result.stdout.splitlines()
        report += "\n### Lines of Code\n"
        """
        2,182 49 % lines of code
        687 15 % white-space lines
        1,419 32 % comment lines
        148 3 % preprocessor directive lines
        4,436 100 % total lines

        out:
        lines of code 2,182 49 %
        white-space lines 687 15 %
        ...

        """
        # make a markdown table of these lines
        report += "| Type | Lines | Percentage |\n"
        report += "| --- | --- | --- |\n"
        for line in lines[3:-2]:
            parts = line.split()
            if len(parts) < 4:
                continue
            lines = parts[0]
            percentage = parts[1]
            loc_type = " ".join(parts[3:])
            report += f"| {loc_type} | {lines} | {percentage} |\n"

        # analyze
        command = f"roslynator analyze {self.full_csproj_path}"
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.stderr != "":
            raise Exception(
                f"Failed to analyze the source code: stdout: {result.stdout}, stderr: {result.stderr}"
            )
        # remove first 1 line and last 2 lines
        lines = result.stdout.splitlines()
        report += "\n### Static Analysis\n- "
        report += "\n- ".join(lines[3:-5]) + "\n"

        # list symbols
        command = f"roslynator list-symbols {self.full_csproj_path}"
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.stderr != "":
            raise Exception(
                f"Failed to analyze the source code: stdout: {result.stdout}, stderr: {result.stderr}"
            )
        # remove first 1 line and last 2 lines
        lines = result.stdout.splitlines()
        report += "\n### List of Symbols\n"
        report += "```csharp\n"
        report += "\n".join(lines[4:-2]) + "\n"
        report += "```\n"

        return report

    def analyze_nuget_packages(self) -> str:
        # check if the current used version in csproj is available for .net8
        report = "\n## NuGet Package Analysis\n"
        if not self.package_references_dict and not self.hardcoded_dlls_dict:
            return report + ">No NuGet package references found\n"
        for package, version in self.package_references_dict.items():
            report += self._check_nuget_package_compatibility(package, version)

        for dll, version in self.hardcoded_dlls_dict.items():
            report += self._check_nuget_package_compatibility(dll, version)

        return report

    def _check_nuget_package_compatibility(self, package_id, package_version) -> str:
        # Construct the URL according to NuGet API v3
        # use nuget api to check if the package is available for .net8
        report = f"\n{package_id} {package_version}\n"
        base_url = "https://api.nuget.org/v3-flatcontainer"
        lower_id = package_id.lower()
        lower_version = package_version.lower()
        download_url = (
            f"{base_url}/{lower_id}/{lower_version}/{lower_id}.{lower_version}.nupkg"
        )

        # Download the .nupkg file and find available target frameworks
        response = requests.get(download_url)
        target_frameworks = []
        if response.status_code == 200:
            # Open the .nupkg as a zip file in memory
            with zipfile.ZipFile(io.BytesIO(response.content)) as package_zip:
                # List all files and directories in the .nupkg file
                for file_info in package_zip.infolist():
                    if not file_info.filename.lower().startswith("lib/net"):
                        continue
                    # e.g. lib/netstandard2.0/Newtonsoft.Json.dll
                    # e.g. lib/net5.0/Newtonsoft.Json.dll
                    # extract all monikers: netstandard, net5, ...
                    moniker = file_info.filename.lower().split("/")[1]
                    target_frameworks.append(moniker)
        else:
            logging.info(
                f"Failed to download {package_id} {package_version}: {response.status_code}"
            )
            report += f"> Warning: Failed to download {package_id} {package_version}: {response.status_code}\n"
            return report

        sorted(target_frameworks)
        report += f"- Available Target Frameworks: {target_frameworks}\n"

        if any(tf.startswith("netstandard") for tf in target_frameworks):
            report += "> Found netstandard, should be compatible.\n"
        elif "net8.0" in target_frameworks:
            report += "> Found net8.0, should be compatible.\n"
        elif "net6.0" in target_frameworks:
            report += "> Found net6.0, should be compatible.\n"
        elif "net5.0" in target_frameworks:
            report += "> Found net5.0, should be compatible.\n"
        else:
            report += "> Warning: no compatible target framework found.\n"

        return report

    def analyze_obsolete_methods(self) -> str:
        # Creating a regex pattern to match any of the method names
        # \b is used for word boundary to ensure exact matches
        report = "\n## Obsolete Methods\n"
        pattern = (
            r"\b(" + "|".join(re.escape(method) for method in OBSOLETE_METHODS) + r")\b"
        )
        compiled_pattern = re.compile(pattern)

        file_to_obsolete_methods = {}
        for file in self.source_project.files:
            lines = file.source_code.splitlines()
            # Use a set to store found methods to avoid duplicates
            found_methods = set()
            for line in lines:
                # Search for the pattern in the current line
                matches = compiled_pattern.findall(line)
                if matches:
                    found_methods.update(matches)

            if found_methods:
                # Convert set to list for JSON serializability or other uses
                file_to_obsolete_methods[file.file_name] = list(found_methods)

        if not file_to_obsolete_methods:
            return report + "No obsolete methods found\n"

        for file, methods in file_to_obsolete_methods.items():
            report += f"File: {file}\n"
            for method in methods:
                report += f"- {method}\n"
        return report
