import os
import logging
import xml.etree.ElementTree as ET

from gs_common.CodeProject import CodeFile, CodeProject

from src.code_executor.code_formatter import CodeFormatter


class DotnetFrameworkCodeFormatter(CodeFormatter):
    @staticmethod
    def format(project: CodeProject) -> CodeProject:
        csproj_file = DotnetFrameworkCodeFormatter.get_main_csproj_file(project)
        root = DotnetFrameworkCodeFormatter.read_and_format_csproj_file(csproj_file)
        DotnetFrameworkCodeFormatter.set_internals_visible_to_testproject(
            project, root, csproj_file.file_name
        )
        DotnetFrameworkCodeFormatter.disable_sign_assembly(root)
        DotnetFrameworkCodeFormatter.set_framework_version_to_48(root)
        DotnetFrameworkCodeFormatter.add_default_output_path(root)
        csproj_file.source_code = ET.tostring(root, encoding="unicode")
        csproj_file.source_code = DotnetFrameworkCodeFormatter.replace_packages_dotdot(
            csproj_file.source_code
        )
        csproj_file.source_code = DotnetFrameworkCodeFormatter.remove_ico_references(
            csproj_file.source_code
        )
        return project

    @staticmethod
    def get_main_csproj_file(project: CodeProject):
        # get all .csproj files
        csproj_files = [
            file for file in project.files if file.file_name.endswith(".csproj")
        ]
        # may only be one
        if len(csproj_files) != 1:
            raise Exception(
                f"Expected exactly one .csproj file, but found {len(csproj_files)}: {[file.file_name for file in csproj_files]}"
            )
        return csproj_files[0]

    @staticmethod
    def read_and_format_csproj_file(csproj_file: CodeFile):
        root = ET.fromstring(csproj_file.source_code)
        # we have different namespaces
        # for old csprojs: http://schemas.microsoft.com/developer/msbuild/2003
        # for new sdk style csprojs Microsoft.NET.Sdk
        # remove the namespace everywhere
        for elem in root.iter():
            if "}" in elem.tag:
                elem.tag = elem.tag.split("}", 1)[1]
        return root

    @staticmethod
    def disable_sign_assembly(root: ET.Element):
        for sign_assembly in root.findall(".//SignAssembly"):
            sign_assembly.text = "false"

    @staticmethod
    def replace_packages_dotdot(xml_content: str):
        # use the raw string here because else we would have to parse all elems and attribs
        while "../packages" in xml_content or "..\\packages" in xml_content:
            xml_content = xml_content.replace("../packages", "packages")
            xml_content = xml_content.replace("..\\packages", "packages")
        return xml_content

    @staticmethod
    def set_internals_visible_to_testproject(
        project: CodeProject, root: ET.Element, csproj_file_name: str
    ):
        using_to_insert = "using System.Runtime.CompilerServices;"
        # NOTE: let's hope the user does not change the test project name
        test_project_name = (
            os.path.basename(csproj_file_name).replace(".csproj", "") + "-GSTests"
        )
        attribute_to_insert = f'[assembly: InternalsVisibleTo("{test_project_name}")]'
        assembly_info_file = next(
            (
                file
                for file in project.files
                if file.file_name.endswith("AssemblyInfo.cs")
            ),
            None,
        )

        if assembly_info_file is not None:
            # do not insert if it already exists; else compile error on net6 (net8 is fine)
            if using_to_insert in assembly_info_file.source_code:
                using_to_insert = ""
            assembly_info_file.source_code = (
                using_to_insert
                + "\n"
                + assembly_info_file.source_code
                + "\n"
                + attribute_to_insert
            )
        else:
            base_dir_csproj = os.path.dirname(csproj_file_name)
            assembly_info_path = os.path.join(
                base_dir_csproj, "Properties", "AssemblyInfo.cs"
            )
            project.files.append(
                CodeFile(
                    file_name=assembly_info_path,
                    source_code=using_to_insert + "\n" + attribute_to_insert,
                )
            )
            if not root.get("Sdk") and not root.get("sdk"):
                item_group = ET.SubElement(root, "ItemGroup")
                compile = ET.SubElement(item_group, "Compile")
                compile.set("Include", "Properties\\AssemblyInfo.cs")

    @staticmethod
    def set_framework_version_to_48(root: ET.Element):
        # NOTE: windows docker can only do specific versions of .NET Framework
        # -> just change very old csprojs to 4.8 and hope that it compiles
        # extra NOTE: for linux mono docker it just works also with old versions...
        target_framework_version = root.find(".//TargetFrameworkVersion")
        # if the tag exists, update it
        if target_framework_version is not None:
            target_framework_version.text = "v4.8"
        # if it does not exist, create it
        else:
            property_group = ET.SubElement(root, "PropertyGroup")
            target_framework_version = ET.SubElement(
                property_group, "TargetFrameworkVersion"
            )
            target_framework_version.text = "v4.8"

    @staticmethod
    def add_default_output_path(root: ET.Element):
        # go to PropertyGroup and add OutputPath if it does not exist
        property_group = root.find(".//PropertyGroup")
        output_path = property_group.find(".//OutputPath")
        if output_path is None:
            output_path = ET.SubElement(property_group, "OutputPath")
            output_path.text = "bin\\Debug"
        else:
            output_path.text = "bin\\Debug"

    @staticmethod
    def remove_ico_references(csproj_file: str):
        """
         <PropertyGroup>
            <ApplicationIcon>splash_qWu_icon.ico</ApplicationIcon>
        </PropertyGroup>
          <ItemGroup>
            <Content Include="splash_qWu_icon.ico" />
        </ItemGroup>
        """
        # remove all lines with ...ico"
        lines = csproj_file.split("\n")
        new_lines = []
        for line in lines:
            if ".ico" not in line:
                new_lines.append(line)
            else:
                logging.warning(
                    f"Removed .ico reference from csproj file: {line.strip()}"
                )
        return "\n".join(new_lines)
